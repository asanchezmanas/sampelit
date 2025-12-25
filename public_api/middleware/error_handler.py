# public-api/middleware/error_handler.py
"""
Unified error handling middleware.

Catches all exceptions and returns consistent JSON responses.
Logs errors to monitoring service.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
import traceback
from public_api.models import ErrorCodes

logger = logging.getLogger(__name__)


class APIError(Exception):
    """
    Custom API error for consistent error handling.
    
    Usage:
        raise APIError("User not found", code="USER_NOT_FOUND", status=404)
    """
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR",
        status: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status = status
        self.details = details
        super().__init__(message)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches all exceptions and returns consistent JSON.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except APIError as e:
            # Our custom errors
            logger.warning(f"APIError: {e.code} - {e.message}")
            return JSONResponse(
                status_code=e.status,
                content={
                    "success": False,
                    "error": e.message,
                    "code": e.code,
                    "details": e.details,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except HTTPException as e:
            # FastAPI HTTP exceptions
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": e.detail if isinstance(e.detail, str) else str(e.detail),
                    "code": f"HTTP_{e.status_code}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        except ValueError as e:
            # Pydantic validation errors come wrapped as ValueError
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": str(e),
                    "code": "VALIDATION_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:

            # Unexpected errors
            now = datetime.now(timezone.utc)
            error_id = f"err_{now.strftime('%Y%m%d%H%M%S')}"
            
            logger.error(
                f"Unhandled error [{error_id}]: {str(e)}\n{traceback.format_exc()}"
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": str(e),
                    "code": "INTERNAL_ERROR",
                    "error_id": error_id,
                    "type": type(e).__name__,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )


def error_handler_middleware(app):
    """Add error handler middleware to app"""
    return ErrorHandlerMiddleware(app)


