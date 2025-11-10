"""Tests for Clerk webhook provisioning."""

import json
from unittest.mock import patch

import pytest
from svix.webhooks import WebhookVerificationError

from app.core.config import settings
from app.models.dealership import Dealership
from app.models.user import User


@pytest.fixture(autouse=True)
def configure_webhook_secret():
    """Ensure the webhook secret is set for tests."""
    original = settings.CLERK_WEBHOOK_SECRET
    settings.CLERK_WEBHOOK_SECRET = "test_secret"
    try:
        yield
    finally:
        settings.CLERK_WEBHOOK_SECRET = original


def _headers() -> dict[str, str]:
    return {
        "svix-id": "msg_p_123",
        "svix-signature": "v1,test",
        "svix-timestamp": "1700000000",
    }


def test_membership_created_provisions_user_and_dealership(client, db_session):
    """Webhook should create dealership and user, and be idempotent."""

    event = {
        "type": "organizationMembership.created",
        "data": {
            "role": "admin",
            "organization": {
                "id": "org_test_webhook",
                "name": "Webhook Motors",
            },
            "public_user_data": {
                "user_id": "user_test_webhook",
                "identifier": "webhook@example.com",
                "first_name": "Web",
                "last_name": " Hook",
            },
        },
    }

    with patch("app.api.webhooks.clerk.Webhook.verify", return_value=json.dumps(event)):
        response = client.post("/webhooks/clerk", data="{}", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["created_dealership"] is True
    assert body["created_user"] is True

    dealership = db_session.query(Dealership).filter_by(clerk_org_id="org_test_webhook").first()
    assert dealership is not None
    assert dealership.name == "Webhook Motors"

    user = db_session.query(User).filter_by(clerk_user_id="user_test_webhook").first()
    assert user is not None
    assert user.dealership_id == dealership.id
    assert user.role == "admin"

    # Second call should be idempotent
    with patch("app.api.webhooks.clerk.Webhook.verify", return_value=json.dumps(event)):
        response_repeat = client.post("/webhooks/clerk", data="{}", headers=_headers())

    assert response_repeat.status_code == 200
    body_repeat = response_repeat.json()
    assert body_repeat["created_dealership"] is False
    assert body_repeat["created_user"] is False


def test_invalid_signature_returns_400(client):
    """Invalid signature should return 400 without touching the database."""

    with patch(
        "app.api.webhooks.clerk.Webhook.verify",
        side_effect=WebhookVerificationError("invalid"),
    ):
        response = client.post("/webhooks/clerk", data="{}", headers=_headers())

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"


def test_user_deleted_removes_user_from_database(client, db_session):
    """Webhook should delete user when user.deleted event is received."""
    # First create a user
    from app.models.dealership import Dealership
    from app.models.user import User
    import uuid

    dealership = Dealership(
        id=uuid.uuid4(),
        clerk_org_id="org_test_delete",
        name="Test Dealership",
        email="test@example.com",
        subscription_status="active",
        subscription_tier="starter",
    )
    db_session.add(dealership)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        dealership_id=dealership.id,
        clerk_user_id="user_test_delete",
        email="delete@example.com",
        name="Test User",
        role="sales_rep",
    )
    db_session.add(user)
    db_session.commit()

    # Verify user exists
    assert db_session.query(User).filter_by(clerk_user_id="user_test_delete").first() is not None

    # Send deletion event
    event = {
        "type": "user.deleted",
        "data": {
            "id": "user_test_delete",
        },
    }

    with patch("app.api.webhooks.clerk.Webhook.verify", return_value=event):
        response = client.post("/webhooks/clerk", data="{}", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["event_type"] == "user.deleted"
    assert body["deleted_user_id"] is not None
    assert body["clerk_user_id"] == "user_test_delete"

    # Verify user is deleted
    assert db_session.query(User).filter_by(clerk_user_id="user_test_delete").first() is None


def test_user_deleted_idempotent(client, db_session):
    """Deleting a non-existent user should be idempotent (no error)."""
    event = {
        "type": "user.deleted",
        "data": {
            "id": "user_nonexistent",
        },
    }

    with patch("app.api.webhooks.clerk.Webhook.verify", return_value=event):
        response = client.post("/webhooks/clerk", data="{}", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["deleted_user_id"] is None
    assert body["message"] == "User not found in database"


def test_membership_deleted_removes_user_from_database(client, db_session):
    """Webhook should delete user when removed from organization."""
    # First create a user and dealership
    from app.models.dealership import Dealership
    from app.models.user import User
    import uuid

    dealership = Dealership(
        id=uuid.uuid4(),
        clerk_org_id="org_test_membership_delete",
        name="Test Dealership",
        email="test@example.com",
        subscription_status="active",
        subscription_tier="starter",
    )
    db_session.add(dealership)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        dealership_id=dealership.id,
        clerk_user_id="user_test_membership_delete",
        email="membership@example.com",
        name="Test User",
        role="sales_rep",
    )
    db_session.add(user)
    db_session.commit()

    # Verify user exists
    assert (
        db_session.query(User)
        .filter_by(clerk_user_id="user_test_membership_delete")
        .first()
        is not None
    )

    # Send membership deletion event
    event = {
        "type": "organizationMembership.deleted",
        "data": {
            "organization": {
                "id": "org_test_membership_delete",
            },
            "public_user_data": {
                "user_id": "user_test_membership_delete",
            },
        },
    }

    with patch("app.api.webhooks.clerk.Webhook.verify", return_value=event):
        response = client.post("/webhooks/clerk", data="{}", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["event_type"] == "organizationMembership.deleted"
    assert body["deleted_user_id"] is not None
    assert body["clerk_user_id"] == "user_test_membership_delete"

    # Verify user is deleted
    assert (
        db_session.query(User)
        .filter_by(clerk_user_id="user_test_membership_delete")
        .first()
        is None
    )


def test_membership_deleted_wrong_dealership_skips_deletion(client, db_session):
    """If user doesn't belong to the organization, deletion should be skipped."""
    from app.models.dealership import Dealership
    from app.models.user import User
    import uuid

    # Create dealership and user
    dealership1 = Dealership(
        id=uuid.uuid4(),
        clerk_org_id="org_test_1",
        name="Dealership 1",
        email="test1@example.com",
        subscription_status="active",
        subscription_tier="starter",
    )
    db_session.add(dealership1)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        dealership_id=dealership1.id,
        clerk_user_id="user_test_wrong_org",
        email="wrong@example.com",
        name="Test User",
        role="sales_rep",
    )
    db_session.add(user)
    db_session.commit()

    # Try to delete from a different organization
    event = {
        "type": "organizationMembership.deleted",
        "data": {
            "organization": {
                "id": "org_test_2",  # Different org
            },
            "public_user_data": {
                "user_id": "user_test_wrong_org",
            },
        },
    }

    with patch("app.api.webhooks.clerk.Webhook.verify", return_value=event):
        response = client.post("/webhooks/clerk", data="{}", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["deleted_user_id"] is None
    assert "does not belong" in body["message"] or "Dealership not found" in body["message"]

    # Verify user still exists
    assert (
        db_session.query(User)
        .filter_by(clerk_user_id="user_test_wrong_org")
        .first()
        is not None
    )

