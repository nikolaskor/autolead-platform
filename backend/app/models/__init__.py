"""
SQLAlchemy models for the Norvalt platform.

All models use UUID primary keys and include proper foreign key relationships.
Multi-tenant architecture enforced via dealership_id.
"""
from ..core.database import Base
from .dealership import Dealership
from .user import User
from .lead import Lead
from .conversation import Conversation
from .email import Email

__all__ = [
    "Base",
    "Dealership",
    "User",
    "Lead",
    "Conversation",
    "Email",
]

