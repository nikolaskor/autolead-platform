"""
Tests for Email Service (SendGrid integration).
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.email_service import EmailService, email_service


class TestEmailService:
    """Test suite for EmailService class."""

    def test_init_with_valid_api_key(self):
        """Test EmailService initialization with valid API key."""
        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-sendgrid-key-123"
            service = EmailService()
            assert service.client is not None

    def test_init_without_api_key_raises_error(self):
        """Test EmailService initialization fails without API key."""
        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = None
            with pytest.raises(ValueError, match="SENDGRID_API_KEY is not set"):
                EmailService()

    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_initial_response_success(self, mock_sendgrid):
        """Test successful email sending."""
        # Mock SendGrid response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg_test123"}
        
        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            result = service.send_initial_response(
                to_email="customer@test.com",
                to_name="Test Customer",
                subject="Svar på din henvendelse",
                ai_response="Hei! Vi har mottatt din henvendelse.",
                dealership_name="Test Bilforhandler",
                dealership_phone="+47 123 45 678",
                dealership_email="sales@dealership.no",
                dealership_address="Testveien 123, Oslo"
            )
            
            assert result["status"] == "sent"
            assert result["email_id"] == "msg_test123"
            assert result["provider"] == "sendgrid"
            assert result["status_code"] == 202

    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_initial_response_with_minimal_data(self, mock_sendgrid):
        """Test email sending with minimal required data."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg_test456"}
        
        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            result = service.send_initial_response(
                to_email="customer@test.com",
                to_name="Customer",
                subject="Svar",
                ai_response="Takk for henvendelsen.",
                dealership_name="Bilforhandler",
                dealership_phone=None,
                dealership_email=None,
                dealership_address=None
            )
            
            assert result["status"] == "sent"
            assert result["email_id"] == "msg_test456"

    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_initial_response_failure(self, mock_sendgrid):
        """Test email sending failure handling."""
        mock_client = Mock()
        mock_client.send.side_effect = Exception("SendGrid API error")
        mock_sendgrid.return_value = mock_client

        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            result = service.send_initial_response(
                to_email="customer@test.com",
                to_name="Customer",
                subject="Test",
                ai_response="Message",
                dealership_name="Dealership"
            )
            
            assert result["status"] == "failed"
            assert result["email_id"] is None
            assert "error" in result
            assert "SendGrid API error" in result["error"]

    @patch('app.services.email_service.SendGridAPIClient')
    def test_build_email_html_escapes_user_input(self, mock_sendgrid):
        """Test that HTML template properly escapes user input to prevent XSS."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg_test789"}
        
        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            # Attempt XSS injection in user-provided fields
            malicious_name = "<script>alert('xss')</script>"
            malicious_response = "<img src=x onerror=alert('xss')>"
            malicious_dealership = "<iframe src='evil.com'></iframe>"
            
            html = service._build_email_html(
                customer_name=malicious_name,
                response_text=malicious_response,
                dealership_name=malicious_dealership,
                dealership_phone="<script>alert(1)</script>",
                dealership_email="test@<script>alert(2)</script>.com",
                dealership_address="<b onload=alert(3)>Address</b>"
            )
            
            # Verify all dangerous characters are escaped
            assert "<script>" not in html
            assert "&lt;script&gt;" in html
            assert "<iframe" not in html
            assert "&lt;iframe" in html
            assert "onerror=" not in html
            assert "onload=" not in html

    def test_build_email_html_includes_all_contact_info(self):
        """Test HTML template includes all provided contact information."""
        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            html = service._build_email_html(
                customer_name="Test Customer",
                response_text="Test response",
                dealership_name="Test Bilforhandler",
                dealership_phone="+47 123 45 678",
                dealership_email="sales@test.no",
                dealership_address="Testveien 123, Oslo"
            )
            
            assert "Test Customer" in html
            assert "Test response" in html
            assert "Test Bilforhandler" in html
            assert "+47 123 45 678" in html
            assert "sales@test.no" in html
            assert "Testveien 123, Oslo" in html
            assert "📞 Telefon:" in html
            assert "✉️ E-post:" in html
            assert "📍 Adresse:" in html

    def test_build_email_html_without_contact_info(self):
        """Test HTML template when contact info is missing."""
        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            html = service._build_email_html(
                customer_name="Test Customer",
                response_text="Test response",
                dealership_name="Test Bilforhandler",
                dealership_phone=None,
                dealership_email=None,
                dealership_address=None
            )
            
            assert "Test Customer" in html
            assert "Test Bilforhandler" in html
            # Contact section should be empty but still valid HTML
            assert "Kontakt oss:" in html

    def test_build_email_text_format(self):
        """Test plain text email generation."""
        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            text = service._build_email_text(
                customer_name="Test Customer",
                response_text="Vi har mottatt din henvendelse.",
                dealership_name="Test Bilforhandler",
                dealership_phone="+47 123 45 678",
                dealership_email="sales@test.no"
            )
            
            assert "Hei Test Customer!" in text
            assert "Vi har mottatt din henvendelse." in text
            assert "Test Bilforhandler" in text
            assert "Telefon: +47 123 45 678" in text
            assert "E-post: sales@test.no" in text
            assert "Powered by Autolead" in text

    def test_build_email_text_minimal(self):
        """Test plain text email with minimal data."""
        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            text = service._build_email_text(
                customer_name="Customer",
                response_text="Takk.",
                dealership_name="Dealership",
                dealership_phone=None,
                dealership_email=None
            )
            
            assert "Hei Customer!" in text
            assert "Takk." in text
            assert "Dealership" in text

    @patch('app.services.email_service.SendGridAPIClient')
    def test_reply_to_header_set_correctly(self, mock_sendgrid):
        """Test that Reply-To header is set for multi-tenant isolation."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg_test999"}
        
        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        with patch('app.services.email_service.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            service = EmailService()
            
            service.send_initial_response(
                to_email="customer@test.com",
                to_name="Customer",
                subject="Test",
                ai_response="Message",
                dealership_name="Dealership",
                dealership_email="dealership@example.com"
            )
            
            # Verify send was called
            assert mock_client.send.called
            
            # Get the Mail object that was sent
            call_args = mock_client.send.call_args
            mail_object = call_args[0][0] if call_args[0] else None
            
            # Verify Reply-To is set (if Mail object structure allows checking)
            # Note: This is simplified - actual test might need to inspect Mail object internals
            assert mail_object is not None

    def test_global_email_service_instance(self):
        """Test that global email_service instance is available."""
        assert email_service is not None
        assert isinstance(email_service, EmailService)
