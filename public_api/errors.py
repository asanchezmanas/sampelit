# public-api/errors.py
"""
Centralized Error Codes for Samplit Platform.

Each error code follows the format: MODULE_CATEGORY_NUMBER
Examples:
- AUTH_LOGIN_001: Login error #1 in auth module
- EXP_CREATE_001: Experiment creation error #1
- DB_CONN_001: Database connection error #1

This makes debugging much easier by immediately identifying where errors occur.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """
    Centralized error codes for the entire application.
    
    Format: MODULE_CATEGORY_NUMBER
    - Module: AUTH, EXP, TRACK, ANAL, DB, API
    - Category: Action/Feature (LOGIN, CREATE, QUERY, etc.)
    - Number: Sequential error number
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # AUTH MODULE (Authentication & Authorization)
    # ═══════════════════════════════════════════════════════════════════
    
    # Login errors
    AUTH_LOGIN_001 = "AUTH_LOGIN_001"      # Invalid credentials
    AUTH_LOGIN_002 = "AUTH_LOGIN_002"      # Account locked
    AUTH_LOGIN_003 = "AUTH_LOGIN_003"      # Email not verified
    
    # Registration errors  
    AUTH_REG_001 = "AUTH_REG_001"          # Email already exists
    AUTH_REG_002 = "AUTH_REG_002"          # Invalid email format
    AUTH_REG_003 = "AUTH_REG_003"          # Weak password
    
    # Token errors
    AUTH_TOKEN_001 = "AUTH_TOKEN_001"      # Token expired
    AUTH_TOKEN_002 = "AUTH_TOKEN_002"      # Token invalid
    AUTH_TOKEN_003 = "AUTH_TOKEN_003"      # Token missing
    
    # Permission errors
    AUTH_PERM_001 = "AUTH_PERM_001"        # Insufficient permissions
    AUTH_PERM_002 = "AUTH_PERM_002"        # Admin required
    
    # ═══════════════════════════════════════════════════════════════════
    # EXPERIMENT MODULE (Experiment Management)
    # ═══════════════════════════════════════════════════════════════════
    
    # Create errors
    EXP_CREATE_001 = "EXP_CREATE_001"      # Invalid experiment name
    EXP_CREATE_002 = "EXP_CREATE_002"      # Invalid URL format
    EXP_CREATE_003 = "EXP_CREATE_003"      # No elements provided
    EXP_CREATE_004 = "EXP_CREATE_004"      # No variants in element
    EXP_CREATE_005 = "EXP_CREATE_005"      # Invalid selector
    
    # Read errors
    EXP_READ_001 = "EXP_READ_001"          # Experiment not found
    EXP_READ_002 = "EXP_READ_002"          # Not authorized to view
    
    # Update errors
    EXP_UPDATE_001 = "EXP_UPDATE_001"      # Cannot update active experiment
    EXP_UPDATE_002 = "EXP_UPDATE_002"      # Invalid status transition
    
    # Delete errors
    EXP_DELETE_001 = "EXP_DELETE_001"      # Cannot delete active experiment
    
    # ═══════════════════════════════════════════════════════════════════
    # TRACKER MODULE (SDK/Visitor Tracking)
    # ═══════════════════════════════════════════════════════════════════
    
    # Assignment errors
    TRACK_ASSIGN_001 = "TRACK_ASSIGN_001"  # Invalid installation token
    TRACK_ASSIGN_002 = "TRACK_ASSIGN_002"  # Experiment not active
    TRACK_ASSIGN_003 = "TRACK_ASSIGN_003"  # User identifier missing
    
    # Conversion errors
    TRACK_CONV_001 = "TRACK_CONV_001"      # Assignment not found
    TRACK_CONV_002 = "TRACK_CONV_002"      # Already converted
    TRACK_CONV_003 = "TRACK_CONV_003"      # Invalid conversion value
    
    # ═══════════════════════════════════════════════════════════════════
    # ANALYTICS MODULE
    # ═══════════════════════════════════════════════════════════════════
    
    ANAL_CALC_001 = "ANAL_CALC_001"        # Insufficient data for stats
    ANAL_CALC_002 = "ANAL_CALC_002"        # Invalid date range
    ANAL_EXPORT_001 = "ANAL_EXPORT_001"    # Export failed
    
    # ═══════════════════════════════════════════════════════════════════
    # DATABASE MODULE
    # ═══════════════════════════════════════════════════════════════════
    
    DB_CONN_001 = "DB_CONN_001"            # Connection failed
    DB_CONN_002 = "DB_CONN_002"            # Connection pool exhausted
    DB_QUERY_001 = "DB_QUERY_001"          # Query failed
    DB_QUERY_002 = "DB_QUERY_002"          # Constraint violation
    DB_TRANS_001 = "DB_TRANS_001"          # Transaction rollback
    
    # ═══════════════════════════════════════════════════════════════════
    # API MODULE (General)
    # ═══════════════════════════════════════════════════════════════════
    
    API_VAL_001 = "API_VAL_001"            # Request validation failed
    API_VAL_002 = "API_VAL_002"            # Missing required field
    API_RATE_001 = "API_RATE_001"          # Rate limit exceeded
    API_INT_001 = "API_INT_001"            # Internal server error


# Error code descriptions for documentation and user-facing messages
ERROR_DESCRIPTIONS: Dict[str, str] = {
    # Auth
    ErrorCode.AUTH_LOGIN_001: "Invalid email or password",
    ErrorCode.AUTH_LOGIN_002: "Account is temporarily locked due to too many failed attempts",
    ErrorCode.AUTH_LOGIN_003: "Please verify your email before logging in",
    ErrorCode.AUTH_REG_001: "An account with this email already exists",
    ErrorCode.AUTH_REG_002: "Please provide a valid email address",
    ErrorCode.AUTH_REG_003: "Password must be at least 8 characters with mixed case and numbers",
    ErrorCode.AUTH_TOKEN_001: "Your session has expired, please login again",
    ErrorCode.AUTH_TOKEN_002: "Invalid authentication token",
    ErrorCode.AUTH_TOKEN_003: "Authentication required",
    ErrorCode.AUTH_PERM_001: "You don't have permission to perform this action",
    ErrorCode.AUTH_PERM_002: "Administrator access required",
    
    # Experiments
    ErrorCode.EXP_CREATE_001: "Experiment name must be 3-255 characters",
    ErrorCode.EXP_CREATE_002: "URL must start with http:// or https://",
    ErrorCode.EXP_CREATE_003: "At least one element is required",
    ErrorCode.EXP_CREATE_004: "Each element needs at least one variant",
    ErrorCode.EXP_CREATE_005: "Invalid CSS/XPath selector",
    ErrorCode.EXP_READ_001: "Experiment not found",
    ErrorCode.EXP_READ_002: "You don't have access to this experiment",
    ErrorCode.EXP_UPDATE_001: "Cannot modify an active experiment",
    ErrorCode.EXP_UPDATE_002: "Invalid status transition",
    ErrorCode.EXP_DELETE_001: "Stop the experiment before deleting",
    
    # Tracker
    ErrorCode.TRACK_ASSIGN_001: "Invalid or missing installation token",
    ErrorCode.TRACK_ASSIGN_002: "This experiment is not currently active",
    ErrorCode.TRACK_ASSIGN_003: "User identifier is required",
    ErrorCode.TRACK_CONV_001: "No assignment found for this user",
    ErrorCode.TRACK_CONV_002: "Conversion already recorded",
    ErrorCode.TRACK_CONV_003: "Conversion value must be positive",
    
    # Analytics
    ErrorCode.ANAL_CALC_001: "Not enough data for statistical analysis",
    ErrorCode.ANAL_CALC_002: "Invalid date range",
    ErrorCode.ANAL_EXPORT_001: "Failed to export data",
    
    # Database
    ErrorCode.DB_CONN_001: "Database connection failed",
    ErrorCode.DB_CONN_002: "Database connection pool exhausted",
    ErrorCode.DB_QUERY_001: "Database query failed",
    ErrorCode.DB_QUERY_002: "Data constraint violation",
    ErrorCode.DB_TRANS_001: "Transaction failed and was rolled back",
    
    # API
    ErrorCode.API_VAL_001: "Request validation failed",
    ErrorCode.API_VAL_002: "Missing required field",
    ErrorCode.API_RATE_001: "Too many requests, please slow down",
    ErrorCode.API_INT_001: "An unexpected error occurred",
}


def get_error_description(code: ErrorCode) -> str:
    """Get user-friendly description for an error code."""
    return ERROR_DESCRIPTIONS.get(code, "An error occurred")


def get_error_module(code: str) -> str:
    """Extract module name from error code."""
    parts = code.split("_")
    if len(parts) >= 1:
        module_map = {
            "AUTH": "authentication",
            "EXP": "experiments",
            "TRACK": "tracker",
            "ANAL": "analytics",
            "DB": "database",
            "API": "api"
        }
        return module_map.get(parts[0], "unknown")
    return "unknown"
