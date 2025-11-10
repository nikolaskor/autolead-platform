"""
Pydantic schemas for Conversation API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation message."""
    
    lead_id: UUID
    message_content: str = Field(..., min_length=1)
    channel: str = Field(..., description="Channel: email, sms, facebook, manual")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": "123e4567-e89b-12d3-a456-426614174000",
                "message_content": "We have the Tesla Model 3 available for test drive this Saturday.",
                "channel": "email"
            }
        }


class ConversationResponse(BaseModel):
    """Schema for conversation responses."""
    
    id: UUID
    lead_id: UUID
    dealership_id: UUID
    channel: str
    direction: str  # inbound, outbound
    sender: Optional[str] = None
    sender_type: str  # customer, ai, human
    message_content: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "lead_id": "123e4567-e89b-12d3-a456-426614174001",
                "dealership_id": "123e4567-e89b-12d3-a456-426614174002",
                "channel": "email",
                "direction": "outbound",
                "sender": "AI",
                "sender_type": "ai",
                "message_content": "Takk for din interesse!",
                "created_at": "2025-11-05T10:35:00Z"
            }
        }

