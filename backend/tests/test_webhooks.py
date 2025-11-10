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

