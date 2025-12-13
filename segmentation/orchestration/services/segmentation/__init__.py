# orchestration/services/segmentation/__init__.py

"""
Segmentation Module

Provides multi-level segmentation capabilities:
- Context extraction (multi-channel)
- Eligibility detection (auto-activation)
- Manual segmentation (user-defined)
- Auto-clustering (K-means, DBSCAN)
"""

from .context_extractor import ContextExtractor, ChannelType
from .eligibility_service import EligibilityService
from .segmentation_service import SegmentationService
from .clustering_service import ClusteringService

__all__ = [
    'ContextExtractor',
    'ChannelType',
    'EligibilityService',
    'SegmentationService',
    'ClusteringService',
]
