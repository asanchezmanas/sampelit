# engine/__init__.py
"""
Samplit Optimization Engine

Core algorithms for A/B testing optimization.

This module contains proprietary algorithms for:
- Thompson Sampling (Bayesian optimization)
- Multi-armed bandit algorithms
- Contextual optimization

VERSION: 1.0.0
LICENSE: Proprietary
"""

from .core import BayesianAllocator

__version__ = '1.0.0'
__author__ = 'Samplit Technologies'
__all__ = ['BayesianAllocator']
