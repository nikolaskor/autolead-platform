"""
Email model for storing and processing incoming emails.

Emails are received via webhook (SendGrid Inbound Parse), classified by AI,
and potentially converted to leads.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class Email(Base):
    """
    Email model - represents an incoming email to be processed.

    Processing flow:
    1. Received via webhook (pending)
    2. Pre-filtered for spam (processing)
    3. AI classification (processing)
    4. Lead extraction if sales_inquiry (processing)
    5. Lead creation or archival (completed/failed)
    """
    __tablename__ = "emails"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    dealership_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dealerships.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )  # Set when email is converted to a lead

    # Email metadata
    message_id = Column(String(255), unique=True, nullable=False, index=True)  # Email Message-ID header
    from_email = Column(String(255), nullable=False, index=True)
    from_name = Column(String(255), nullable=True)
    to_email = Column(String(255), nullable=False)  # The dealership's forwarding address
    subject = Column(String(500), nullable=True)

    # Email content
    body_text = Column(Text, nullable=True)  # Plain text version
    body_html = Column(Text, nullable=True)  # HTML version
    raw_headers = Column(JSONB, nullable=True)  # Store all email headers
    attachments = Column(JSONB, nullable=True)  # List of attachment metadata [{filename, size, content_type}]

    # Processing status
    processing_status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True
    )  # pending, processing, completed, failed

    # AI classification results
    classification = Column(String(50), nullable=True, index=True)  # sales_inquiry, spam, other, uncertain
    classification_confidence = Column(Float, nullable=True)  # 0.0-1.0
    classification_reasoning = Column(Text, nullable=True)  # AI's explanation

    # Extracted lead data (if classified as sales_inquiry)
    extracted_data = Column(JSONB, nullable=True)  # Structured data for lead creation

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    received_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    dealership = relationship("Dealership", back_populates="emails")
    lead = relationship("Lead", back_populates="source_email", foreign_keys=[lead_id])

    # Indexes for common queries
    __table_args__ = (
        Index("idx_emails_status_received", processing_status, received_at.desc()),
        Index("idx_emails_dealership_received", dealership_id, received_at.desc()),
        Index("idx_emails_classification", classification, classification_confidence),
    )

    def __repr__(self):
        return f"<Email(id={self.id}, from='{self.from_email}', status='{self.processing_status}')>"
