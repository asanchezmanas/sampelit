# engine/core/__init__.py
"""
Core Optimization Algorithms

This module provides the factory function for creating optimization allocators.
Implementation details are kept internal and may change without notice.
"""

from .allocators import BayesianAllocator, AdaptiveBayesianAllocator
from .allocators.sequential import SequentialAllocator


def _get_allocator(strategy_code: str, config: dict):
    """
    Factory function for creating optimization allocators
    
    This is an internal function used by OptimizerFactory.
    Do not call directly from application code.
    
    Args:
        strategy_code: Strategy identifier:
            - 'adaptive': Adaptive Bayesian (Adaptive Bayesian Inference)
            - 'standard': Standard Bayesian
            - 'fast_learning': Low-traffic optimized
            - 'sequential': Multi-step optimization
            - 'hybrid': Auto-select best method
        config: Configuration dict with algorithm parameters
            
    Returns:
        Allocator instance implementing IOptimizer interface
        
    Raises:
        ValueError: If strategy_code is unknown
        
    Example:
        >>> allocator = _get_allocator('adaptive', {'alpha_prior': 1.0})
        >>> variants = [...]
        >>> selected_idx = allocator.select_variant(variants)
        
    Note:
        This function is used by OptimizerFactory and should not be called
        directly. Use OptimizerFactory.create() instead.
    """
    
    # Strategy mapping
    strategy_map = {
        'adaptive': AdaptiveBayesianAllocator,
        'standard': BayesianAllocator,
        'fast_learning': AdaptiveBayesianAllocator,  # With high exploration
        'sequential': SequentialAllocator,
        'hybrid': AdaptiveBayesianAllocator,
    }
    
    # Get allocator class
    allocator_class = strategy_map.get(strategy_code)
    
    if allocator_class is None:
        raise ValueError(
            f"Unknown strategy: {strategy_code}. "
            f"Available strategies: {list(strategy_map.keys())}"
        )
    
    # Adjust config for fast_learning
    if strategy_code == 'fast_learning':
        config = {
            **config,
            'exploration_bonus': config.get('exploration_bonus', 0.5),
            'min_samples': config.get('min_samples', 50),  # Lower threshold
        }
    
    # Create and return allocator
    return allocator_class(config)


__all__ = [
    'BayesianAllocator',
    'AdaptiveBayesianAllocator',
    'SequentialAllocator',
    '_get_allocator'
]
