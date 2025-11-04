"""
User model representing sales reps, managers, and admins at dealerships.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class User(Base):
    """
    User model - represents sales reps, managers, and admins.
    
    Each user belongs to one dealership and has a role.
    Maps to Clerk user via clerk_user_id.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    dealership_id = Column(UUID(as_uuid=True), ForeignKey("dealerships.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Clerk integration
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic information
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    
    # Role: admin, manager, sales_rep
    role = Column(String(50), default="sales_rep", nullable=False)
    
    # Notification preferences (JSONB for flexibility)
    notification_preferences = Column(
        JSONB, 
        default={"sms": True, "email": True}, 
        nullable=False
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    dealership = relationship("Dealership", back_populates="users")
    assigned_leads = relationship("Lead", back_populates="assigned_user", foreign_keys="Lead.assigned_to")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

