"""
Facebook Lead Ads webhook endpoint.
Handles webhook verification and leadgen event processing.
"""
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.facebook_client import FacebookClient, FacebookAuthError, FacebookGraphAPIError
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.dealership import Dealership

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhooks/facebook", response_class=PlainTextResponse)
async def verify_facebook_webhook(request: Request):
    """
    Facebook webhook verification endpoint (GET request).

    Meta sends a GET request with hub.mode, hub.verify_token, and hub.challenge.
    We must verify the token matches ours and return the challenge.

    Query Parameters:
        hub.mode: Should be "subscribe"
        hub.verify_token: Token we configured in Meta App
        hub.challenge: Challenge string to return

    Returns:
        PlainTextResponse with the challenge string
    """
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(f"Facebook webhook verification request: mode={mode}")

    # Verify token matches
    if mode == "subscribe" and token == settings.FACEBOOK_VERIFY_TOKEN:
        logger.info("✅ Facebook webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        logger.warning(f"❌ Facebook webhook verification failed: invalid token or mode")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/facebook")
async def receive_facebook_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Facebook leadgen webhook receiver (POST request).

    Receives leadgen events from Facebook when a customer submits a Lead Ad form.
    Validates signature, extracts lead_id, and processes lead in background.

    Security:
        - Verifies X-Hub-Signature-256 header using App Secret
        - Rejects requests with invalid signatures

    Returns:
        200 OK immediately to prevent timeout
    """
    # Read raw body for signature verification
    body_bytes = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256", "")

    # Verify signature
    if not verify_signature(body_bytes, signature_header):
        logger.warning("❌ Facebook webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON body
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Error parsing webhook JSON: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info(f"✅ Facebook webhook received: {data.get('object')}")

    # Process webhook payload
    object_type = data.get("object")

    if object_type == "page":
        entries = data.get("entry", [])

        for entry in entries:
            changes = entry.get("changes", [])

            for change in changes:
                field = change.get("field")
                value = change.get("value", {})

                if field == "leadgen":
                    leadgen_id = value.get("leadgen_id")
                    page_id = value.get("page_id")
                    form_id = value.get("form_id")

                    logger.info(f"📋 Leadgen event: lead_id={leadgen_id}, page_id={page_id}, form_id={form_id}")

                    # Queue background task to process lead
                    background_tasks.add_task(
                        process_facebook_lead,
                        leadgen_id=leadgen_id,
                        page_id=page_id,
                        form_id=form_id
                    )

    # Return 200 immediately
    return {"status": "received"}


def verify_signature(payload: bytes, signature_header: str) -> bool:
    """
    Verify Facebook webhook signature using HMAC SHA256.

    Args:
        payload: Raw request body (bytes)
        signature_header: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid, False otherwise
    """
    if not settings.FACEBOOK_APP_SECRET:
        logger.error("FACEBOOK_APP_SECRET not configured, rejecting webhook")
        return False

    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header")
        return False

    # Remove 'sha256=' prefix
    try:
        received_signature = signature_header.split("=")[1]
    except IndexError:
        logger.warning("Malformed X-Hub-Signature-256 header")
        return False

    # Calculate expected signature
    expected_signature = hmac.new(
        key=settings.FACEBOOK_APP_SECRET.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected_signature, received_signature)


async def process_facebook_lead(
    leadgen_id: str,
    page_id: str,
    form_id: str
):
    """
    Background task to process Facebook lead.

    Steps:
    1. Check for duplicate lead (by facebook_lead_id)
    2. Call Graph API to retrieve full lead data
    3. Map fields to Lead model
    4. Create lead in database
    5. Create initial conversation record
    6. Trigger AI response (future: integrate with AI service)

    Args:
        leadgen_id: Facebook lead ID
        page_id: Facebook page ID
        form_id: Facebook form ID
    """
    logger.info(f"🔄 Processing Facebook lead: {leadgen_id}")

    # Create new database session for background task
    db = SessionLocal()
    
    try:
        # Check for duplicate lead
        existing_lead = db.query(Lead).filter(
            Lead.source_metadata["facebook_lead_id"].astext == leadgen_id
        ).first()

        if existing_lead:
            logger.info(f"⚠️ Duplicate lead detected: {leadgen_id}, skipping")
            return

        # Initialize Facebook client
        # TODO: In production, get Page Access Token for specific page_id from dealerships table
        fb_client = FacebookClient()

        # Retrieve lead data from Graph API
        try:
            lead_data = await fb_client.get_lead(leadgen_id)
        except FacebookAuthError as e:
            logger.error(f"❌ Facebook auth error: {str(e)}")
            # TODO: Alert dealership that token needs renewal
            return
        except FacebookGraphAPIError as e:
            logger.error(f"❌ Facebook API error: {str(e)}")
            # TODO: Implement retry logic
            return

        # Skip test leads
        if lead_data.is_test:
            logger.info(f"🧪 Test lead detected: {leadgen_id}, skipping AI response")
            # Still create lead for testing purposes, but mark it

        # TODO: Determine dealership_id from page_id
        # For now, we'll need to add logic to map page_id to dealership_id
        # This requires storing page_id -> dealership_id mapping in database

        # For MVP/testing: Use a default dealership (first one in database)
        dealership = db.query(Dealership).first()
        if not dealership:
            logger.error("No dealerships configured in database. Please create at least one dealership before processing Facebook leads.")
            return

        dealership_id = str(dealership.id)

        # Convert to Lead model dictionary
        lead_dict = lead_data.to_lead_dict(dealership_id)

        # Create lead in database
        new_lead = Lead(**lead_dict)
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)

        logger.info(f"✅ Created lead from Facebook: {new_lead.id} (customer: {new_lead.customer_name})")

        # Create initial conversation record
        if lead_data.initial_message:
            conversation = Conversation(
                lead_id=new_lead.id,
                dealership_id=UUID(dealership_id),
                channel="facebook",
                direction="inbound",
                sender=lead_data.customer_name or "Customer",
                sender_type="customer",
                message_content=lead_data.initial_message
            )
            db.add(conversation)
            db.commit()

            logger.info(f"✅ Created conversation record for lead {new_lead.id}")

        # Trigger AI response workflow
        # - Generate AI response using Claude API
        # - Send email to customer
        # - Update lead status to 'contacted'
        if not lead_data.is_test:
            logger.info(f"📧 Triggering AI response for lead {new_lead.id}")
            from ....services.lead_processor import lead_processor
            import asyncio
            asyncio.run(lead_processor.process_new_lead(
                lead_id=new_lead.id,
                db=db,
                skip_ai_response=False
            ))

    except Exception as e:
        logger.error(f"❌ Error processing Facebook lead {leadgen_id}: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
