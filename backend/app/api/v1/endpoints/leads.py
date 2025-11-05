"""
Lead API endpoints.
Provides CRUD operations for leads with authentication and multi-tenant isolation.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional
from uuid import UUID
import math

from ....core.database import get_db
from ....core.exceptions import NotFoundException
from ....api.deps import get_current_user, get_current_dealership
from ....models.lead import Lead
from ....models.user import User
from ....models.dealership import Dealership
from ....models.conversation import Conversation
from ....schemas import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListResponse,
    PaginatedResponse,
)

router = APIRouter()


@router.get("/leads", response_model=PaginatedResponse[LeadListResponse])
def list_leads(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search by customer name or email"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
    db: Session = Depends(get_db),
):
    """
    List leads with filtering and pagination.
    
    - **status**: Filter by lead status (new, contacted, qualified, won, lost)
    - **source**: Filter by lead source (website, email, facebook, manual)
    - **search**: Search by customer name or email
    - **limit**: Number of items per page (1-100)
    - **offset**: Pagination offset
    
    Returns paginated list of leads with conversation counts.
    """
    # Base query with relationship loading
    query = db.query(Lead).options(
        joinedload(Lead.assigned_user)
    ).filter(
        Lead.dealership_id == dealership.id
    )
    
    # Apply filters
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    
    if source:
        query = query.filter(Lead.source == source)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Lead.customer_name.ilike(search_term),
                Lead.customer_email.ilike(search_term)
            )
        )
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and order
    leads = query.order_by(Lead.created_at.desc()).limit(limit).offset(offset).all()
    
    # Add conversation counts
    lead_responses = []
    for lead in leads:
        conversation_count = db.query(func.count(Conversation.id)).filter(
            Conversation.lead_id == lead.id
        ).scalar()
        
        lead_dict = LeadListResponse.model_validate(lead).model_dump()
        lead_dict['conversation_count'] = conversation_count
        lead_responses.append(LeadListResponse(**lead_dict))
    
    # Calculate pages
    pages = math.ceil(total / limit) if total > 0 else 0
    page = (offset // limit) + 1
    
    return PaginatedResponse(
        items=lead_responses,
        total=total,
        page=page,
        pages=pages,
        limit=limit
    )


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: UUID,
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
    db: Session = Depends(get_db),
):
    """
    Get a single lead by ID with full details.
    
    Returns lead information including assigned user details.
    Returns 404 if lead not found or belongs to different dealership.
    """
    lead = db.query(Lead).options(
        joinedload(Lead.assigned_user)
    ).filter(
        Lead.id == lead_id,
        Lead.dealership_id == dealership.id
    ).first()
    
    if not lead:
        raise NotFoundException("Lead not found")
    
    return LeadResponse.model_validate(lead)


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    lead_data: LeadCreate,
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
    db: Session = Depends(get_db),
):
    """
    Create a new lead manually.
    
    - Automatically assigns to current user's dealership
    - Sets initial status to 'new'
    - Does NOT trigger AI auto-response (manual leads only)
    
    Returns the created lead with 201 status.
    """
    # Create lead instance
    lead = Lead(
        dealership_id=dealership.id,
        status="new",
        lead_score=50,  # Default score
        **lead_data.model_dump()
    )
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    return LeadResponse.model_validate(lead)


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: UUID,
    lead_update: LeadUpdate,
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
    db: Session = Depends(get_db),
):
    """
    Update a lead (partial update).
    
    - Can update status, assignment, and customer details
    - Only fields provided in request are updated
    - Returns 404 if lead not found
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.dealership_id == dealership.id
    ).first()
    
    if not lead:
        raise NotFoundException("Lead not found")
    
    # Update only provided fields
    update_data = lead_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    db.commit()
    db.refresh(lead)
    
    return LeadResponse.model_validate(lead)


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: UUID,
    user: User = Depends(get_current_user),
    dealership: Dealership = Depends(get_current_dealership),
    db: Session = Depends(get_db),
):
    """
    Delete a lead permanently.
    
    - Hard delete for MVP
    - Also deletes associated conversations (cascade)
    - Returns 204 No Content on success
    - Returns 404 if lead not found
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.dealership_id == dealership.id
    ).first()
    
    if not lead:
        raise NotFoundException("Lead not found")
    
    db.delete(lead)
    db.commit()
    
    return None

