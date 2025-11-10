"""
Model tests.

Tests SQLAlchemy model creation, validation, and relationships.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models import Dealership, User, Lead, Conversation
from app.core.database import SessionLocal


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Don't commit test data
        db.close()


def test_dealership_creation(db_session):
    """Test creating a dealership model."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@example.no",
        phone="+47 12345678",
        clerk_org_id="org_test_001",
        subscription_status="active",
        subscription_tier="starter",
    )
    
    db_session.add(dealership)
    db_session.flush()
    
    assert dealership.id is not None
    assert dealership.name == "Test Dealership"
    assert dealership.created_at is not None


def test_user_creation(db_session):
    """Test creating a user model."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@example.no",
        clerk_org_id="org_test_002",
    )
    db_session.add(dealership)
    db_session.flush()
    
    user = User(
        id=uuid4(),
        dealership_id=dealership.id,
        clerk_user_id="user_test_001",
        email="user@example.no",
        name="Test User",
        role="sales_rep",
    )
    
    db_session.add(user)
    db_session.flush()
    
    assert user.id is not None
    assert user.dealership_id == dealership.id
    assert user.role == "sales_rep"


def test_lead_creation(db_session):
    """Test creating a lead model."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@example.no",
        clerk_org_id="org_test_003",
    )
    db_session.add(dealership)
    db_session.flush()
    
    lead = Lead(
        id=uuid4(),
        dealership_id=dealership.id,
        source="website",
        customer_name="Test Customer",
        customer_email="customer@example.no",
        customer_phone="+47 987654321",
        vehicle_interest="Tesla Model 3",
        initial_message="Test message",
        status="new",
        lead_score=75,
    )
    
    db_session.add(lead)
    db_session.flush()
    
    assert lead.id is not None
    assert lead.dealership_id == dealership.id
    assert lead.status == "new"
    assert lead.lead_score == 75


def test_lead_email_validation(db_session):
    """Test lead email validation constraint."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@example.no",
        clerk_org_id="org_test_004",
    )
    db_session.add(dealership)
    db_session.flush()
    
    # Valid email should work
    lead = Lead(
        id=uuid4(),
        dealership_id=dealership.id,
        source="website",
        customer_email="valid@example.no",
        status="new",
    )
    db_session.add(lead)
    db_session.flush()
    assert lead.customer_email == "valid@example.no"


def test_lead_relationship(db_session):
    """Test Lead -> Dealership relationship."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@example.no",
        clerk_org_id="org_test_005",
    )
    db_session.add(dealership)
    db_session.flush()
    
    lead = Lead(
        id=uuid4(),
        dealership_id=dealership.id,
        source="website",
        status="new",
    )
    db_session.add(lead)
    db_session.flush()
    
    # Test relationship
    assert lead.dealership.id == dealership.id
    assert lead.dealership.name == "Test Dealership"


def test_conversation_creation(db_session):
    """Test creating a conversation model."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@example.no",
        clerk_org_id="org_test_006",
    )
    db_session.add(dealership)
    db_session.flush()
    
    lead = Lead(
        id=uuid4(),
        dealership_id=dealership.id,
        source="website",
        status="new",
    )
    db_session.add(lead)
    db_session.flush()
    
    conversation = Conversation(
        id=uuid4(),
        lead_id=lead.id,
        dealership_id=dealership.id,
        channel="email",
        direction="inbound",
        sender="Customer",
        sender_type="customer",
        message_content="Test message",
    )
    
    db_session.add(conversation)
    db_session.flush()
    
    assert conversation.id is not None
    assert conversation.lead_id == lead.id
    assert conversation.channel == "email"


def test_jsonb_fields(db_session):
    """Test JSONB fields work correctly."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@example.no",
        clerk_org_id="org_test_007",
    )
    db_session.add(dealership)
    db_session.flush()
    
    user = User(
        id=uuid4(),
        dealership_id=dealership.id,
        clerk_user_id="user_test_002",
        email="user@example.no",
        notification_preferences={"sms": False, "email": True, "push": True},
    )
    db_session.add(user)
    db_session.flush()
    
    assert user.notification_preferences["sms"] is False
    assert user.notification_preferences["email"] is True
    assert user.notification_preferences["push"] is True

