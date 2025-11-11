"""
Pydantic schemas for API request/response validation.
"""
from .common import ErrorResponse, SuccessResponse, PaginatedResponse
from .lead import LeadCreate, LeadUpdate, LeadResponse, LeadListResponse, UserResponse
from .conversation import ConversationCreate, ConversationResponse
from .webhook import FormWebhookRequest, FormWebhookResponse

__all__ = [
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadListResponse",
    "UserResponse",
    "ConversationCreate",
    "ConversationResponse",
    "FormWebhookRequest",
    "FormWebhookResponse",
]

