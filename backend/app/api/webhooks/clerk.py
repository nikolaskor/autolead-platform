"""Clerk webhook endpoint for provisioning dealerships and users."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

from ...core.config import settings
from ...core.database import get_db
from ...core.auth import get_dealership_from_org, get_user_from_clerk_id
from ...models.dealership import Dealership
from ...models.user import User

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/clerk", status_code=status.HTTP_200_OK)
async def clerk_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Handle incoming Clerk webhook events.

    Validates the Svix signature and dispatches to event-specific handlers.
    """

    payload = await request.body()
    
    # Normalize headers for Svix - it expects lowercase header names
    headers = {key.lower(): value for key, value in request.headers.items()}

    logger.info("Webhook request received from %s", request.client.host if request.client else "unknown")
    
    try:
        event = _verify_svix_signature(payload, headers)
    except WebhookVerificationError as exc:
        logger.warning("Clerk webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature") from exc
    except Exception as exc:
        logger.exception("Unexpected error during signature verification")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signature verification error") from exc

    event_type: str | None = event.get("type")
    data: Dict[str, Any] = event.get("data", {})

    handlers = {
        "organization.created": _handle_organization_created,
        "organizationMembership.created": _handle_membership_created,
    }

    handler = handlers.get(event_type)
    if not handler:
        logger.debug("Unhandled Clerk webhook event: %s", event_type)
        return {"status": "ignored", "event_type": event_type}

    try:
        result = handler(data, db)
        db.commit()
        return {"status": "processed", "event_type": event_type, **result}
    except HTTPException:
        # Re-raise FastAPI exceptions so status codes propagate
        db.rollback()
        raise
    except Exception as exc:  # noqa: BLE001 - we want to log unexpected errors
        db.rollback()
        logger.exception("Error handling Clerk webhook event %s", event_type)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook handling failed") from exc


def _verify_svix_signature(payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
    """Verify Svix signature and return parsed event payload.
    
    Svix's webhook.verify() returns a dict directly, not a JSON string.
    This function handles the verification and ensures we return a dict.
    
    Args:
        payload: Raw request body bytes
        headers: Request headers (should be lowercase normalized)
        
    Returns:
        Parsed event payload as a dict
        
    Raises:
        WebhookVerificationError: If signature verification fails
    """
    secret = settings.CLERK_WEBHOOK_SECRET
    webhook = Webhook(secret)
    
    # Svix.verify() returns a dict directly when successful
    parsed_event = webhook.verify(payload, headers)
    
    # Handle different return types from Svix (defensive programming)
    if isinstance(parsed_event, dict):
        return parsed_event
    elif isinstance(parsed_event, (bytes, bytearray)):
        # Edge case: if it returns bytes, decode and parse
        decoded = parsed_event.decode("utf-8")
        return json.loads(decoded)
    elif isinstance(parsed_event, str):
        # Edge case: if it returns a string, parse it
        return json.loads(parsed_event)
    else:
        # Unexpected type - log and raise
        logger.error(f"Unexpected return type from Svix.verify(): {type(parsed_event)}")
        raise ValueError(f"Unexpected return type from webhook verification: {type(parsed_event)}")


def _handle_organization_created(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Ensure a dealership exists for the Clerk organization."""

    clerk_org_id = data.get("id")
    if not clerk_org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing organization ID")

    name = data.get("name") or "Unnamed Dealership"
    email = data.get("primary_contact_email_address") or data.get("slug") or "unknown@example.com"

    dealership, created = _ensure_dealership(db, clerk_org_id, name=name, email=email)

    return {
        "dealership_id": str(dealership.id),
        "created_dealership": created,
    }


def _handle_membership_created(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Ensure dealership and user exist for a membership event."""

    organization = data.get("organization") or {}
    clerk_org_id = organization.get("id")
    if not clerk_org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing organization ID")

    public_user = data.get("public_user_data") or {}
    clerk_user_id = public_user.get("user_id")
    if not clerk_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user ID")

    role = data.get("role") or "member"
    email = public_user.get("identifier")
    first_name = public_user.get("first_name")
    last_name = public_user.get("last_name")
    full_name = " ".join(filter(None, [first_name, last_name])).strip() or None

    dealership, created_dealership = _ensure_dealership(
        db,
        clerk_org_id,
        name=organization.get("name"),
        email=email,
    )

    user = get_user_from_clerk_id(clerk_user_id, db)
    created_user = False

    if not user:
        assigned_role = _determine_role(role, created_dealership, dealership, db)
        user = User(
            id=uuid.uuid4(),
            dealership_id=dealership.id,
            clerk_user_id=clerk_user_id,
            email=email or "unknown@example.com",
            name=full_name,
            role=assigned_role,
        )
        db.add(user)
        created_user = True
    else:
        # Ensure user is linked to latest dealership
        if user.dealership_id != dealership.id:
            user.dealership_id = dealership.id
        # Update role if Clerk promotes/demotes
        desired_role = _determine_role(role, created_dealership, dealership, db)
        if user.role != desired_role:
            user.role = desired_role
        # Update email/name if provided
        if email and user.email != email:
            user.email = email
        if full_name and user.name != full_name:
            user.name = full_name

    return {
        "dealership_id": str(dealership.id),
        "user_id": str(user.id),
        "created_dealership": created_dealership,
        "created_user": created_user,
    }


def _ensure_dealership(
    db: Session,
    clerk_org_id: str,
    *,
    name: str | None,
    email: str | None,
) -> Tuple[Dealership, bool]:
    """Fetch or create a dealership for the Clerk organization."""

    dealership = get_dealership_from_org(clerk_org_id, db)
    created = False

    if dealership is None:
        dealership = Dealership(
            id=uuid.uuid4(),
            clerk_org_id=clerk_org_id,
            name=name or "Unnamed Dealership",
            email=email or "unknown@example.com",
            subscription_status="active",
            subscription_tier="starter",
        )
        db.add(dealership)
        db.flush()  # Ensure dealership.id available
        created = True
    else:
        # Update metadata if changed
        updated = False
        if name and dealership.name != name:
            dealership.name = name
            updated = True
        if email and dealership.email != email:
            dealership.email = email
            updated = True
        if updated:
            logger.debug("Updated dealership metadata for Clerk org %s", clerk_org_id)

    return dealership, created


def _determine_role(
    clerk_role: str,
    created_dealership: bool,
    dealership: Dealership,
    db: Session,
) -> str:
    """Determine the application role for a Clerk membership."""

    if created_dealership:
        # First user becomes admin
        return "admin"

    normalized = (clerk_role or "").lower()
    if normalized in {"admin", "owner"}:
        return "admin"

    # Fall back to existing role if dealership already has this user set as admin
    if normalized == "manager":
        return "manager"

    # For first member (dealership already existed but no users) promote to admin
    user_count = (
        db.query(User)
        .filter(User.dealership_id == dealership.id)
        .count()
    )
    if user_count == 0:
        return "admin"

    return "sales_rep"

