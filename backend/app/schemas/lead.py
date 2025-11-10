"""
Pydantic schemas for Lead API endpoints.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class LeadBase(BaseModel):
    """Base lead schema with common fields."""
    
    customer_name: Optional[str] = None
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    vehicle_interest: Optional[str] = None
    initial_message: Optional[str] = None
    source: str = Field(..., description="Lead source: website, email, facebook, manual")
    source_url: Optional[str] = None


class LeadCreate(LeadBase):
    """Schema for creating a new lead."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "Ola Nordmann",
                "customer_email": "ola@example.com",
                "customer_phone": "+47 123 45 678",
                "vehicle_interest": "Tesla Model 3",
                "initial_message": "Interested in test drive this weekend",
                "source": "website",
                "source_url": "https://dealership.no/contact"
            }
        }


class LeadUpdate(BaseModel):
    """Schema for updating a lead (partial updates)."""
    
    status: Optional[str] = Field(None, description="Lead status: new, contacted, qualified, won, lost")
    assigned_to: Optional[UUID] = Field(None, description="User ID to assign lead to")
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    vehicle_interest: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "contacted",
                "assigned_to": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class UserResponse(BaseModel):
    """Minimal user info for lead responses."""
    
    id: UUID
    name: Optional[str]
    email: str
    role: str
    
    class Config:
        from_attributes = True


class LeadResponse(LeadBase):
    """Schema for lead responses."""
    
    id: UUID
    dealership_id: UUID
    status: str
    lead_score: Optional[int] = None
    assigned_to: Optional[UUID] = None
    created_at: datetime
    last_contact_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    
    # Include assigned user details if available
    assigned_user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "dealership_id": "123e4567-e89b-12d3-a456-426614174001",
                "customer_name": "Ola Nordmann",
                "customer_email": "ola@example.com",
                "customer_phone": "+47 123 45 678",
                "vehicle_interest": "Tesla Model 3",
                "initial_message": "Interested in test drive",
                "source": "website",
                "source_url": "https://dealership.no/contact",
                "status": "new",
                "lead_score": 75,
                "created_at": "2025-11-05T10:30:00Z",
                "last_contact_at": None,
                "converted_at": None
            }
        }


class LeadListResponse(LeadResponse):
    """Schema for lead list items (includes conversation count)."""
    
    conversation_count: int = 0
    
    class Config:
        from_attributes = True

