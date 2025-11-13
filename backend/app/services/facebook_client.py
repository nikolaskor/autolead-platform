"""
Facebook Graph API client for Lead Ads integration.
Handles lead retrieval, field mapping, and error handling.
"""
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class FacebookLeadData:
    """Parsed Facebook lead data."""

    def __init__(
        self,
        leadgen_id: str,
        created_time: datetime,
        field_data: List[Dict[str, Any]],
        is_test: bool = False,
        raw_data: Optional[Dict[str, Any]] = None
    ):
        self.leadgen_id = leadgen_id
        self.created_time = created_time
        self.field_data = field_data
        self.is_test = is_test
        self.raw_data = raw_data or {}

        # Parse and map fields
        self._parse_fields()

    def _parse_fields(self):
        """Parse field_data array into accessible attributes."""
        self.customer_name = None
        self.customer_email = None
        self.customer_phone = None
        self.vehicle_interest = None
        self.custom_questions = []

        for field in self.field_data:
            field_name = field.get("name", "").lower()
            values = field.get("values", [])
            value = values[0] if values else None

            if not value:
                continue

            # Map common fields
            if field_name in ["full_name", "name", "first_name"]:
                self.customer_name = value
            elif field_name == "email":
                self.customer_email = value
            elif field_name in ["phone_number", "phone", "mobile"]:
                self.customer_phone = value
            elif field_name in ["vehicle_interest", "which_car", "car_interest", "vehicle"]:
                self.vehicle_interest = value
            else:
                # Store custom questions
                self.custom_questions.append({"question": field_name, "answer": value})

        # Concatenate custom questions into initial_message
        if self.custom_questions:
            self.initial_message = "\n".join([
                f"{q['question']}: {q['answer']}"
                for q in self.custom_questions
            ])
        else:
            self.initial_message = None

    def to_lead_dict(self, dealership_id: str) -> Dict[str, Any]:
        """
        Convert to Lead model dictionary.

        Args:
            dealership_id: UUID of the dealership this lead belongs to

        Returns:
            Dictionary compatible with Lead model
        """
        return {
            "dealership_id": dealership_id,
            "source": "facebook",
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "vehicle_interest": self.vehicle_interest,
            "initial_message": self.initial_message,
            "source_metadata": {
                "facebook_lead_id": self.leadgen_id,
                "created_time": self.created_time.isoformat(),
                "is_test": self.is_test,
                "field_data": self.field_data,
                "raw_data": self.raw_data
            }
        }


class FacebookGraphAPIError(Exception):
    """Base exception for Facebook Graph API errors."""
    pass


class FacebookAuthError(FacebookGraphAPIError):
    """Authentication/authorization error (invalid token)."""
    pass


class FacebookRateLimitError(FacebookGraphAPIError):
    """Rate limit exceeded error."""
    pass


class FacebookClient:
    """
    Facebook Graph API client for retrieving lead information.

    Handles:
    - Lead retrieval via Graph API
    - Field data parsing and mapping
    - Error handling and retries
    - Rate limit detection
    """

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Facebook client.

        Args:
            access_token: Page Access Token (defaults to settings if not provided)
        """
        self.access_token = access_token or settings.FACEBOOK_PAGE_ACCESS_TOKEN
        self.api_version = settings.FACEBOOK_GRAPH_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        if not self.access_token:
            logger.warning("Facebook Page Access Token not configured")

    async def get_lead(self, leadgen_id: str) -> FacebookLeadData:
        """
        Retrieve lead data from Facebook Graph API.

        Args:
            leadgen_id: The Facebook lead ID from the webhook

        Returns:
            Parsed FacebookLeadData object

        Raises:
            FacebookAuthError: If access token is invalid
            FacebookRateLimitError: If rate limit is exceeded
            FacebookGraphAPIError: For other API errors
        """
        if not self.access_token:
            raise FacebookAuthError("Facebook Page Access Token not configured")

        url = f"{self.base_url}/{leadgen_id}"
        params = {
            "access_token": self.access_token
        }

        logger.info(f"Fetching lead data from Facebook Graph API: {leadgen_id}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)

                # Handle different HTTP status codes
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_lead_response(data)

                elif response.status_code == 400:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"Facebook API error (400): {error_message}")
                    raise FacebookGraphAPIError(f"Bad request: {error_message}")

                elif response.status_code == 401:
                    logger.error("Facebook API authentication failed (401)")
                    raise FacebookAuthError("Invalid or expired Page Access Token")

                elif response.status_code == 403:
                    logger.error("Facebook API authorization failed (403)")
                    raise FacebookAuthError("Insufficient permissions to access lead data")

                elif response.status_code == 429:
                    logger.warning("Facebook API rate limit exceeded (429)")
                    raise FacebookRateLimitError("Rate limit exceeded. Please retry later.")

                else:
                    logger.error(f"Facebook API returned unexpected status: {response.status_code}")
                    raise FacebookGraphAPIError(f"Unexpected status code: {response.status_code}")

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching lead {leadgen_id} from Facebook")
            raise FacebookGraphAPIError("Request timeout")

        except httpx.RequestError as e:
            logger.error(f"Request error fetching lead {leadgen_id}: {str(e)}")
            raise FacebookGraphAPIError(f"Request failed: {str(e)}")

    def _parse_lead_response(self, data: Dict[str, Any]) -> FacebookLeadData:
        """
        Parse Graph API response into FacebookLeadData.

        Args:
            data: Raw response from Graph API

        Returns:
            Parsed FacebookLeadData object
        """
        leadgen_id = data.get("id")
        created_time_str = data.get("created_time")
        field_data = data.get("field_data", [])
        is_test = data.get("is_test", False)

        # Parse created_time
        try:
            created_time = datetime.fromisoformat(created_time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse created_time: {created_time_str}, using current time")
            created_time = datetime.utcnow()

        return FacebookLeadData(
            leadgen_id=leadgen_id,
            created_time=created_time,
            field_data=field_data,
            is_test=is_test,
            raw_data=data
        )

    async def verify_token(self) -> bool:
        """
        Verify that the access token is valid.

        Returns:
            True if token is valid, False otherwise
        """
        if not self.access_token:
            return False

        url = f"{self.base_url}/me"
        params = {"access_token": self.access_token}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error verifying Facebook token: {str(e)}")
            return False
