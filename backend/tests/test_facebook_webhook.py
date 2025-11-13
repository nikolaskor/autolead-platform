"""
Tests for Facebook Lead Ads webhook endpoints.
"""
import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from app.main import app
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.services.facebook_client import FacebookLeadData


# Test client
client = TestClient(app)


class TestFacebookWebhookVerification:
    """Tests for GET /api/v1/webhooks/facebook (webhook verification)."""

    def test_webhook_verification_success(self):
        """Test successful webhook verification with correct token."""
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge_12345"
        }

        with patch("app.core.config.settings.FACEBOOK_VERIFY_TOKEN", "test_verify_token"):
            response = client.get("/api/v1/webhooks/facebook", params=params)

        assert response.status_code == 200
        assert response.text == "test_challenge_12345"

    def test_webhook_verification_wrong_token(self):
        """Test webhook verification fails with wrong token."""
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "test_challenge_12345"
        }

        with patch("app.core.config.settings.FACEBOOK_VERIFY_TOKEN", "correct_token"):
            response = client.get("/api/v1/webhooks/facebook", params=params)

        assert response.status_code == 403
        assert "Verification failed" in response.json()["detail"]

    def test_webhook_verification_wrong_mode(self):
        """Test webhook verification fails with wrong mode."""
        params = {
            "hub.mode": "unsubscribe",  # Wrong mode
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge_12345"
        }

        with patch("app.core.config.settings.FACEBOOK_VERIFY_TOKEN", "test_verify_token"):
            response = client.get("/api/v1/webhooks/facebook", params=params)

        assert response.status_code == 403

    def test_webhook_verification_missing_params(self):
        """Test webhook verification fails with missing parameters."""
        params = {
            "hub.mode": "subscribe"
            # Missing verify_token and challenge
        }

        response = client.get("/api/v1/webhooks/facebook", params=params)
        assert response.status_code == 403


class TestFacebookWebhookReceiver:
    """Tests for POST /api/v1/webhooks/facebook (leadgen receiver)."""

    def setup_method(self):
        """Set up test data for each test."""
        self.valid_webhook_payload = {
            "object": "page",
            "entry": [
                {
                    "id": "987654321",
                    "time": 1699901234,
                    "changes": [
                        {
                            "field": "leadgen",
                            "value": {
                                "leadgen_id": "123456789",
                                "page_id": "987654321",
                                "form_id": "456789123",
                                "created_time": 1699901234
                            }
                        }
                    ]
                }
            ]
        }

    def _generate_signature(self, payload: dict, secret: str) -> str:
        """Generate X-Hub-Signature-256 header."""
        payload_bytes = json.dumps(payload).encode()
        signature = hmac.new(
            key=secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    def test_webhook_receiver_valid_signature(self):
        """Test webhook receiver accepts valid signature."""
        app_secret = "test_app_secret"
        signature = self._generate_signature(self.valid_webhook_payload, app_secret)

        with patch("app.core.config.settings.FACEBOOK_APP_SECRET", app_secret):
            response = client.post(
                "/api/v1/webhooks/facebook",
                json=self.valid_webhook_payload,
                headers={"X-Hub-Signature-256": signature}
            )

        assert response.status_code == 200
        assert response.json() == {"status": "received"}

    def test_webhook_receiver_invalid_signature(self):
        """Test webhook receiver rejects invalid signature."""
        app_secret = "test_app_secret"

        with patch("app.core.config.settings.FACEBOOK_APP_SECRET", app_secret):
            response = client.post(
                "/api/v1/webhooks/facebook",
                json=self.valid_webhook_payload,
                headers={"X-Hub-Signature-256": "sha256=invalid_signature"}
            )

        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    def test_webhook_receiver_missing_signature(self):
        """Test webhook receiver rejects missing signature header."""
        with patch("app.core.config.settings.FACEBOOK_APP_SECRET", "test_secret"):
            response = client.post(
                "/api/v1/webhooks/facebook",
                json=self.valid_webhook_payload
                # No signature header
            )

        assert response.status_code == 401

    def test_webhook_receiver_malformed_json(self):
        """Test webhook receiver handles malformed JSON."""
        app_secret = "test_app_secret"

        # Send invalid JSON (as plain text)
        with patch("app.core.config.settings.FACEBOOK_APP_SECRET", app_secret):
            response = client.post(
                "/api/v1/webhooks/facebook",
                data="invalid json",
                headers={
                    "X-Hub-Signature-256": "sha256=test",
                    "Content-Type": "application/json"
                }
            )

        assert response.status_code == 400

    def test_webhook_receiver_processes_leadgen_event(self):
        """Test webhook receiver queues background task for leadgen event."""
        app_secret = "test_app_secret"
        signature = self._generate_signature(self.valid_webhook_payload, app_secret)

        with patch("app.core.config.settings.FACEBOOK_APP_SECRET", app_secret):
            with patch("app.api.v1.endpoints.facebook.process_facebook_lead") as mock_process:
                response = client.post(
                    "/api/v1/webhooks/facebook",
                    json=self.valid_webhook_payload,
                    headers={"X-Hub-Signature-256": signature}
                )

        assert response.status_code == 200
        # Note: Background tasks are executed after response, so we can't easily verify
        # the task was called without more complex async testing

    def test_webhook_receiver_ignores_non_leadgen_events(self):
        """Test webhook receiver ignores non-leadgen events."""
        payload = {
            "object": "page",
            "entry": [
                {
                    "id": "987654321",
                    "changes": [
                        {
                            "field": "feed",  # Not leadgen
                            "value": {"some": "data"}
                        }
                    ]
                }
            ]
        }

        app_secret = "test_app_secret"
        signature = self._generate_signature(payload, app_secret)

        with patch("app.core.config.settings.FACEBOOK_APP_SECRET", app_secret):
            response = client.post(
                "/api/v1/webhooks/facebook",
                json=payload,
                headers={"X-Hub-Signature-256": signature}
            )

        # Should still return 200 (acknowledges receipt)
        assert response.status_code == 200


class TestFacebookLeadProcessing:
    """Tests for lead processing logic."""

    @pytest.fixture
    def mock_facebook_client(self):
        """Mock FacebookClient for testing."""
        with patch("app.api.v1.endpoints.facebook.FacebookClient") as MockClient:
            mock_client = MockClient.return_value

            # Mock lead data
            mock_lead_data = FacebookLeadData(
                leadgen_id="123456789",
                created_time=datetime.utcnow(),
                field_data=[
                    {"name": "full_name", "values": ["Ola Nordmann"]},
                    {"name": "email", "values": ["ola@example.com"]},
                    {"name": "phone_number", "values": ["+4712345678"]},
                    {"name": "vehicle_interest", "values": ["Tesla Model 3"]}
                ],
                is_test=False
            )

            # Mock async method
            mock_client.get_lead = AsyncMock(return_value=mock_lead_data)

            yield mock_client

    def test_lead_data_parsing(self):
        """Test FacebookLeadData parses field_data correctly."""
        field_data = [
            {"name": "full_name", "values": ["Ola Nordmann"]},
            {"name": "email", "values": ["ola@example.com"]},
            {"name": "phone_number", "values": ["+4712345678"]},
            {"name": "vehicle_interest", "values": ["Tesla Model 3"]},
            {"name": "custom_question", "values": ["Looking for electric"]}
        ]

        lead_data = FacebookLeadData(
            leadgen_id="123",
            created_time=datetime.utcnow(),
            field_data=field_data,
            is_test=False
        )

        assert lead_data.customer_name == "Ola Nordmann"
        assert lead_data.customer_email == "ola@example.com"
        assert lead_data.customer_phone == "+4712345678"
        assert lead_data.vehicle_interest == "Tesla Model 3"
        assert "custom_question: Looking for electric" in lead_data.initial_message

    def test_lead_data_to_lead_dict(self):
        """Test FacebookLeadData converts to Lead model dict correctly."""
        field_data = [
            {"name": "full_name", "values": ["Ola Nordmann"]},
            {"name": "email", "values": ["ola@example.com"]}
        ]

        lead_data = FacebookLeadData(
            leadgen_id="123",
            created_time=datetime.utcnow(),
            field_data=field_data,
            is_test=False
        )

        dealership_id = "abc-123"
        lead_dict = lead_data.to_lead_dict(dealership_id)

        assert lead_dict["dealership_id"] == dealership_id
        assert lead_dict["source"] == "facebook"
        assert lead_dict["customer_name"] == "Ola Nordmann"
        assert lead_dict["customer_email"] == "ola@example.com"
        assert lead_dict["source_metadata"]["facebook_lead_id"] == "123"
        assert lead_dict["source_metadata"]["is_test"] is False

    def test_test_lead_detection(self):
        """Test system detects test leads from Facebook."""
        field_data = [
            {"name": "email", "values": ["test@test.com"]}
        ]

        lead_data = FacebookLeadData(
            leadgen_id="test_123",
            created_time=datetime.utcnow(),
            field_data=field_data,
            is_test=True  # Marked as test by Facebook
        )

        assert lead_data.is_test is True


class TestFacebookGraphAPIClient:
    """Tests for FacebookClient Graph API integration."""

    @pytest.mark.asyncio
    async def test_get_lead_success(self):
        """Test successful lead retrieval from Graph API."""
        mock_response_data = {
            "id": "123456789",
            "created_time": "2024-11-13T10:30:00+0000",
            "field_data": [
                {"name": "email", "values": ["test@example.com"]}
            ],
            "is_test": False
        }

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = MockAsyncClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get = AsyncMock(return_value=mock_response)

            from app.services.facebook_client import FacebookClient
            fb_client = FacebookClient(access_token="test_token")

            lead_data = await fb_client.get_lead("123456789")

            assert lead_data.leadgen_id == "123456789"
            assert lead_data.customer_email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_lead_auth_error(self):
        """Test Graph API returns auth error for invalid token."""
        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = MockAsyncClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "error": {"message": "Invalid access token"}
            }
            mock_client.get = AsyncMock(return_value=mock_response)

            from app.services.facebook_client import FacebookClient, FacebookAuthError
            fb_client = FacebookClient(access_token="invalid_token")

            with pytest.raises(FacebookAuthError):
                await fb_client.get_lead("123456789")

    @pytest.mark.asyncio
    async def test_get_lead_rate_limit(self):
        """Test Graph API handles rate limit errors."""
        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = MockAsyncClient.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_client.get = AsyncMock(return_value=mock_response)

            from app.services.facebook_client import FacebookClient, FacebookRateLimitError
            fb_client = FacebookClient(access_token="test_token")

            with pytest.raises(FacebookRateLimitError):
                await fb_client.get_lead("123456789")
