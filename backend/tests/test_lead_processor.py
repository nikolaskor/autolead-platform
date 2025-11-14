"""
Tests for Lead Processor Service (orchestrates AI response workflow).
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from sqlalchemy.orm import Session

from app.services.lead_processor import LeadProcessor, lead_processor
from app.models.lead import Lead
from app.models.dealership import Dealership
from app.models.conversation import Conversation


class TestLeadProcessor:
    """Test suite for LeadProcessor class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def test_dealership(self):
        """Create a test dealership."""
        return Dealership(
            id=uuid4(),
            name="Test Bilforhandler",
            email="test@dealership.no",
            phone="+47 123 45 678",
            address="Testveien 123, Oslo",
            clerk_org_id="org_test123",
            subscription_status="active",
            subscription_tier="starter"
        )

    @pytest.fixture
    def test_lead(self, test_dealership):
        """Create a test lead."""
        return Lead(
            id=uuid4(),
            dealership_id=test_dealership.id,
            source="website",
            status="new",
            customer_name="Test Customer",
            customer_email="customer@test.com",
            customer_phone="+47 987 65 432",
            vehicle_interest="Tesla Model 3",
            initial_message="Interessert i prøvekjøring",
            lead_score=75,
            created_at=datetime.now(tz.utc)
        )

    @pytest.mark.asyncio
    async def test_process_new_lead_success(self, mock_db, test_lead, test_dealership):
        """Test successful lead processing workflow."""
        # Setup mock database queries
        mock_db.query().filter().first.side_effect = [test_lead, test_dealership]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.rollback = Mock()

        processor = LeadProcessor()

        # Mock AI service
        with patch('app.services.lead_processor.ai_service') as mock_ai:
            mock_ai.generate_initial_response.return_value = {
                "response": "Hei! Takk for henvendelsen.",
                "confidence": 0.9,
                "model": "claude-3-5-sonnet-20241022",
                "tokens_used": 150
            }

            # Mock email service
            with patch('app.services.lead_processor.email_service') as mock_email:
                mock_email.send_initial_response.return_value = {
                    "status": "sent",
                    "email_id": "msg_test123",
                    "provider": "sendgrid",
                    "status_code": 202
                }

                result = await processor.process_new_lead(
                    lead_id=test_lead.id,
                    db=mock_db,
                    skip_ai_response=False
                )

                assert result["status"] == "success"
                assert result["lead_id"] == str(test_lead.id)
                assert result["email_sent"] is True
                assert result["ai_tokens_used"] == 150
                assert "response_time_seconds" in result

    @pytest.mark.asyncio
    async def test_process_new_lead_skip_ai_for_manual(self, mock_db, test_lead, test_dealership):
        """Test that manual leads skip AI processing."""
        test_lead.source = "manual"
        mock_db.query().filter().first.side_effect = [test_lead, test_dealership]

        processor = LeadProcessor()
        result = await processor.process_new_lead(
            lead_id=test_lead.id,
            db=mock_db,
            skip_ai_response=False
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "manual_lead_or_test"

    @pytest.mark.asyncio
    async def test_process_new_lead_skip_ai_flag(self, mock_db, test_lead, test_dealership):
        """Test that skip_ai_response flag is respected."""
        mock_db.query().filter().first.side_effect = [test_lead, test_dealership]

        processor = LeadProcessor()
        result = await processor.process_new_lead(
            lead_id=test_lead.id,
            db=mock_db,
            skip_ai_response=True
        )

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_process_new_lead_skip_facebook_test(self, mock_db, test_lead, test_dealership):
        """Test that Facebook test leads are skipped."""
        test_lead.source = "facebook"
        test_lead.source_metadata = {"is_test": True}
        mock_db.query().filter().first.side_effect = [test_lead, test_dealership]

        processor = LeadProcessor()
        result = await processor.process_new_lead(
            lead_id=test_lead.id,
            db=mock_db,
            skip_ai_response=False
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "test_lead"

    @pytest.mark.asyncio
    async def test_process_new_lead_not_found(self, mock_db):
        """Test handling of non-existent lead."""
        mock_db.query().filter().first.return_value = None

        processor = LeadProcessor()
        result = await processor.process_new_lead(
            lead_id=uuid4(),
            db=mock_db,
            skip_ai_response=False
        )

        assert result["status"] == "failed"
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_process_new_lead_dealership_not_found(self, mock_db, test_lead):
        """Test handling of non-existent dealership."""
        mock_db.query().filter().first.side_effect = [test_lead, None]

        processor = LeadProcessor()
        result = await processor.process_new_lead(
            lead_id=test_lead.id,
            db=mock_db,
            skip_ai_response=False
        )

        assert result["status"] == "failed"
        assert "Dealership" in result["error"]

    @pytest.mark.asyncio
    async def test_process_new_lead_ai_failure_returns_error(self, mock_db, test_lead, test_dealership):
        """Test handling of AI service failure."""
        mock_db.query().filter().first.side_effect = [test_lead, test_dealership]

        processor = LeadProcessor()

        with patch('app.services.lead_processor.ai_service') as mock_ai:
            mock_ai.generate_initial_response.side_effect = Exception("AI API error")

            result = await processor.process_new_lead(
                lead_id=test_lead.id,
                db=mock_db,
                skip_ai_response=False
            )

            assert result["status"] == "failed"
            assert "AI API error" in result["error"]

    @pytest.mark.asyncio
    async def test_process_new_lead_email_failure_continues(self, mock_db, test_lead, test_dealership):
        """Test that email failure doesn't stop the workflow."""
        mock_db.query().filter().first.side_effect = [test_lead, test_dealership]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        processor = LeadProcessor()

        with patch('app.services.lead_processor.ai_service') as mock_ai:
            mock_ai.generate_initial_response.return_value = {
                "response": "Hei!",
                "confidence": 0.9,
                "model": "claude",
                "tokens_used": 50
            }

            with patch('app.services.lead_processor.email_service') as mock_email:
                mock_email.send_initial_response.return_value = {
                    "status": "failed",
                    "error": "SendGrid error"
                }

                result = await processor.process_new_lead(
                    lead_id=test_lead.id,
                    db=mock_db,
                    skip_ai_response=False
                )

                # Workflow should complete despite email failure
                assert result["status"] == "success"
                assert result["email_sent"] is False

    @pytest.mark.asyncio
    async def test_process_new_lead_no_customer_email(self, mock_db, test_lead, test_dealership):
        """Test handling of lead without customer email."""
        test_lead.customer_email = None
        mock_db.query().filter().first.side_effect = [test_lead, test_dealership]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        processor = LeadProcessor()

        with patch('app.services.lead_processor.ai_service') as mock_ai:
            mock_ai.generate_initial_response.return_value = {
                "response": "Hei!",
                "confidence": 0.9,
                "model": "claude",
                "tokens_used": 50
            }

            result = await processor.process_new_lead(
                lead_id=test_lead.id,
                db=mock_db,
                skip_ai_response=False
            )

            assert result["status"] == "success"
            assert result["email_sent"] is False

    def test_generate_ai_response_success(self, mock_db, test_lead, test_dealership):
        """Test AI response generation."""
        processor = LeadProcessor()

        with patch('app.services.lead_processor.ai_service') as mock_ai:
            mock_ai.generate_initial_response.return_value = {
                "response": "Hei kunde!",
                "confidence": 0.9,
                "model": "claude-3-5-sonnet-20241022",
                "tokens_used": 100
            }

            result = processor._generate_ai_response(test_lead, test_dealership, mock_db)

            assert result["success"] is True
            assert result["response"] == "Hei kunde!"
            assert result["confidence"] == 0.9
            assert result["tokens_used"] == 100

    def test_generate_ai_response_failure(self, mock_db, test_lead, test_dealership):
        """Test AI response generation failure."""
        processor = LeadProcessor()

        with patch('app.services.lead_processor.ai_service') as mock_ai:
            mock_ai.generate_initial_response.side_effect = Exception("API error")

            result = processor._generate_ai_response(test_lead, test_dealership, mock_db)

            assert result["success"] is False
            assert "error" in result

    def test_send_customer_email_success(self, test_lead, test_dealership):
        """Test email sending."""
        processor = LeadProcessor()

        with patch('app.services.lead_processor.email_service') as mock_email:
            mock_email.send_initial_response.return_value = {
                "status": "sent",
                "email_id": "msg_123"
            }

            result = processor._send_customer_email(
                test_lead,
                test_dealership,
                "Test response"
            )

            assert result["success"] is True
            assert result["email_id"] == "msg_123"

    def test_send_customer_email_no_email_address(self, test_lead, test_dealership):
        """Test email sending when customer has no email."""
        test_lead.customer_email = None
        processor = LeadProcessor()

        result = processor._send_customer_email(
            test_lead,
            test_dealership,
            "Test response"
        )

        assert result["success"] is False
        assert result["reason"] == "no_email"

    def test_send_customer_email_failure(self, test_lead, test_dealership):
        """Test email sending failure."""
        processor = LeadProcessor()

        with patch('app.services.lead_processor.email_service') as mock_email:
            mock_email.send_initial_response.side_effect = Exception("Email error")

            result = processor._send_customer_email(
                test_lead,
                test_dealership,
                "Test response"
            )

            assert result["success"] is False
            assert "error" in result

    def test_create_conversation_record_success(self, mock_db, test_lead, test_dealership):
        """Test conversation record creation."""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.rollback = Mock()

        processor = LeadProcessor()
        conversation = processor._create_conversation_record(
            test_lead,
            test_dealership,
            "AI response text",
            mock_db
        )

        assert mock_db.add.call_count == 2  # Inbound + Outbound
        assert mock_db.commit.called
        assert conversation is not None

    def test_create_conversation_record_failure(self, mock_db, test_lead, test_dealership):
        """Test conversation record creation failure."""
        mock_db.add = Mock()
        mock_db.commit.side_effect = Exception("DB error")
        mock_db.rollback = Mock()

        processor = LeadProcessor()
        conversation = processor._create_conversation_record(
            test_lead,
            test_dealership,
            "AI response",
            mock_db
        )

        assert conversation is None
        assert mock_db.rollback.called

    def test_update_lead_status_success(self, mock_db, test_lead):
        """Test lead status update."""
        mock_db.commit = Mock()
        mock_db.rollback = Mock()

        processor = LeadProcessor()
        processor._update_lead_status(test_lead, datetime.now(tz.utc), mock_db)

        assert test_lead.status == "contacted"
        assert test_lead.last_contact_at is not None
        assert test_lead.first_response_time is not None
        assert mock_db.commit.called

    def test_update_lead_status_failure(self, mock_db, test_lead):
        """Test lead status update failure."""
        mock_db.commit.side_effect = Exception("DB error")
        mock_db.rollback = Mock()

        processor = LeadProcessor()
        processor._update_lead_status(test_lead, datetime.now(tz.utc), mock_db)

        assert mock_db.rollback.called

    def test_global_lead_processor_instance(self):
        """Test that global lead_processor instance is available."""
        assert lead_processor is not None
        assert isinstance(lead_processor, LeadProcessor)
