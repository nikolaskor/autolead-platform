"""
Lead Processor Service - Orchestrates AI response workflow.

Workflow:
1. Receive new lead
2. Generate AI response with Claude
3. Send email to customer
4. Create conversation record
5. Update lead status
6. Log performance metrics

Target: Complete within 90 seconds
"""
import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional

from .ai_service import ai_service
from .email_service import email_service
from ..models.lead import Lead
from ..models.conversation import Conversation
from ..models.dealership import Dealership

logger = logging.getLogger(__name__)


class LeadProcessor:
    """Processes new leads and generates automated responses."""

    async def process_new_lead(
        self,
        lead_id: UUID,
        db: Session,
        skip_ai_response: bool = False
    ) -> dict:
        """
        Process a new lead with AI auto-response.

        Args:
            lead_id: ID of the lead to process
            db: Database session
            skip_ai_response: If True, skip AI response (for manual leads)

        Returns:
            dict with processing results
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Fetch lead with dealership
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")

            dealership = db.query(Dealership).filter(
                Dealership.id == lead.dealership_id
            ).first()
            if not dealership:
                raise ValueError(f"Dealership {lead.dealership_id} not found")

            logger.info(
                f"Processing lead {lead_id}",
                extra={
                    "lead_id": str(lead_id),
                    "customer": lead.customer_name,
                    "source": lead.source,
                    "dealership": dealership.name
                }
            )

            # Skip AI for manual leads or test leads
            if skip_ai_response or lead.source == "manual":
                logger.info(f"Skipping AI response for lead {lead_id} (source: {lead.source})")
                return {
                    "status": "skipped",
                    "reason": "manual_lead_or_test"
                }

            # Skip AI for test leads from Facebook
            if lead.source == "facebook" and lead.source_metadata:
                if lead.source_metadata.get("is_test"):
                    logger.info(f"Skipping AI response for test lead {lead_id}")
                    return {
                        "status": "skipped",
                        "reason": "test_lead"
                    }

            # Step 1: Generate AI response
            ai_result = self._generate_ai_response(lead, dealership, db)
            if not ai_result["success"]:
                return ai_result

            ai_response = ai_result["response"]

            # Step 2: Send email to customer
            email_result = self._send_customer_email(
                lead, dealership, ai_response
            )
            if not email_result["success"]:
                # Log email failure but don't fail the whole process
                logger.warning(f"Email sending failed for lead {lead_id}")

            # Step 3: Create conversation record
            conversation = self._create_conversation_record(
                lead, dealership, ai_response, db
            )

            # Step 4: Update lead status
            self._update_lead_status(lead, start_time, db)

            # Calculate response time
            end_time = datetime.now(timezone.utc)
            response_time_seconds = (end_time - start_time).total_seconds()

            logger.info(
                f"Lead {lead_id} processed successfully in {response_time_seconds:.2f}s",
                extra={
                    "lead_id": str(lead_id),
                    "response_time": response_time_seconds,
                    "ai_tokens": ai_result.get("tokens_used", 0),
                    "email_sent": email_result["success"]
                }
            )

            return {
                "status": "success",
                "lead_id": str(lead_id),
                "conversation_id": str(conversation.id) if conversation else None,
                "response_time_seconds": response_time_seconds,
                "ai_tokens_used": ai_result.get("tokens_used", 0),
                "email_sent": email_result["success"],
                "email_id": email_result.get("email_id")
            }

        except Exception as e:
            logger.error(f"Lead processing failed for {lead_id}: {str(e)}")
            return {
                "status": "failed",
                "lead_id": str(lead_id),
                "error": str(e)
            }

    def _generate_ai_response(
        self,
        lead: Lead,
        dealership: Dealership,
        db: Session
    ) -> dict:
        """Generate AI response for the lead."""
        try:
            # Generate AI response
            result = ai_service.generate_initial_response(
                customer_name=lead.customer_name or "kunde",
                vehicle_interest=lead.vehicle_interest,
                customer_message=lead.initial_message or "Henvendelse om bil",
                dealership_name=dealership.name,
                dealership_phone=dealership.phone,
                dealership_email=dealership.email,
                available_vehicles=None  # Vehicle inventory not yet implemented
            )

            return {
                "success": True,
                "response": result["response"],
                "confidence": result.get("confidence", 0.9),
                "tokens_used": result.get("tokens_used", 0),
                "model": result.get("model", "unknown")
            }

        except Exception as e:
            logger.error(f"AI response generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _send_customer_email(
        self,
        lead: Lead,
        dealership: Dealership,
        ai_response: str
    ) -> dict:
        """Send email to customer with AI response."""
        try:
            if not lead.customer_email:
                logger.warning(f"No email for lead {lead.id}, skipping email send")
                return {"success": False, "reason": "no_email"}

            # Generate subject line
            subject = f"Svar på din henvendelse"
            if lead.vehicle_interest:
                subject += f" - {lead.vehicle_interest}"

            result = email_service.send_initial_response(
                to_email=lead.customer_email,
                to_name=lead.customer_name or "kunde",
                subject=subject,
                ai_response=ai_response,
                dealership_name=dealership.name,
                dealership_phone=dealership.phone,
                dealership_email=dealership.email,
                dealership_address=dealership.address
            )

            if result["status"] == "sent":
                return {
                    "success": True,
                    "email_id": result.get("email_id")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_conversation_record(
        self,
        lead: Lead,
        dealership: Dealership,
        ai_response: str,
        db: Session
    ) -> Optional[Conversation]:
        """Create conversation record for AI response."""
        try:
            # Create inbound message (customer's inquiry)
            inbound = Conversation(
                lead_id=lead.id,
                dealership_id=dealership.id,
                channel="email" if lead.source == "email" else lead.source,
                direction="inbound",
                sender=lead.customer_name or "Customer",
                sender_type="customer",
                message_content=lead.initial_message or "Initial inquiry",
                message_metadata={"source": lead.source}
            )
            db.add(inbound)

            # Create outbound message (AI response)
            outbound = Conversation(
                lead_id=lead.id,
                dealership_id=dealership.id,
                channel="email",
                direction="outbound",
                sender="AI Assistant",
                sender_type="ai",
                message_content=ai_response,
                message_metadata={"automated": True, "ai_model": "claude-3-5-sonnet"}
            )
            db.add(outbound)

            db.commit()
            db.refresh(outbound)

            return outbound

        except Exception as e:
            logger.error(f"Failed to create conversation record: {str(e)}")
            db.rollback()
            return None

    def _update_lead_status(
        self,
        lead: Lead,
        start_time: datetime,
        db: Session
    ):
        """Update lead status after processing."""
        try:
            # Calculate first response time
            response_time = datetime.now(timezone.utc) - lead.created_at

            # Update lead
            lead.status = "contacted"
            lead.last_contact_at = datetime.now(timezone.utc)
            lead.first_response_time = response_time

            db.commit()

        except Exception as e:
            logger.error(f"Failed to update lead status: {str(e)}")
            db.rollback()


# Global lead processor instance
lead_processor = LeadProcessor()
