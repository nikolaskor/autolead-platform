"""
Email API endpoints.

Handles:
- SendGrid Inbound Parse webhook
- Email listing and management
- Email processing triggers
"""
import json
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Form, BackgroundTasks
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.rls import set_dealership_context
from ....api.deps import get_current_user
from ....models.email import Email
from ....models.dealership import Dealership
from ....models.user import User
from ....schemas.email import EmailResponse, EmailListResponse
from ....services.email_processor import email_processor


router = APIRouter()


@router.post("/webhook/inbound", status_code=200)
async def receive_email_webhook(
    background_tasks: BackgroundTasks,
    to: str = Form(...),
    from_: str = Form(..., alias="from"),
    subject: str = Form(None),
    text: Optional[str] = Form(None),
    html: Optional[str] = Form(None),
    headers: Optional[str] = Form(None),
    envelope: Optional[str] = Form(None),
    charsets: Optional[str] = Form(None),
    SPF: Optional[str] = Form(None),
    attachments: Optional[int] = Form(0),
    db: Session = Depends(get_db)
):
    """
    SendGrid Inbound Parse webhook endpoint.

    Receives emails forwarded to dealership-specific addresses
    (e.g., bnh-abc123@leads.autolead.no) and processes them.

    SendGrid documentation: https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook
    """
    # Parse the "to" address to find the dealership
    # Format: dealership-{short_id}@leads.autolead.no
    # For now, we'll look up by email_forwarding_address
    dealership = db.query(Dealership).filter(
        Dealership.email_forwarding_address == to,
        Dealership.email_integration_enabled.is_(True)
    ).first()

    if not dealership:
        raise HTTPException(
            status_code=404,
            detail=f"No dealership found with forwarding address: {to}"
        )

    # Parse headers JSON
    headers_dict = {}
    if headers:
        try:
            headers_dict = json.loads(headers)
        except json.JSONDecodeError:
            headers_dict = {"raw": headers}

    # Extract Message-ID from headers (required for deduplication)
    message_id = headers_dict.get("Message-Id") or headers_dict.get("Message-ID")
    if not message_id:
        # Fallback: generate from from+to+subject+timestamp
        import hashlib
        import datetime
        unique_str = f"{from_}{to}{subject}{datetime.datetime.now(datetime.UTC).isoformat()}"
        message_id = f"<{hashlib.md5(unique_str.encode()).hexdigest()}@autolead.no>"

    # Check if email already exists (deduplication)
    existing_email = db.query(Email).filter(Email.message_id == message_id).first()
    if existing_email:
        return {"status": "ok", "message": "Email already processed", "email_id": str(existing_email.id)}

    # Parse sender name and email
    # Format: "Name <email@domain.com>" or just "email@domain.com"
    from_name = None
    from_email = from_
    if "<" in from_ and ">" in from_:
        # Extract name and email
        parts = from_.split("<")
        from_name = parts[0].strip().strip('"')
        from_email = parts[1].strip(">").strip()

    # Create email record
    email = Email(
        dealership_id=dealership.id,
        message_id=message_id,
        from_email=from_email,
        from_name=from_name if from_name else None,
        to_email=to,
        subject=subject,
        body_text=text,
        body_html=html,
        raw_headers=headers_dict,
        attachments=None,  # TODO: Handle file uploads
        processing_status="pending",
    )

    db.add(email)
    db.commit()
    db.refresh(email)

    # Process email in background
    background_tasks.add_task(process_email_background, email.id)

    return {
        "status": "ok",
        "message": "Email received and queued for processing",
        "email_id": str(email.id)
    }


def process_email_background(email_id: UUID):
    """
    Background task to process an email.

    This is called after the webhook returns 200 OK to SendGrid.
    """
    from ....core.database import SessionLocal
    from ....services.lead_processor import lead_processor
    import asyncio

    db = SessionLocal()
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if email:
            email_processor.process_email(db, email)

            # If a lead was created from this email, trigger AI response
            if email.lead_id:
                asyncio.run(lead_processor.process_new_lead(
                    lead_id=email.lead_id,
                    db=db,
                    skip_ai_response=False
                ))
    finally:
        db.close()


@router.get("/", response_model=EmailListResponse)
def list_emails(
    skip: int = 0,
    limit: int = 50,
    classification: Optional[str] = None,
    processing_status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    List emails for the current dealership.

    Optional filters:
    - classification: Filter by classification (sales_inquiry, spam, other, uncertain)
    - processing_status: Filter by processing status (pending, processing, completed, failed)
    """
    set_dealership_context(db, user.dealership_id)

    query = db.query(Email).filter(Email.dealership_id == user.dealership_id)

    if classification:
        query = query.filter(Email.classification == classification)

    if processing_status:
        query = query.filter(Email.processing_status == processing_status)

    total = query.count()
    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(limit).all()

    return EmailListResponse(
        emails=emails,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/{email_id}", response_model=EmailResponse)
def get_email(
    email_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get a specific email by ID."""
    set_dealership_context(db, user.dealership_id)

    email = db.query(Email).filter(
        Email.id == email_id,
        Email.dealership_id == user.dealership_id
    ).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return email


@router.post("/{email_id}/reprocess", response_model=EmailResponse)
def reprocess_email(
    email_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Reprocess an email (e.g., if classification was uncertain or failed).

    Useful for:
    - Retrying failed emails
    - Reclassifying uncertain emails
    - Re-extracting lead data
    """
    set_dealership_context(db, user.dealership_id)

    email = db.query(Email).filter(
        Email.id == email_id,
        Email.dealership_id == user.dealership_id
    ).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Reset processing status
    email.processing_status = "pending"
    email.retry_count += 1
    email.error_message = None
    db.commit()

    # Process email
    email_processor.process_email(db, email)

    db.refresh(email)
    return email
