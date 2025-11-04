"""
Dealership model representing car dealership organizations.
Each dealership is a separate tenant in the multi-tenant system.
"""
from sqlalchemy import Column, String, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
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
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(String, nullable=True)
    
    # Clerk integration
    clerk_org_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Subscription information
    subscription_status = Column(String(50), default="active")  # active, trial, cancelled
    subscription_tier = Column(String(50), default="starter")   # starter, professional, enterprise
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="dealership", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="dealership", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="dealership", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dealership(id={self.id}, name='{self.name}')>"

