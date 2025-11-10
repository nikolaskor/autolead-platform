"""
Tests for authentication and authorization.
"""
import pytest
from unittest.mock import patch
from app.core.exceptions import UnauthorizedException


def test_health_check_no_auth(client):
    """Test that health check endpoint doesn't require authentication."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint_no_auth(client):
    """Test that root endpoint doesn't require authentication."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Norvalt API" in response.json()["message"]


def test_list_leads_without_auth(client):
    """Test that leads endpoint requires authentication."""
    response = client.get("/api/v1/leads")
    assert response.status_code == 401


def test_list_leads_with_invalid_token(client):
    """Test that invalid JWT token is rejected."""
    with patch('app.core.auth.verify_clerk_jwt', side_effect=UnauthorizedException("Invalid token")):
        response = client.get(
            "/api/v1/leads",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


def test_list_leads_with_valid_auth(client, auth_headers, test_user, test_dealership):
    """Test that valid authentication allows access to leads."""
    with patch('app.core.auth.verify_clerk_jwt') as mock_verify:
        mock_verify.return_value = {
            "sub": test_user.clerk_user_id,
            "org_id": test_dealership.clerk_org_id
        }
        
        response = client.get("/api/v1/leads", headers=auth_headers)
        assert response.status_code == 200
        assert "items" in response.json()


def test_missing_authorization_header(client):
    """Test that missing authorization header returns 401."""
    response = client.get("/api/v1/leads")
    assert response.status_code == 401
    assert "authorization" in response.json()["detail"].lower()


def test_malformed_authorization_header(client):
    """Test that malformed authorization header returns 401."""
    response = client.get(
        "/api/v1/leads",
        headers={"Authorization": "InvalidFormat"}
    )
    assert response.status_code == 401

