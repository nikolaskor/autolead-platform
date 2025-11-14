"""
Public webhook endpoints for lead capture.

These endpoints are PUBLIC (no authentication required) and are called by:
- Website forms embedded on dealership sites
- External services
- Third-party integrations
"""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from typing import Optional

from ....core.database import get_db
from ....core.rls import set_dealership_context
from ....models.lead import Lead
from ....models.dealership import Dealership
from ....services.lead_processor import lead_processor

logger = logging.getLogger(__name__)

router = APIRouter()


class FormSubmission(BaseModel):
    """Schema for website form submissions."""
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    email: EmailStr = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, max_length=50, description="Customer phone number")
    vehicle_interest: Optional[str] = Field(None, max_length=255, description="Vehicle of interest")
    message: str = Field(..., min_length=1, description="Customer message")
    source_url: Optional[str] = Field(None, description="URL of the page where form was submitted")


@router.post("/form/{dealership_id}", status_code=200)
async def receive_form_submission(
    dealership_id: UUID,
    submission: FormSubmission,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Public webhook endpoint for website form submissions.

    This endpoint is called by the embedded forms on dealership websites.
    No authentication required (public endpoint).

    Args:
        dealership_id: UUID of the dealership receiving the lead
        submission: Form data (name, email, phone, message, etc.)

    Returns:
        Success response with lead_id

    Workflow:
        1. Validate dealership exists
        2. Create lead record immediately (response <100ms)
        3. Queue AI response + email workflow (background)
        4. Return success to form

    Example:
        POST /webhooks/form/123e4567-e89b-12d3-a456-426614174000
        {
            "name": "Ola Nordmann",
            "email": "ola@example.com",
            "phone": "+4712345678",
            "vehicle_interest": "Tesla Model 3",
            "message": "Interested in test drive",
            "source_url": "https://dealership.no/contact"
        }
    """
    try:
        # Verify dealership exists
        dealership = db.query(Dealership).filter(Dealership.id == dealership_id).first()
        if not dealership:
            raise HTTPException(
                status_code=404,
                detail=f"Dealership not found: {dealership_id}"
            )

        # Set RLS context
        set_dealership_context(db, dealership_id)

        # Check for duplicate lead (same email within last 24 hours)
        from datetime import datetime, timedelta, timezone
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        existing_lead = db.query(Lead).filter(
            Lead.dealership_id == dealership_id,
            Lead.customer_email == submission.email,
            Lead.created_at >= twenty_four_hours_ago
        ).first()

        if existing_lead:
            logger.info(
                f"Duplicate lead detected for {submission.email} at dealership {dealership_id}",
                extra={"lead_id": str(existing_lead.id)}
            )
            # Update existing lead instead of creating new
            existing_lead.initial_message = f"{existing_lead.initial_message}\n\n---\nNy henvendelse:\n{submission.message}"
            existing_lead.source_url = submission.source_url or existing_lead.source_url
            db.commit()
            db.refresh(existing_lead)

            return {
                "lead_id": str(existing_lead.id),
                "status": "updated",
                "message": "Lead updated with new inquiry"
            }

        # Create new lead
        lead = Lead(
            dealership_id=dealership_id,
            source="website",
            source_url=submission.source_url,
            source_metadata={
                "form_version": "1.0",
                "user_agent": None  # Could extract from request headers
            },
            status="new",
            customer_name=submission.name,
            customer_email=submission.email,
            customer_phone=submission.phone,
            vehicle_interest=submission.vehicle_interest,
            initial_message=submission.message,
            lead_score=60  # Default score for website leads
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        logger.info(
            f"Lead created from website form: {lead.id}",
            extra={
                "lead_id": str(lead.id),
                "customer": submission.name,
                "dealership": dealership.name
            }
        )

        # Queue AI response workflow in background
        background_tasks.add_task(
            lead_processor.process_new_lead,
            lead_id=lead.id,
            db=db,
            skip_ai_response=False
        )

        return {
            "lead_id": str(lead.id),
            "status": "created",
            "message": "Lead received successfully. You will receive a response shortly."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process form submission. Please try again."
        )
