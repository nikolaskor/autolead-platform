"""
Tests for Lead API endpoints.
"""
import pytest
from unittest.mock import patch
from uuid import uuid4


def test_create_lead(client, auth_headers, test_user, test_dealership):
    """Test creating a new lead."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        lead_data = {
            "customer_name": "New Customer",
            "customer_email": "newcustomer@test.com",
            "customer_phone": "+47 111 22 333",
            "vehicle_interest": "VW ID.4",
            "initial_message": "Interested in test drive",
            "source": "website"
        }
        
        response = client.post("/api/v1/leads", json=lead_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_email"] == lead_data["customer_email"]
        assert data["status"] == "new"
        assert data["dealership_id"] == str(test_dealership.id)


def test_list_leads(client, auth_headers, test_user, test_dealership, test_lead):
    """Test listing leads with pagination."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        response = client.get("/api/v1/leads", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1


def test_list_leads_with_filters(client, auth_headers, test_user, test_dealership, test_lead):
    """Test filtering leads by status and source."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        # Filter by status
        response = client.get(
            "/api/v1/leads?status=new",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "new" for item in data["items"])
        
        # Filter by source
        response = client.get(
            "/api/v1/leads?source=website",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["source"] == "website" for item in data["items"])


def test_get_lead_by_id(client, auth_headers, test_user, test_dealership, test_lead):
    """Test getting a single lead by ID."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        response = client.get(
            f"/api/v1/leads/{test_lead.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_lead.id)
        assert data["customer_email"] == test_lead.customer_email


def test_get_nonexistent_lead(client, auth_headers, test_user, test_dealership):
    """Test getting a lead that doesn't exist."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/leads/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


def test_update_lead(client, auth_headers, test_user, test_dealership, test_lead):
    """Test updating a lead."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        update_data = {
            "status": "contacted",
            "vehicle_interest": "Tesla Model Y"
        }
        
        response = client.patch(
            f"/api/v1/leads/{test_lead.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "contacted"
        assert data["vehicle_interest"] == "Tesla Model Y"


def test_delete_lead(client, auth_headers, test_user, test_dealership, test_lead):
    """Test deleting a lead."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        response = client.delete(
            f"/api/v1/leads/{test_lead.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify lead is deleted
        response = client.get(
            f"/api/v1/leads/{test_lead.id}",
            headers=auth_headers
        )
        assert response.status_code == 404


def test_multi_tenant_isolation(client, db_session, test_user, test_dealership):
    """Test that users can't access leads from other dealerships."""
    # Create another dealership and lead
    from app.models.dealership import Dealership
    from app.models.lead import Lead
    
    other_dealership = Dealership(
        id=uuid4(),
        name="Other Dealership",
        email="other@dealership.com",
        clerk_org_id="org_other123",
        subscription_status="active"
    )
    db_session.add(other_dealership)
    db_session.commit()
    
    other_lead = Lead(
        id=uuid4(),
        dealership_id=other_dealership.id,
        source="website",
        status="new",
        customer_email="other@customer.com",
        lead_score=50
    )
    db_session.add(other_lead)
    db_session.commit()
    
    # Try to access other dealership's lead
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        headers = {"Authorization": "Bearer test_token"}
        response = client.get(
            f"/api/v1/leads/{other_lead.id}",
            headers=headers
        )
        
        # Should get 404 (not found), not 403, because RLS filters it out
        assert response.status_code == 404


def test_search_leads(client, auth_headers, test_user, test_dealership, test_lead):
    """Test searching leads by name or email."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        # Search by name
        response = client.get(
            "/api/v1/leads?search=Test",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

