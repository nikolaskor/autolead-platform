"""
Pytest configuration and fixtures for API tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.core.database import Base, get_db
from app.models.dealership import Dealership
from app.models.user import User
from app.models.lead import Lead
from main import app


# Test database setup (using SQLite in-memory for tests)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with overridden database dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_dealership(db_session):
    """Create a test dealership."""
    dealership = Dealership(
        id=uuid4(),
        name="Test Dealership",
        email="test@dealership.com",
        phone="+47 123 45 678",
        clerk_org_id="org_test123",
        subscription_status="active",
        subscription_tier="starter"
    )
    db_session.add(dealership)
    db_session.commit()
    db_session.refresh(dealership)
    return dealership


@pytest.fixture
def test_user(db_session, test_dealership):
    """Create a test user."""
    user = User(
        id=uuid4(),
        dealership_id=test_dealership.id,
        clerk_user_id="user_test123",
        email="test@user.com",
        name="Test User",
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_lead(db_session, test_dealership):
    """Create a test lead."""
    lead = Lead(
        id=uuid4(),
        dealership_id=test_dealership.id,
        source="website",
        status="new",
        customer_name="Test Customer",
        customer_email="customer@test.com",
        customer_phone="+47 987 65 432",
        vehicle_interest="Tesla Model 3",
        initial_message="Test message",
        lead_score=75
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


@pytest.fixture
def mock_clerk_jwt():
    """
    Mock Clerk JWT verification for testing.
    Returns a mock that simulates successful JWT verification.
    """
    def mock_verify(token: str):
        """Mock JWT verification that returns test claims."""
        return {
            "sub": "user_test123",  # Clerk user ID
            "org_id": "org_test123",  # Clerk org ID
            "email": "test@user.com"
        }
    
    return mock_verify


@pytest.fixture
def auth_headers(test_user, mock_clerk_jwt):
    """
    Create authentication headers for testing.
    Patches the JWT verification to use mock.
    """
    with patch('app.core.auth.verify_clerk_jwt', side_effect=mock_clerk_jwt):
        headers = {"Authorization": "Bearer test_token_123"}
        yield headers

