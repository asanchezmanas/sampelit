# public-api/middleware/error_handler.py
"""
Unified error handling for FastAPI.

Uses FastAPI's exception handler system (not Starlette middleware) for proper error handling.
This ensures all exceptions are caught correctly regardless of where they occur.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
import traceback

# Re-export ErrorCodes for backwards compatibility
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


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize object for JSON serialization."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    elif isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    else:
        # Convert anything else to string
        return str(obj)


def _create_error_response(
    status_code: int,
    error: str,
    code: str,
    details: Optional[Any] = None,
    error_id: Optional[str] = None,
    error_type: Optional[str] = None
) -> JSONResponse:
    """Create consistent error response format."""
    content = {
        "success": False,
        "error": error,
        "code": code,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if details is not None:
        content["details"] = _sanitize_for_json(details)
    if error_id is not None:
        content["error_id"] = error_id
    if error_type is not None:
        content["type"] = error_type
    
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers on the FastAPI app.
    
    This is the proper way to handle exceptions in FastAPI.
    Call this function after creating the app instance.
    """
    
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """Handle our custom APIError exceptions."""
        logger.warning(f"APIError: {exc.code} - {exc.message}")
        return _create_error_response(
            status_code=exc.status,
            error=exc.message,
            code=exc.code,
            details=exc.details
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTPException."""
        return _create_error_response(
            status_code=exc.status_code,
            error=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            code=f"HTTP_{exc.status_code}"
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors from request parsing."""
        # Sanitize errors for JSON serialization
        errors = []
        for err in exc.errors():
            errors.append({
                "loc": list(err.get("loc", [])),  # Convert tuple to list
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", ""))
            })
        return _create_error_response(
            status_code=422,
            error="Validation failed",
            code="VALIDATION_ERROR",
            details=errors
        )

    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        """Handle direct Pydantic ValidationError."""
        # Sanitize errors for JSON serialization
        errors = []
        for err in exc.errors():
            errors.append({
                "loc": list(err.get("loc", [])),  # Convert tuple to list
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", ""))
            })
        return _create_error_response(
            status_code=422,
            error="Validation failed",
            code="VALIDATION_ERROR",
            details=errors
        )


    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError (often from Pydantic field validators)."""
        return _create_error_response(
            status_code=422,
            error=str(exc),
            code="VALIDATION_ERROR"
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions."""
        now = datetime.now(timezone.utc)
        error_id = f"err_{now.strftime('%Y%m%d%H%M%S')}"
        
        logger.error(
            f"Unhandled error [{error_id}]: {str(exc)}\n{traceback.format_exc()}"
        )
        
        return _create_error_response(
            status_code=500,
            error=str(exc),
            code="INTERNAL_ERROR",
            error_id=error_id,
            error_type=type(exc).__name__
        )


# Legacy support - keep ErrorHandlerMiddleware for backwards compatibility
# but it's no longer needed if using register_exception_handlers
from starlette.middleware.base import BaseHTTPMiddleware

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    DEPRECATED: Use register_exception_handlers() instead.
    
    This middleware is kept for backwards compatibility but FastAPI's
    exception handlers are the proper pattern and handle all cases correctly.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # This middleware rarely catches exceptions because
            # FastAPI's exception handlers run first
            logger.error(f"Middleware caught: {e}")
            return _create_error_response(
                status_code=500,
                error=str(e),
                code="INTERNAL_ERROR",
                error_type=type(e).__name__
            )


def error_handler_middleware(app):
    """DEPRECATED: Use register_exception_handlers() instead."""
    return ErrorHandlerMiddleware(app)
