"""
Clerk JWT authentication module.
Handles JWT verification using Clerk's JWKS endpoint.
"""
import httpx
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Dict, Optional
from functools import lru_cache
import logging

from .config import settings
from .exceptions import UnauthorizedException, ForbiddenException
from ..models.dealership import Dealership
from ..models.user import User

logger = logging.getLogger(__name__)


def get_jwks_url() -> str:
    """
    Get JWKS URL from environment configuration.
    
    The JWKS URL is specific to each Clerk instance and should be configured
    in the CLERK_JWKS_URL environment variable. You can find this URL in your
    Clerk dashboard under API Keys.
    
    Returns:
        str: JWKS endpoint URL
        
    Raises:
        UnauthorizedException: If JWKS URL is not configured
    """
    if settings.CLERK_JWKS_URL:
        return settings.CLERK_JWKS_URL
    
    # Fallback error message
    raise UnauthorizedException(
        "CLERK_JWKS_URL must be configured in environment variables. "
        "Find it in your Clerk dashboard under API Keys > JWKS URL."
    )


@lru_cache(maxsize=1)
def fetch_jwks() -> Dict:
    """
    Fetch JWKS (JSON Web Key Set) from Clerk.
    Cached to avoid repeated requests.
    
    Returns:
        Dict: JWKS data containing public keys
        
    Raises:
        UnauthorizedException: If JWKS cannot be fetched
    """
    try:
        jwks_url = get_jwks_url()
        response = httpx.get(jwks_url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch JWKS from Clerk: {e}")
        raise UnauthorizedException("Unable to verify authentication")


def verify_clerk_jwt(token: str) -> Dict:
    """
    Verify a Clerk JWT token and extract claims.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict: Decoded JWT claims containing user and org information
        
    Raises:
        UnauthorizedException: If token is invalid or verification fails
    """
    try:
        # Fetch JWKS
        jwks = fetch_jwks()
        
        # Decode the token header to get the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise UnauthorizedException("Invalid token: missing key ID")
        
        # Find the matching key in JWKS
        key = None
        for jwk_key in jwks.get("keys", []):
            if jwk_key.get("kid") == kid:
                key = jwk_key
                break
        
        if not key:
            raise UnauthorizedException("Invalid token: key not found")
        
        # Verify and decode the JWT
        # Note: Clerk uses RS256 algorithm
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # Clerk doesn't always set audience
            }
        )
        
        return claims
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise UnauthorizedException(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}")
        raise UnauthorizedException("Authentication failed")


def get_dealership_from_org(clerk_org_id: str, db: Session) -> Optional[Dealership]:
    """
    Get dealership from Clerk organization ID.
    
    Args:
        clerk_org_id: Clerk organization ID
        db: Database session
        
    Returns:
        Dealership object or None if not found
    """
    return db.query(Dealership).filter(
        Dealership.clerk_org_id == clerk_org_id
    ).first()


def get_user_from_clerk_id(clerk_user_id: str, db: Session) -> Optional[User]:
    """
    Get user from Clerk user ID.
    
    Args:
        clerk_user_id: Clerk user ID
        db: Database session
        
    Returns:
        User object or None if not found
    """
    return db.query(User).filter(
        User.clerk_user_id == clerk_user_id
    ).first()

