"""
Common Pydantic schemas used across the API.
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response format."""
    
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    
    items: List[T]
    total: int
    page: int
    pages: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "pages": 10,
                "limit": 10
            }
        }

