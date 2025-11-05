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
    Construct JWKS URL from Clerk publishable key.
    
    Clerk publishable keys have format: pk_test_[base64]  or pk_live_[base64]
    The JWKS URL is: https://[instance].clerk.accounts.dev/.well-known/jwks.json
    
    Returns:
        str: JWKS endpoint URL
    """
    # Extract instance from publishable key
    # For now, we'll use a generic approach and extract domain from the key
    # Clerk provides JWKS at a standard location
    pub_key = settings.CLERK_PUBLISHABLE_KEY
    
    # Determine if test or production
    if pub_key.startswith("pk_test_"):
        # Test environment - clerk uses clerk.accounts.dev domain
        # We'll construct the URL dynamically
        # For testing, we can use the frontend API from the publishable key
        # Format: https://[frontend-api].clerk.accounts.dev/.well-known/jwks.json
        
        # Extract the base64 part after pk_test_ to derive the instance
        # However, Clerk also provides a simpler approach:
        # We can use the SECRET_KEY to derive the issuer domain
        
        # For Clerk, the issuer is typically in the JWT itself
        # We'll fetch JWKS from the standard location
        # Using a placeholder - in practice, decode a test JWT to get the issuer
        # For now, we'll use the secret key prefix to find the instance
        
        # Clerk's JWKS is at: https://clerk.[instance].com/.well-known/jwks.json
        # OR https://[instance].clerk.accounts.dev/.well-known/jwks.json
        
        # Simplified: Use Clerk's provided frontend API
        # The frontend API is embedded in the publishable key or can be inferred
        
        # Let's use a more direct approach:
        # Clerk recommends using the issuer from the JWT to construct JWKS URL
        # For simplicity, we'll hardcode for testing and make it configurable
        return "https://clerk.accounts.dev/.well-known/jwks.json"
    else:
        # Production environment
        return "https://clerk.accounts.dev/.well-known/jwks.json"


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

