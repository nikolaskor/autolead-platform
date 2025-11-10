"""
Pydantic schemas for Email API endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class EmailBase(BaseModel):
    """Base email schema with common fields."""
    from_email: str
    from_name: Optional[str] = None
    to_email: str
    subject: Optional[str] = None


class EmailCreate(EmailBase):
    """Schema for creating a new email record."""
    message_id: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    raw_headers: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    dealership_id: UUID


class EmailResponse(EmailBase):
    """Schema for email response."""
    id: UUID
    dealership_id: UUID
    lead_id: Optional[UUID] = None
    message_id: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    raw_headers: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    processing_status: str
    classification: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_reasoning: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    received_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmailListResponse(BaseModel):
    """Schema for paginated email list response."""
    emails: List[EmailResponse]
    total: int
    page: int = 1
    page_size: int = 50


class EmailClassificationResult(BaseModel):
    """Schema for AI classification result."""
    classification: str = Field(..., description="sales_inquiry, spam, other, or uncertain")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    reasoning: str = Field(..., description="Explanation for the classification")


class EmailLeadExtraction(BaseModel):
    """Schema for extracted lead data from email."""
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    car_interest: Optional[str] = None
    inquiry_summary: Optional[str] = None
    urgency: str = Field(default="medium", description="high, medium, or low")
    source: str = Field(default="email", description="Email source identifier")
