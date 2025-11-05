"""
FastAPI dependencies for authentication and authorization.
"""
from fastapi import Depends, Header
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..core.auth import verify_clerk_jwt, get_user_from_clerk_id, get_dealership_from_org
from ..core.exceptions import UnauthorizedException, ForbiddenException
from ..core.rls import set_dealership_context
from ..models.user import User
from ..models.dealership import Dealership


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Extracts JWT from Authorization header, verifies it with Clerk,
    and loads the user from the database.
    
    Args:
        authorization: Authorization header (Bearer token)
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        UnauthorizedException: If token is missing or invalid
    """
    if not authorization:
        raise UnauthorizedException("Missing authorization header")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedException("Invalid authorization header format")
    
    token = parts[1]
    
    # Verify JWT with Clerk
    claims = verify_clerk_jwt(token)
    
    # Extract user ID from claims
    # Clerk puts user ID in 'sub' claim
    clerk_user_id = claims.get("sub")
    if not clerk_user_id:
        raise UnauthorizedException("Invalid token: missing user ID")
    
    # Load user from database
    user = get_user_from_clerk_id(clerk_user_id, db)
    if not user:
        raise UnauthorizedException("User not found")
    
    # Set RLS context for this user's dealership
    if user.dealership_id:
        set_dealership_context(db, user.dealership_id)
    
    return user


def get_current_dealership(
    user: User = Depends(get_current_user)
) -> Dealership:
    """
    FastAPI dependency to get the current user's dealership.
    
    Args:
        user: Current authenticated user
        
    Returns:
        Dealership: User's dealership
        
    Raises:
        ForbiddenException: If user has no dealership
    """
    if not user.dealership:
        raise ForbiddenException("User not associated with a dealership")
    
    return user.dealership


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @app.get("/admin")
        def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    
    Args:
        allowed_roles: Roles that are allowed to access the endpoint
        
    Returns:
        Dependency function
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise ForbiddenException(
                f"This endpoint requires one of these roles: {', '.join(allowed_roles)}"
            )
        return user
    
    return role_checker

