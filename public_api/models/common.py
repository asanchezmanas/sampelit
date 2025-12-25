# public-api/models/common.py
"""
Common response models used across all endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timezone

T = TypeVar('T')


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed",
                "data": {"id": "abc123"}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Resource not found",
                "code": "NOT_FOUND",
                "details": {"resource": "experiment", "id": "abc123"},
                "timestamp": "2025-01-01T00:00:00Z"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response"""
    items: List[T]
    total: int
    page: int = 1
    per_page: int = 20
    has_more: bool = False
    
    @property
    def pages(self) -> int:
        return (self.total + self.per_page - 1) // self.per_page if self.per_page > 0 else 0


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    database: bool = True
    cache: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "database": True,
                "cache": True,
                "timestamp": "2025-01-01T00:00:00Z"
            }
        }

class ErrorCodes:
    """Standard error codes for consistent error handling"""
    
    # Auth errors (401/403)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    
    # Resource errors (404)
    NOT_FOUND = "NOT_FOUND"
    EXPERIMENT_NOT_FOUND = "EXPERIMENT_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # Rate limit (429)
    RATE_LIMITED = "RATE_LIMITED"
    
    # Payment (402)
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    PLAN_LIMIT_REACHED = "PLAN_LIMIT_REACHED"
    
    # Server errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
