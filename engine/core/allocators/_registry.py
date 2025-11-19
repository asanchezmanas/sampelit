# engine/core/allocators/_registry.py

"""
Internal allocator registry

This module maps strategy codes to actual implementations
without exposing algorithm names.
"""

from typing import Dict, Any, Callable
from .._base import BaseAllocator

# Internal mapping (nunca en logs)
_STRATEGY_MAP = {
    "adaptive": "allocators._bayesian",
    "fast_learning": "allocators._explore", 
    "sequential": "allocators._sequential",
    "hybrid": "allocators._hybrid"
}

def get_allocator(strategy_code: str, config: Dict[str, Any]) -> BaseAllocator:
    """
    Internal factory - returns allocator instance
    
    This is intentionally opaque. No external code should know
    which specific algorithm is being used.
    """
    
    if strategy_code not in _STRATEGY_MAP:
        strategy_code = "adaptive"  # Default seguro
    
    module_path = _STRATEGY_MAP[strategy_code]
    
    # Dynamic import (ofusca en stack traces)
    module = __import__(
        f"engine.core.{module_path}", 
        fromlist=['create']
    )
    
    return module.create(config)
