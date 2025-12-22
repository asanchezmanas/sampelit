# public-api/models/__init__.py
"""
Centralized Pydantic models for the API.

Import models from here to keep routers clean.
"""

from .common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    HealthResponse
)

from .leads import (
    LeadCaptureRequest,
    LeadCaptureResponse,
    LeadStatus
)

from .experiment_models import (
    ExperimentStatus,
    ElementType,
    SelectorType,
    SelectorConfig,
    VariantContent,
    ElementConfig,
    CreateExperimentRequest,
    UpdateExperimentRequest,
    ExperimentListResponse,
    ExperimentDetailResponse,
    AssignmentRequest,
    AssignmentResponse,
    ConversionRequest,
    ConversionResponse
)

__all__ = [
    # Common
    'APIResponse',
    'ErrorResponse', 
    'PaginatedResponse',
    'HealthResponse',
    # Leads
    'LeadCaptureRequest',
    'LeadCaptureResponse',
    'LeadStatus',
    # Experiments
    'ExperimentStatus',
    'ElementType',
    'SelectorType',
    'SelectorConfig',
    'VariantContent',
    'ElementConfig',
    'CreateExperimentRequest',
    'UpdateExperimentRequest',
    'ExperimentListResponse',
    'ExperimentDetailResponse',
    'AssignmentRequest',
    'AssignmentResponse',
    'ConversionRequest',
    'ConversionResponse',
]
