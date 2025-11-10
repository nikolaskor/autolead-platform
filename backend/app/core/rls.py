"""
Row-Level Security (RLS) helper functions for multi-tenant data isolation.

These functions set the PostgreSQL session variable that RLS policies use
to filter data by dealership_id.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def set_dealership_context(db: Session, dealership_id: UUID) -> None:
    """
    Set the current dealership context for Row-Level Security.
    
    This sets a PostgreSQL session variable that RLS policies use to filter
    queries by dealership_id. Must be called at the start of each request
    after authentication.
    
    Args:
        db: SQLAlchemy database session
        dealership_id: UUID of the dealership to set as context
        
    Example:
        @app.get("/api/leads")
        def get_leads(db: Session = Depends(get_db), dealership_id: UUID = Depends(get_dealership_id)):
            set_dealership_context(db, dealership_id)
            leads = db.query(Lead).all()  # RLS automatically filters by dealership_id
            return leads
    """
    try:
        db.execute(
            text("SET LOCAL app.current_dealership_id = :dealership_id"),
            {"dealership_id": str(dealership_id)}
        )
        logger.debug(f"Set dealership context to {dealership_id}")
    except Exception as e:
        logger.error(f"Failed to set dealership context: {e}")
        raise


def clear_dealership_context(db: Session) -> None:
    """
    Clear the current dealership context.
    
    Useful for cleanup or when you need to query across dealerships
    (admin operations only).
    
    Args:
        db: SQLAlchemy database session
    """
    try:
        db.execute(text("RESET app.current_dealership_id"))
        logger.debug("Cleared dealership context")
    except Exception as e:
        logger.error(f"Failed to clear dealership context: {e}")
        raise


def get_current_dealership_context(db: Session) -> str | None:
    """
    Get the current dealership context if set.
    
    Args:
        db: SQLAlchemy database session
        
    Returns:
        str: Current dealership_id or None if not set
    """
    try:
        result = db.execute(text("SELECT current_setting('app.current_dealership_id', true)"))
        value = result.scalar()
        return value if value else None
    except Exception as e:
        logger.error(f"Failed to get dealership context: {e}")
        return None

