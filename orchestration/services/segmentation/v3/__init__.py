"""
Contextual Bandits Module (V3.1)

Context-aware personalization using Thompson Sampling with user segmentation.

Copyright (c) 2024 Samplit Technologies
"""

__version__ = "3.1.0"

from .context_extractor import ContextExtractor
from .contextual_allocator import ContextualAllocator
from .adaptive_contextual import AdaptiveContextualAllocator
from .segment_analyzer import SegmentAnalyzer

__all__ = [
    'ContextExtractor',
    'ContextualAllocator',
    'AdaptiveContextualAllocator',
    'SegmentAnalyzer'
]

"""
Hierarchical Clustering Module (V3.2)

Multi-level segmentation with cascade allocation.

Copyright (c) 2024 Samplit Technologies
"""

__version__ = "3.2.0"

from .hierarchy_builder import HierarchyBuilder, SegmentNode
from .cascade_allocator import CascadeAllocator
from .tree_visualizer import TreeVisualizer

__all__ = [
    'HierarchyBuilder',
    'SegmentNode',
    'CascadeAllocator',
    'TreeVisualizer'
]


"""
Deep Learning Embeddings Module (V3.3)

Neural network-based user representations for semantic segmentation.

Copyright (c) 2024 Samplit Technologies
"""

__version__ = "3.3.0"

from .neural_encoder import NeuralEncoder, EmbeddingConfig
from .embedding_model import EmbeddingModel, EmbeddingTrainer
from .similarity_engine import SimilarityEngine
from .transfer_learning import TransferLearningManager

__all__ = [
    'NeuralEncoder',
    'EmbeddingConfig',
    'EmbeddingModel',
    'EmbeddingTrainer',
    'SimilarityEngine',
    'TransferLearningManager'
]


"""
Multi-region Support Module (V3.4)

Geo-distributed allocation with data residency compliance.

Copyright (c) 2024 Samplit Technologies
"""

__version__ = "3.4.0"

from .region_manager import RegionManager, Region
from .geo_allocator import GeoAllocator
from .sync_engine import SyncEngine
from .gdpr_compliance import GDPRCompliance

__all__ = [
    'RegionManager',
    'Region',
    'GeoAllocator',
    'SyncEngine',
    'GDPRCompliance'
]
