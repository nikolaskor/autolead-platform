"""
Dealership model representing car dealership organizations.
Each dealership is a separate tenant in the multi-tenant system.
"""
from sqlalchemy import Column, String, DateTime, func, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class Dealership(Base):
    """
    Dealership model - represents a car dealership organization.
    
    Each dealership is isolated from others (multi-tenant architecture).
    Maps to Clerk organization via clerk_org_id.
    """
    __tablename__ = "dealerships"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(50), nullable=True)
    address = Column(String, nullable=True)
    
    # Clerk integration
    clerk_org_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Subscription information
    subscription_status = Column(String(50), default="active")  # active, trial, cancelled
    subscription_tier = Column(String(50), default="starter")   # starter, professional, enterprise

    # Email integration settings
    email_integration_enabled = Column(Boolean, default=False, nullable=False)
    email_forwarding_address = Column(String(255), unique=True, nullable=True)  # e.g., bnh-abc123@leads.autolead.no
    email_integration_settings = Column(JSONB, nullable=True)  # Future: IMAP credentials, filters, etc.

    # Facebook Lead Ads integration settings
    facebook_integration_enabled = Column(Boolean, default=False, nullable=False)
    facebook_page_tokens = Column(JSONB, nullable=True)  # Encrypted Page Access Tokens: {"page_id": "encrypted_token"}
    facebook_integration_settings = Column(JSONB, nullable=True)  # App ID, webhook settings, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="dealership", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="dealership", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="dealership", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="dealership", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        # Email validation using PostgreSQL regex (case-insensitive)
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'",
            name="valid_dealership_email"
        ),
    )

    def __repr__(self):
        return f"<Dealership(id={self.id}, name='{self.name}')>"

