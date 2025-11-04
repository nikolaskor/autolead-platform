"""
Conversation model representing message history between dealership and customers.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class Conversation(Base):
    """
    Conversation model - represents a message in a lead's conversation history.
    
    Tracks all communications: AI responses, human replies, customer messages.
    Each conversation belongs to a lead and dealership.
    """
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    dealership_id = Column(UUID(as_uuid=True), ForeignKey("dealerships.id", ondelete="CASCADE"), nullable=False)
    
    # Message details
    channel = Column(String(50), nullable=False)      # email, sms, facebook, manual
    direction = Column(String(20), nullable=False)    # inbound, outbound
    sender = Column(String(255), nullable=True)       # Customer name, "AI", or user name
    sender_type = Column(String(20), nullable=True)   # customer, ai, human
    message_content = Column(String, nullable=False)
    
    # Metadata (flexible storage for channel-specific data)
    metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    dealership = relationship("Dealership", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        # Index on created_at DESC for conversation history queries
        Index("idx_conversations_created_desc", created_at.desc()),
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, lead_id={self.lead_id}, sender_type='{self.sender_type}')>"

