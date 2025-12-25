# public-api/middleware/error_handler.py
"""
Unified error handling for FastAPI.

Uses FastAPI's exception handler system (not Starlette middleware) for proper error handling.
This ensures all exceptions are caught correctly regardless of where they occur.

Features:
- Consistent JSON error response format
- Request ID for tracing (correlates logs with responses)
- File/line location for debugging (in non-production)
- Structured logging with full context
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import logging
import traceback
import uuid
import sys
import os

# Re-export ErrorCodes for backwards compatibility
from public_api.models import ErrorCodes

logger = logging.getLogger(__name__)

# Check if we're in development mode for detailed error info
IS_DEVELOPMENT = os.getenv("ENVIRONMENT", "development").lower() in ("development", "dev", "local", "test")


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


def generate_request_id() -> str:
    """Generate a unique request ID for tracing."""
    return f"req_{uuid.uuid4().hex[:12]}"


def extract_error_location(exc: Exception) -> Optional[Dict[str, Any]]:
    """
    Extract file, line, and function where the error occurred.
    Returns None if extraction fails or in production mode.
    """
    if not IS_DEVELOPMENT:
        return None
    
    try:
        tb = traceback.extract_tb(exc.__traceback__)
        if tb:
            # Get the last frame (where error occurred)
            last_frame = tb[-1]
            return {
                "file": os.path.basename(last_frame.filename),
                "line": last_frame.lineno,
                "function": last_frame.name,
                "context": last_frame.line or ""
            }
    except Exception:
        pass
    return None


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
    request: Optional[Request] = None,
    details: Optional[Any] = None,
    error_id: Optional[str] = None,
    error_type: Optional[str] = None,
    location: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create consistent error response format with enhanced debugging info."""
    # Generate request ID if not provided
    if error_id is None:
        error_id = generate_request_id()
    
    content = {
        "success": False,
        "error": error,
        "code": code,
        "request_id": error_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add request context if available
    if request and IS_DEVELOPMENT:
        content["request"] = {
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None
        }
    
    if details is not None:
        content["details"] = _sanitize_for_json(details)
    if error_type is not None:
        content["type"] = error_type
    if location is not None and IS_DEVELOPMENT:
        content["location"] = location
    
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
        request_id = generate_request_id()
        logger.warning(f"[{request_id}] APIError: {exc.code} - {exc.message} | {request.method} {request.url.path}")
        return _create_error_response(
            status_code=exc.status,
            error=exc.message,
            code=exc.code,
            request=request,
            details=exc.details,
            error_id=request_id
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTPException."""
        request_id = generate_request_id()
        logger.info(f"[{request_id}] HTTPException: {exc.status_code} | {request.method} {request.url.path}")
        return _create_error_response(
            status_code=exc.status_code,
            error=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            code=f"HTTP_{exc.status_code}",
            request=request,
            error_id=request_id
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors from request parsing."""
        request_id = generate_request_id()
        # Sanitize errors for JSON serialization
        errors = []
        for err in exc.errors():
            errors.append({
                "loc": list(err.get("loc", [])),  # Convert tuple to list
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", ""))
            })
        logger.warning(f"[{request_id}] ValidationError: {len(errors)} error(s) | {request.method} {request.url.path}")
        return _create_error_response(
            status_code=422,
            error="Validation failed",
            code="VALIDATION_ERROR",
            request=request,
            details=errors,
            error_id=request_id
        )

    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        """Handle direct Pydantic ValidationError."""
        request_id = generate_request_id()
        # Sanitize errors for JSON serialization
        errors = []
        for err in exc.errors():
            errors.append({
                "loc": list(err.get("loc", [])),  # Convert tuple to list
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", ""))
            })
        logger.warning(f"[{request_id}] Pydantic ValidationError: {len(errors)} error(s) | {request.method} {request.url.path}")
        return _create_error_response(
            status_code=422,
            error="Validation failed",
            code="VALIDATION_ERROR",
            request=request,
            details=errors,
            error_id=request_id
        )


    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError (often from Pydantic field validators)."""
        request_id = generate_request_id()
        location = extract_error_location(exc)
        logger.warning(f"[{request_id}] ValueError: {exc} | {request.method} {request.url.path}")
        return _create_error_response(
            status_code=422,
            error=str(exc),
            code="VALIDATION_ERROR",
            request=request,
            error_id=request_id,
            location=location
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions."""
        request_id = generate_request_id()
        location = extract_error_location(exc)
        
        # Enhanced structured logging
        logger.error(
            f"[{request_id}] Unhandled {type(exc).__name__}: {str(exc)} | "
            f"{request.method} {request.url.path}\n{traceback.format_exc()}"
        )
        
        return _create_error_response(
            status_code=500,
            error=str(exc),
            code="INTERNAL_ERROR",
            request=request,
            error_id=request_id,
            error_type=type(exc).__name__,
            location=location
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
