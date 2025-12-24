# engine/core/__init__.py
"""
Core Optimization Algorithms - Extensible Factory

CHANGELOG:
- 2024-12: Refactored to registry pattern for easy extension
"""

from typing import Dict, Any, Type
from .allocators import (
    BayesianAllocator,
    AdaptiveBayesianAllocator,
    SequentialAllocator,
    EpsilonGreedyAllocator,
)

# ============================================
# ALLOCATOR REGISTRY
# ============================================
# Add new allocators here - zero coupling!

ALLOCATOR_REGISTRY: Dict[str, Type] = {
    # Production-ready
    'adaptive': AdaptiveBayesianAllocator,
    'thompson': BayesianAllocator,
    'sequential': SequentialAllocator,
    'epsilon_greedy': EpsilonGreedyAllocator,
    
    # Legacy aliases
    'standard': BayesianAllocator,
    'fast_learning': AdaptiveBayesianAllocator,
    'hybrid': AdaptiveBayesianAllocator,
}


def _get_allocator(strategy_code: str, config: dict):
    """
    Factory function for creating optimization allocators
    
    Args:
        strategy_code: Strategy identifier
        config: Configuration dict
        
    Returns:
        Allocator instance
        
    Raises:
        ValueError: If strategy_code is unknown
        
    Example:
        >>> allocator = _get_allocator('adaptive', {'alpha_prior': 1.0})
        >>> selected = allocator.select_variant(variants)
    """
    
    allocator_class = ALLOCATOR_REGISTRY.get(strategy_code)
    
    if allocator_class is None:
        available = ', '.join(ALLOCATOR_REGISTRY.keys())
        raise ValueError(
            f"Unknown strategy: '{strategy_code}'. "
            f"Available: {available}"
        )
    
    # Special config adjustments
    if strategy_code == 'fast_learning':
        config = {
            **config,
            'exploration_bonus': config.get('exploration_bonus', 0.5),
            'min_samples': config.get('min_samples', 50),
        }
    
    return allocator_class(config)


def register_allocator(name: str, allocator_class: Type):
    """
    Register a new allocator (for plugins/extensions)
    
    Example:
        >>> from my_allocators import CustomAllocator
        >>> register_allocator('custom', CustomAllocator)
        >>> allocator = _get_allocator('custom', {})
    """
    ALLOCATOR_REGISTRY[name] = allocator_class


def list_allocators() -> list[str]:
    """List all available allocator strategies"""
    return list(ALLOCATOR_REGISTRY.keys())


__all__ = [
    'BayesianAllocator',
    'AdaptiveBayesianAllocator',
    'SequentialAllocator',
    '_get_allocator',
    'register_allocator',
    'list_allocators',
]
