"""
Pydantic schemas for webhook endpoints.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID


class FormWebhookRequest(BaseModel):
    """Schema for website form webhook requests."""

    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    email: EmailStr = Field(..., description="Customer email address")
    phone: Optional[str] = Field(None, max_length=50, description="Customer phone number")
    vehicle_interest: Optional[str] = Field(None, max_length=255, description="Vehicle of interest")
    message: str = Field(..., min_length=1, description="Customer message")
    source_url: Optional[str] = Field(None, description="URL where form was submitted")

    @validator('name')
    def name_must_not_be_empty(cls, v):
        """Validate that name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip()

    @validator('message')
    def message_must_not_be_empty(cls, v):
        """Validate that message is not just whitespace."""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace')
        return v.strip()

    @validator('phone')
    def phone_must_not_be_empty(cls, v):
        """Validate that phone is not just whitespace if provided."""
        if v and not v.strip():
            return None
        return v.strip() if v else None

    @validator('vehicle_interest')
    def vehicle_interest_must_not_be_empty(cls, v):
        """Validate that vehicle_interest is not just whitespace if provided."""
        if v and not v.strip():
            return None
        return v.strip() if v else None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ola Nordmann",
                "email": "ola@example.com",
                "phone": "+47 123 45 678",
                "vehicle_interest": "Tesla Model 3",
                "message": "I'm interested in a test drive this weekend",
                "source_url": "https://dealership.no/contact"
            }
        }


class FormWebhookResponse(BaseModel):
    """Schema for webhook response."""

    lead_id: UUID
    status: str = Field(..., description="Creation status: created or updated")

    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "created"
            }
        }
