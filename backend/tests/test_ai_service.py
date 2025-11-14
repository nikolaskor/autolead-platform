"""
Tests for AI Service (Claude API integration).
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ai_service import AIService, ai_service


class TestAIService:
    """Test suite for AIService class."""

    def test_init_with_valid_api_key(self):
        """Test AIService initialization with valid API key."""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key-123"
            service = AIService()
            assert service.client is not None
            assert service.model == "claude-3-5-sonnet-20241022"

    def test_init_without_api_key_raises_error(self):
        """Test AIService initialization fails without API key."""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not set"):
                AIService()

    @patch('app.services.ai_service.Anthropic')
    def test_generate_initial_response_success(self, mock_anthropic):
        """Test successful initial response generation."""
        # Mock Claude API response
        mock_message = Mock()
        mock_message.content = [Mock(text="Hei kunde! Takk for henvendelsen.")]
        mock_message.usage = Mock(input_tokens=100, output_tokens=50)
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            result = service.generate_initial_response(
                customer_name="Test Customer",
                vehicle_interest="Tesla Model 3",
                customer_message="Interessert i prøvekjøring",
                dealership_name="Test Bilforhandler",
                dealership_phone="+47 123 45 678",
                dealership_email="test@dealership.no"
            )
            
            assert result["response"] == "Hei kunde! Takk for henvendelsen."
            assert result["confidence"] == 0.9
            assert result["model"] == "claude-3-5-sonnet-20241022"
            assert result["tokens_used"] == 150
            assert "error" not in result

    @patch('app.services.ai_service.Anthropic')
    def test_generate_initial_response_with_available_vehicles(self, mock_anthropic):
        """Test initial response generation with vehicle inventory."""
        mock_message = Mock()
        mock_message.content = [Mock(text="Vi har Tesla på lager!")]
        mock_message.usage = Mock(input_tokens=150, output_tokens=60)
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            vehicles = [
                {"make": "Tesla", "model": "Model 3", "year": 2023, "price": 450000},
                {"make": "VW", "model": "ID.4", "year": 2023, "price": 380000}
            ]
            
            result = service.generate_initial_response(
                customer_name="Test Customer",
                vehicle_interest="Tesla Model 3",
                customer_message="Interessert i Tesla",
                dealership_name="Test Bilforhandler",
                available_vehicles=vehicles
            )
            
            assert result["response"] == "Vi har Tesla på lager!"
            assert result["confidence"] == 0.9

    @patch('app.services.ai_service.Anthropic')
    def test_generate_initial_response_fallback_on_error(self, mock_anthropic):
        """Test fallback response when AI API fails."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            result = service.generate_initial_response(
                customer_name="Test Customer",
                vehicle_interest="Tesla Model 3",
                customer_message="Interessert i bil",
                dealership_name="Test Bilforhandler"
            )
            
            assert "Hei Test Customer!" in result["response"]
            assert "Test Bilforhandler" in result["response"]
            assert result["confidence"] == 0.3
            assert result["model"] == "fallback"
            assert "error" in result
            assert "API Error" in result["error"]

    @patch('app.services.ai_service.Anthropic')
    def test_generate_follow_up_response_success(self, mock_anthropic):
        """Test successful follow-up response generation."""
        mock_message = Mock()
        mock_message.content = [Mock(text="Hei igjen! Er du fortsatt interessert?")]
        mock_message.usage = Mock(input_tokens=80, output_tokens=30)
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            previous_conversation = [
                {"sender_type": "ai", "message": "Hei! Takk for henvendelsen."},
                {"sender_type": "customer", "message": "Interessert i bil."}
            ]
            
            result = service.generate_follow_up_response(
                customer_name="Test Customer",
                vehicle_interest="Tesla Model 3",
                previous_conversation=previous_conversation,
                dealership_name="Test Bilforhandler",
                follow_up_number=1
            )
            
            assert result["response"] == "Hei igjen! Er du fortsatt interessert?"
            assert result["confidence"] == 0.85
            assert result["tokens_used"] == 110

    @patch('app.services.ai_service.Anthropic')
    def test_generate_follow_up_response_fallback_on_error(self, mock_anthropic):
        """Test fallback follow-up response when AI API fails."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("Network error")
        mock_anthropic.return_value = mock_client

        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            result = service.generate_follow_up_response(
                customer_name="Test Customer",
                vehicle_interest="Tesla",
                previous_conversation=[],
                dealership_name="Test Bilforhandler",
                follow_up_number=2
            )
            
            assert "Hei Test Customer!" in result["response"]
            assert result["confidence"] == 0.3
            assert result["model"] == "fallback"
            assert "error" in result

    def test_build_system_prompt_without_inventory(self):
        """Test system prompt generation without vehicle inventory."""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            prompt = service._build_system_prompt(
                dealership_name="Test Bilforhandler",
                dealership_phone="+47 123 45 678",
                dealership_email="test@dealership.no",
                available_vehicles=None
            )
            
            assert "Test Bilforhandler" in prompt
            assert "+47 123 45 678" in prompt
            assert "test@dealership.no" in prompt
            assert "norsk" in prompt.lower()
            assert "Biler på lager" not in prompt

    def test_build_system_prompt_with_inventory(self):
        """Test system prompt generation with vehicle inventory."""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            vehicles = [
                {"make": "Tesla", "model": "Model 3", "year": 2023},
                {"make": "VW", "model": "ID.4", "year": 2023}
            ]
            
            prompt = service._build_system_prompt(
                dealership_name="Test Bilforhandler",
                dealership_phone=None,
                dealership_email=None,
                available_vehicles=vehicles
            )
            
            assert "Biler på lager" in prompt
            assert "Tesla Model 3" in prompt
            assert "VW ID.4" in prompt

    def test_build_initial_response_prompt(self):
        """Test initial response prompt generation."""
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            service = AIService()
            
            prompt = service._build_initial_response_prompt(
                customer_name="Test Customer",
                vehicle_interest="Tesla Model 3",
                customer_message="Interessert i prøvekjøring"
            )
            
            assert "Test Customer" in prompt
            assert "Tesla Model 3" in prompt
            assert "Interessert i prøvekjøring" in prompt

    def test_global_ai_service_instance(self):
        """Test that global ai_service instance is available."""
        assert ai_service is not None
        assert isinstance(ai_service, AIService)
