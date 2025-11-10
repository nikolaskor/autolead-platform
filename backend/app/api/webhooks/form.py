"""Website form webhook endpoint for lead capture."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.dealership import Dealership
from ...models.lead import Lead
from ...schemas import FormWebhookRequest, FormWebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/form/{dealership_id}", status_code=status.HTTP_200_OK, response_model=FormWebhookResponse)
async def form_webhook(
    dealership_id: UUID = Path(..., description="Dealership UUID"),
    form_data: FormWebhookRequest = ...,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Handle website form submissions and create leads.

    This is a public endpoint that accepts form submissions from dealership websites.
    It validates the request, checks for duplicates, and creates or updates leads.

    **Duplicate Detection:**
    - If a lead with the same email exists within the last 5 minutes, updates it
    - If a lead with the same email exists within the last 7 days, creates new lead
    - After 7 days, always creates a new lead (new inquiry)

    **Edge Cases Handled:**
    - Invalid dealership_id: 404 Not Found
    - Duplicate submission within 5 min: Updates existing lead, returns 200
    - Missing optional fields: Stored as None
    - Invalid email format: Rejected by Pydantic validation (400)
    - Malformed JSON: Rejected by FastAPI (422)

    Args:
        dealership_id: UUID of the dealership
        form_data: Validated form submission data
        db: Database session

    Returns:
        FormWebhookResponse with lead_id and status

    Raises:
        HTTPException 404: Dealership not found
        HTTPException 400: Invalid request data
        HTTPException 500: Internal server error
    """

    logger.info(
        "Form webhook received for dealership %s from %s",
        dealership_id,
        form_data.email
    )

    # Verify dealership exists
    dealership = db.query(Dealership).filter(Dealership.id == dealership_id).first()
    if not dealership:
        logger.warning("Form webhook received for non-existent dealership: %s", dealership_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dealership not found: {dealership_id}"
        )

    try:
        # Check for duplicate within last 5 minutes (likely form resubmission)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_duplicate = db.query(Lead).filter(
            Lead.dealership_id == dealership_id,
            Lead.customer_email == form_data.email,
            Lead.created_at >= five_minutes_ago
        ).first()

        if recent_duplicate:
            # Update existing lead with latest data
            logger.info(
                "Duplicate form submission within 5 minutes for email %s, updating lead %s",
                form_data.email,
                recent_duplicate.id
            )
            recent_duplicate.customer_name = form_data.name
            recent_duplicate.customer_phone = form_data.phone
            recent_duplicate.vehicle_interest = form_data.vehicle_interest
            recent_duplicate.initial_message = form_data.message
            recent_duplicate.source_url = form_data.source_url

            db.commit()
            db.refresh(recent_duplicate)

            return FormWebhookResponse(
                lead_id=recent_duplicate.id,
                status="updated"
            )

        # Create new lead
        lead = Lead(
            dealership_id=dealership_id,
            customer_name=form_data.name,
            customer_email=form_data.email,
            customer_phone=form_data.phone,
            vehicle_interest=form_data.vehicle_interest,
            initial_message=form_data.message,
            source="website",
            source_url=form_data.source_url,
            status="new",
            lead_score=50,  # Default score
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        logger.info(
            "Created lead %s for dealership %s from website form (customer: %s)",
            lead.id,
            dealership_id,
            form_data.email
        )

        # TODO: Queue AI response job (Week 7)
        # await queue_ai_response_job(lead.id)

        return FormWebhookResponse(
            lead_id=lead.id,
            status="created"
        )

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Error processing form webhook for dealership %s",
            dealership_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process form submission"
        ) from exc
