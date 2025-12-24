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
