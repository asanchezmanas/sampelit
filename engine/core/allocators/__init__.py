# engine/core/allocators/__init__.py
"""
Optimization Allocators

Implementations of multi-armed bandit algorithms:
- Thompson Sampling (Bayesian)
- Adaptive Thompson Sampling
- Epsilon-Greedy (roadmap)
- UCB (Upper Confidence Bound) (roadmap)
- Contextual bandits (roadmap)

Current Status:
✅ BayesianAllocator - Production ready
✅ AdaptiveBayesianAllocator - Production ready
🚧 EpsilonGreedyAllocator - Roadmap v1.1
🚧 UCBAllocator - Roadmap v1.1
🚧 ContextualAllocator - Roadmap v2.0
"""

from .bayesian import BayesianAllocator, AdaptiveBayesianAllocator

__all__ = [
    'BayesianAllocator',
    'AdaptiveBayesianAllocator'
]
