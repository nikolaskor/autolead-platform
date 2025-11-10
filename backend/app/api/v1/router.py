"""
Main router for API v1.
Combines all endpoint routers.
"""
from fastapi import APIRouter
from .endpoints import leads, conversations

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    leads.router,
    tags=["leads"]
)

api_router.include_router(
    conversations.router,
    tags=["conversations"]
)

