"""
Conversation API endpoints.
Provides endpoints for viewing and creating conversation messages.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from ....core.database import get_db
from ....core.exceptions import NotFoundException
from ....api.deps import get_current_user, get_current_dealership
from ....models.conversation import Conversation
from ....models.lead import Lead
from ....models.user import User
from ....models.dealership import Dealership
from ....schemas import ConversationCreate, ConversationResponse

router = APIRouter()


@router.get("/leads/{lead_id}/conversations", response_model=List[ConversationResponse])
def get_conversations(
    lead_id: UUID,
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
    db: Session = Depends(get_db),
):
    """
    Get all conversations for a specific lead.
    
    - Returns conversations ordered by created_at (newest first)
    - Verifies lead belongs to user's dealership
    - Returns 404 if lead not found
    """
    # Verify lead exists and belongs to dealership
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.dealership_id == dealership.id
    ).first()
    
    if not lead:
        raise NotFoundException("Lead not found")
    
    # Get conversations for this lead
    conversations = db.query(Conversation).filter(
        Conversation.lead_id == lead_id
    ).order_by(Conversation.created_at.desc()).all()
    
    return [ConversationResponse.model_validate(conv) for conv in conversations]


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
    db: Session = Depends(get_db),
):
    """
    Create a new conversation message.
    
    - Automatically sets dealership_id
    - Sets sender information from authenticated user
    - Sender type is 'human' for manual messages
    - Direction is 'outbound' for messages from dealership
    - Returns 404 if lead not found
    """
    # Verify lead exists and belongs to dealership
    lead = db.query(Lead).filter(
        Lead.id == conversation_data.lead_id,
        Lead.dealership_id == dealership.id
    ).first()
    
    if not lead:
        raise NotFoundException("Lead not found")
    
    # Create conversation instance
    conversation = Conversation(
        lead_id=conversation_data.lead_id,
        dealership_id=dealership.id,
        channel=conversation_data.channel,
        direction="outbound",  # Message from dealership
        sender=user.name or user.email,
        sender_type="human",  # Manual message from user
        message_content=conversation_data.message_content,
    )
    
    db.add(conversation)
    
    # Update lead's last_contact_at
    lead.last_contact_at = datetime.utcnow()
    
    db.commit()
    db.refresh(conversation)
    
    return ConversationResponse.model_validate(conversation)

