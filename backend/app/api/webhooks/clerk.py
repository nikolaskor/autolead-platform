"""Clerk webhook endpoint for provisioning dealerships and users."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

from ...core.config import settings
from ...core.database import get_db
from ...core.auth import get_dealership_from_org, get_user_from_clerk_id
from ...models.dealership import Dealership
from ...models.user import User

logger = logging.getLogger(__name__)

# Email validation regex (matches database constraint)
EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _validate_and_normalize_email(email: str | None, clerk_org_id: str | None = None) -> str:
    """Validate email format and generate valid placeholder if needed.
    
    Args:
        email: Email address to validate
        clerk_org_id: Optional Clerk organization ID for generating placeholder
        
    Returns:
        Valid email address (either original or generated placeholder)
    """
    if email and EMAIL_REGEX.match(email):
        return email
    
    # Generate valid placeholder email if invalid or missing
    if clerk_org_id:
        # Use org ID to create unique placeholder
        org_slug = clerk_org_id.replace("org_", "").lower()[:20]  # Limit length
        return f"org-{org_slug}@placeholder.norvalt.no"
    
    return "unknown@placeholder.norvalt.no"


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
        "user.deleted": _handle_user_deleted,
        "organizationMembership.deleted": _handle_membership_deleted,
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
    except IntegrityError as exc:
        # Handle database constraint violations
        db.rollback()
        error_detail = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        
        # Extract constraint violation details
        if "CheckViolation" in error_detail or "valid_dealership_email" in error_detail:
            logger.error(
                "Email validation failed for webhook event %s: %s",
                event_type,
                error_detail
            )
            detail_msg = "Invalid email format provided. Email must match standard format (e.g., user@example.com)."
            if settings.DEBUG:
                detail_msg += f" Details: {error_detail}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_msg
            ) from exc
        elif "UniqueViolation" in error_detail or "dealerships_email_key" in error_detail:
            logger.error(
                "Duplicate email violation for webhook event %s: %s",
                event_type,
                error_detail
            )
            detail_msg = "A dealership with this email already exists. The webhook may be retrying or the email is already in use."
            if settings.DEBUG:
                detail_msg += f" Details: {error_detail}"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail_msg
            ) from exc
        else:
            # Other integrity violations
            logger.exception("Database integrity error handling webhook event %s", event_type)
            detail_msg = f"Database constraint violation: {error_detail}"
            if not settings.DEBUG:
                detail_msg = "Database constraint violation occurred"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_msg
            ) from exc
    except Exception as exc:  # noqa: BLE001 - we want to log unexpected errors
        db.rollback()
        logger.exception("Error handling Clerk webhook event %s", event_type)
        detail_msg = "Webhook handling failed"
        if settings.DEBUG:
            detail_msg += f": {str(exc)}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail_msg) from exc


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
    raw_email = data.get("primary_contact_email_address") or data.get("slug")
    email = _validate_and_normalize_email(raw_email, clerk_org_id)

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
    
    # Try to get user email from multiple sources
    raw_email = public_user.get("identifier")
    # Also check email_addresses array if identifier is not available
    if not raw_email or not EMAIL_REGEX.match(raw_email):
        email_addresses = public_user.get("email_addresses", [])
        if email_addresses and len(email_addresses) > 0:
            # Get the first verified email, or first email if none verified
            verified_email = next((e.get("email_address") for e in email_addresses if e.get("verification", {}).get("status") == "verified"), None)
            if verified_email:
                raw_email = verified_email
            elif email_addresses[0].get("email_address"):
                raw_email = email_addresses[0].get("email_address")
    
    first_name = public_user.get("first_name")
    last_name = public_user.get("last_name")
    full_name = " ".join(filter(None, [first_name, last_name])).strip() or None

    # Determine dealership email:
    # 1. Use valid user email if available
    # 2. Otherwise generate placeholder
    # 3. If dealership exists with placeholder, we'll update it below if we have valid email
    user_email_valid = raw_email and EMAIL_REGEX.match(raw_email)
    dealership_email = raw_email if user_email_valid else _validate_and_normalize_email(raw_email, clerk_org_id)
    
    dealership, created_dealership = _ensure_dealership(
        db,
        clerk_org_id,
        name=organization.get("name"),
        email=dealership_email,
    )
    
    # If dealership has placeholder email but we now have valid user email, update it
    if user_email_valid and dealership.email.startswith("org-") and "@placeholder.norvalt.no" in dealership.email:
        logger.info(
            "Updating dealership %s email from placeholder %s to user email %s",
            dealership.id,
            dealership.email,
            raw_email
        )
        dealership.email = raw_email

    user = get_user_from_clerk_id(clerk_user_id, db)
    created_user = False

    if not user:
        assigned_role = _determine_role(role, created_dealership, dealership, db)
        # Use validated email for user, or fallback to placeholder
        user_email = raw_email if raw_email and EMAIL_REGEX.match(raw_email) else f"user-{clerk_user_id[:20]}@placeholder.norvalt.no"
        user = User(
            id=uuid.uuid4(),
            dealership_id=dealership.id,
            clerk_user_id=clerk_user_id,
            email=user_email,
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
        # Update email/name if provided and valid
        if raw_email and EMAIL_REGEX.match(raw_email) and user.email != raw_email:
            user.email = raw_email
        if full_name and user.name != full_name:
            user.name = full_name

    return {
        "dealership_id": str(dealership.id),
        "user_id": str(user.id),
        "created_dealership": created_dealership,
        "created_user": created_user,
    }


def _handle_user_deleted(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Delete user from database when user account is deleted in Clerk.
    
    This handler is called when a user account is completely deleted from Clerk.
    The user and all their associations will be removed from the database.
    Leads assigned to this user will have their assigned_to set to NULL (via FK constraint).
    """
    clerk_user_id = data.get("id")
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing user ID in user.deleted event"
        )
    
    user = get_user_from_clerk_id(clerk_user_id, db)
    if not user:
        logger.debug("User with Clerk ID %s not found in database, skipping deletion", clerk_user_id)
        return {
            "deleted_user_id": None,
            "clerk_user_id": clerk_user_id,
            "message": "User not found in database"
        }
    
    user_id = str(user.id)
    user_email = user.email
    db.delete(user)
    logger.info(
        "Deleted user %s (email: %s, Clerk ID: %s) from database",
        user_id,
        user_email,
        clerk_user_id
    )
    
    return {
        "deleted_user_id": user_id,
        "clerk_user_id": clerk_user_id,
        "user_email": user_email,
    }


def _handle_membership_deleted(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Delete user from database when removed from organization.
    
    In this application, users belong to a single dealership (organization).
    When a user is removed from an organization, they should be deleted from
    the database since they can no longer access the platform.
    
    Leads assigned to this user will have their assigned_to set to NULL (via FK constraint).
    """
    organization = data.get("organization") or {}
    clerk_org_id = organization.get("id")
    if not clerk_org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing organization ID in organizationMembership.deleted event"
        )
    
    public_user = data.get("public_user_data") or {}
    clerk_user_id = public_user.get("user_id")
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing user ID in organizationMembership.deleted event"
        )
    
    # Verify the user belongs to this organization's dealership
    dealership = get_dealership_from_org(clerk_org_id, db)
    if not dealership:
        logger.warning(
            "Dealership not found for Clerk org %s, cannot verify membership deletion",
            clerk_org_id
        )
        return {
            "deleted_user_id": None,
            "clerk_user_id": clerk_user_id,
            "clerk_org_id": clerk_org_id,
            "message": "Dealership not found"
        }
    
    user = get_user_from_clerk_id(clerk_user_id, db)
    if not user:
        logger.debug(
            "User with Clerk ID %s not found in database, skipping deletion",
            clerk_user_id
        )
        return {
            "deleted_user_id": None,
            "clerk_user_id": clerk_user_id,
            "clerk_org_id": clerk_org_id,
            "message": "User not found in database"
        }
    
    # Verify user belongs to this dealership
    if user.dealership_id != dealership.id:
        logger.warning(
            "User %s does not belong to dealership %s, skipping deletion",
            clerk_user_id,
            clerk_org_id
        )
        return {
            "deleted_user_id": None,
            "clerk_user_id": clerk_user_id,
            "clerk_org_id": clerk_org_id,
            "message": "User does not belong to this dealership"
        }
    
    user_id = str(user.id)
    user_email = user.email
    db.delete(user)
    logger.info(
        "Deleted user %s (email: %s, Clerk ID: %s) from dealership %s",
        user_id,
        user_email,
        clerk_user_id,
        clerk_org_id
    )
    
    return {
        "deleted_user_id": user_id,
        "clerk_user_id": clerk_user_id,
        "clerk_org_id": clerk_org_id,
        "user_email": user_email,
    }


def _ensure_dealership(
    db: Session,
    clerk_org_id: str,
    *,
    name: str | None,
    email: str | None,
) -> Tuple[Dealership, bool]:
    """Fetch or create a dealership for the Clerk organization.
    
    Checks for existing dealership by clerk_org_id first, then by email.
    If found by email but different org_id, updates the org_id to prevent duplicates.
    """
    
    # First, try to find by clerk_org_id (primary lookup)
    dealership = get_dealership_from_org(clerk_org_id, db)
    created = False

    if dealership is None and email:
        # If not found by org_id, check if dealership exists with this email
        existing_by_email = db.query(Dealership).filter(Dealership.email == email).first()
        if existing_by_email:
            # Dealership exists with this email but different org_id
            # Update the org_id to link them (handles org_id changes in Clerk)
            logger.info(
                "Found dealership %s by email %s, updating clerk_org_id from %s to %s",
                existing_by_email.id,
                email,
                existing_by_email.clerk_org_id,
                clerk_org_id
            )
            existing_by_email.clerk_org_id = clerk_org_id
            dealership = existing_by_email
            # Update name if provided and different
            if name and dealership.name != name:
                dealership.name = name
            return dealership, False

    if dealership is None:
        # Create new dealership
        dealership = Dealership(
            id=uuid.uuid4(),
            clerk_org_id=clerk_org_id,
            name=name or "Unnamed Dealership",
            email=email or "unknown@placeholder.norvalt.no",
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
            # Only update email if it's valid and different
            if EMAIL_REGEX.match(email):
                dealership.email = email
                updated = True
            else:
                logger.warning(
                    "Skipping email update for dealership %s: invalid format %s",
                    dealership.id,
                    email
                )
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

