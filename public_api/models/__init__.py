# public-api/models/__init__.py
"""
Centralized Pydantic models for the API.

Import models from here to keep routers clean.
"""

from .common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    HealthResponse,
    ErrorCodes
)

from .leads import (
    LeadCaptureRequest,
    LeadCaptureResponse,
    LeadStatus
)

from .tracker import (
    TrackerAssignmentRequest,
    TrackerAssignmentResponse,
    TrackerConversionRequest,
    TrackerConversionResponse,
    ExperimentInfo,
    ActiveExperimentsRequest,
    ActiveExperimentsResponse,
    GenericEventRequest
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
    ConversionResponse,
    ExperimentAnalytics,
    BayesianInsights
)

__all__ = [
    # Common
    'APIResponse',
    'ErrorResponse', 
    'PaginatedResponse',
    'HealthResponse',
    'ErrorCodes',
    # Leads
    'LeadCaptureRequest',
    'LeadCaptureResponse',
    'LeadStatus',
    # Tracker
    'TrackerAssignmentRequest',
    'TrackerAssignmentResponse',
    'TrackerConversionRequest',
    'TrackerConversionResponse',
    'ExperimentInfo',
    'ActiveExperimentsRequest',
    'ActiveExperimentsResponse',
    'GenericEventRequest',
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
    'ExperimentAnalytics',
    'BayesianInsights',
]
