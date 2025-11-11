"""
Lead model representing customer inquiries from all sources.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Index, CheckConstraint, Interval
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class Lead(Base):
    """
    Lead model - represents a customer inquiry.
    
    Captures leads from website forms, email, Facebook, and manual entry.
    Each lead belongs to one dealership (multi-tenant).
    """
    __tablename__ = "leads"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    dealership_id = Column(UUID(as_uuid=True), ForeignKey("dealerships.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Source tracking
    source = Column(String(50), nullable=False, index=True)  # website, email, facebook, manual
    source_url = Column(String, nullable=True)
    source_metadata = Column(JSONB, nullable=True)  # Store raw data for debugging
    
    # Status
    status = Column(String(50), default="new", nullable=False, index=True)  # new, contacted, qualified, won, lost
    
    # Customer information
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True, index=True)
    customer_phone = Column(String(50), nullable=True)
    
    # Lead details
    vehicle_interest = Column(String(255), nullable=True)
    initial_message = Column(String, nullable=True)
    lead_score = Column(Integer, default=50, nullable=False)  # 1-100
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance tracking
    first_response_time = Column(Interval, nullable=True)
    
    # Relationships
    dealership = relationship("Dealership", back_populates="leads")
    assigned_user = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_to])
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    source_email = relationship("Email", back_populates="lead", uselist=False)  # One-to-one: lead can have one source email
    
    # Constraints
    __table_args__ = (
        # Email validation using PostgreSQL regex
        CheckConstraint(
            "customer_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$' OR customer_email IS NULL",
            name="valid_email"
        ),
        # Index on created_at DESC for recent leads queries
        Index("idx_leads_created_desc", created_at.desc()),
    )
    
    def __repr__(self):
        return f"<Lead(id={self.id}, customer_name='{self.customer_name}', status='{self.status}')>"

