"""
Dealership settings API endpoints.

Handles:
- Email integration configuration
- Forwarding address generation
- Integration settings management
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from ....core.database import get_db
from ....api.deps import get_current_user
from ....models.user import User
from ....models.dealership import Dealership


router = APIRouter()


class EmailIntegrationSettings(BaseModel):
    """Schema for email integration settings."""
    email_integration_enabled: bool
    email_forwarding_address: Optional[str] = None
    email_integration_settings: Optional[Dict[str, Any]] = None


class EmailIntegrationUpdate(BaseModel):
    """Schema for updating email integration settings."""
    email_integration_enabled: bool


class EmailIntegrationResponse(BaseModel):
    """Response schema for email integration setup."""
    email_integration_enabled: bool
    email_forwarding_address: Optional[str]
    instructions: str


@router.get("/email-integration", response_model=EmailIntegrationResponse)
def get_email_integration_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get current email integration settings for the dealership.

    Returns:
    - email_integration_enabled: Whether email integration is active
    - email_forwarding_address: The unique forwarding address for this dealership
    - instructions: Setup instructions for the dealership
    """
    dealership = db.query(Dealership).filter(Dealership.id == user.dealership_id).first()

    if not dealership:
        raise HTTPException(status_code=404, detail="Dealership not found")

    instructions = ""
    if dealership.email_integration_enabled:
        instructions = f"""
Email integration is enabled for your dealership.

**Setup Instructions:**

1. Forward all sales emails to: {dealership.email_forwarding_address}

2. How to set up email forwarding:
   - **Gmail**: Settings → Forwarding and POP/IMAP → Add forwarding address
   - **Outlook**: Settings → Mail → Forwarding → Enable forwarding
   - **Other email providers**: Check your email provider's documentation

3. Once forwarding is set up, all incoming sales emails will be automatically:
   - Classified as sales inquiries, spam, or other
   - Converted to leads if they're genuine sales inquiries
   - Available in your dashboard for review

**Note:** Make sure to keep your original email address active - we'll forward emails, not replace your inbox.
""".strip()
    else:
        instructions = """
Email integration is currently disabled.

To enable email integration, click the "Enable Email Integration" button. You'll receive a unique forwarding address that you can use to monitor your sales inbox.
""".strip()

    return EmailIntegrationResponse(
        email_integration_enabled=dealership.email_integration_enabled,
        email_forwarding_address=dealership.email_forwarding_address,
        instructions=instructions
    )


@router.post("/email-integration/enable", response_model=EmailIntegrationResponse)
def enable_email_integration(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Enable email integration for the dealership.

    Generates a unique forwarding address if not already created.
    Format: {dealership_slug}-{random_id}@leads.autolead.no
    """
    dealership = db.query(Dealership).filter(Dealership.id == user.dealership_id).first()

    if not dealership:
        raise HTTPException(status_code=404, detail="Dealership not found")

    # Generate forwarding address if not exists
    if not dealership.email_forwarding_address:
        # Create slug from dealership name
        slug = dealership.name.lower().replace(" ", "-").replace(".", "")
        # Remove special characters
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        # Limit to 20 chars
        slug = slug[:20]

        # Generate random ID (8 characters)
        random_id = secrets.token_urlsafe(6)  # 6 bytes = 8 base64url chars

        # Create unique forwarding address
        forwarding_address = f"{slug}-{random_id}@leads.autolead.no"

        # Check for duplicates (extremely unlikely)
        while db.query(Dealership).filter(
            Dealership.email_forwarding_address == forwarding_address
        ).first():
            random_id = secrets.token_urlsafe(6)
            forwarding_address = f"{slug}-{random_id}@leads.autolead.no"

        dealership.email_forwarding_address = forwarding_address

    # Enable integration
    dealership.email_integration_enabled = True
    db.commit()

    instructions = f"""
Email integration is now enabled!

**Your unique forwarding address:**
{dealership.email_forwarding_address}

**Setup Instructions:**

1. Forward all sales emails to: {dealership.email_forwarding_address}

2. How to set up email forwarding:
   - **Gmail**: Settings → Forwarding and POP/IMAP → Add forwarding address
   - **Outlook**: Settings → Mail → Forwarding → Enable forwarding
   - **Other email providers**: Check your email provider's documentation

3. Once forwarding is set up, all incoming sales emails will be automatically:
   - Classified as sales inquiries, spam, or other
   - Converted to leads if they're genuine sales inquiries
   - Available in your dashboard for review

**Note:** Make sure to keep your original email address active - we'll forward emails, not replace your inbox.
""".strip()

    return EmailIntegrationResponse(
        email_integration_enabled=True,
        email_forwarding_address=dealership.email_forwarding_address,
        instructions=instructions
    )


@router.post("/email-integration/disable", response_model=EmailIntegrationResponse)
def disable_email_integration(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disable email integration for the dealership.

    Note: This does not delete the forwarding address - it can be re-enabled later.
    """
    dealership = db.query(Dealership).filter(Dealership.id == user.dealership_id).first()

    if not dealership:
        raise HTTPException(status_code=404, detail="Dealership not found")

    dealership.email_integration_enabled = False
    db.commit()

    return EmailIntegrationResponse(
        email_integration_enabled=False,
        email_forwarding_address=dealership.email_forwarding_address,
        instructions="Email integration has been disabled. You can re-enable it at any time."
    )
