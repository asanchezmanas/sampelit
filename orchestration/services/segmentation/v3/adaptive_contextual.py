"""
Adaptive Contextual Thompson Sampling

Combines context-aware segmentation with adaptive exploration bonus
for optimal performance.

Copyright (c) 2024 Samplit Technologies
"""

import numpy as np
from typing import Dict, Any, List, Optional
import logging
from uuid import UUID

from .contextual_allocator import ContextualAllocator

logger = logging.getLogger(__name__)


class AdaptiveContextualAllocator(ContextualAllocator):
    """
    Adaptive Contextual Thompson Sampling
    
    Combines:
    - Context-aware segmentation (from ContextualAllocator)
    - Adaptive exploration bonus (similar to V2 Fase 3)
    
    Best performance for most use cases - balances exploitation
    of winning variants with exploration of undersampled ones.
    
    Algorithm:
        1. Build segment from context
        2. Fetch segment-specific states
        3. Sample from Beta(alpha, beta)
        4. Add exploration bonus for undersampled variants
        5. Select variant with highest adjusted sample
    
    Exploration Bonus Formula:
        bonus = exploration_factor * sqrt(log(total_samples) / variant_samples)
    
    Example:
        >>> allocator = AdaptiveContextualAllocator(
        ...     db_pool=db_pool,
        ...     feature_service=feature_service,
        ...     config={
        ...         'context_features': ['source', 'device'],
        ...         'exploration_bonus': 0.15,  # NEW
        ...         'min_samples_per_segment': 100
        ...     }
        ... )
    """
    
    def __init__(
        self,
        db_pool,
        feature_service=None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(db_pool, feature_service, config)
        
        # Additional config for adaptive exploration
        self.exploration_bonus = self.config.get('exploration_bonus', 0.15)
        self.min_exploration_samples = self.config.get('min_exploration_samples', 100)
        
        logger.info(
            f"Initialized AdaptiveContextualAllocator: "
            f"exploration_bonus={self.exploration_bonus}"
        )
    
    async def _thompson_sampling(
        self,
        variants: List[Dict[str, Any]]
    ) -> UUID:
        """
        Thompson Sampling with exploration bonus
        
        Overrides parent method to add adaptive exploration.
        """
        # Calculate total samples for exploration bonus
        total_samples = sum(v['samples'] for v in variants)
        
        # ─────────────────────────────────────────────────────────────
        # Pure exploration phase (if too few samples)
        # ─────────────────────────────────────────────────────────────
        if total_samples < self.min_exploration_samples:
            logger.debug(
                f"Pure exploration: total_samples={total_samples} "
                f"< {self.min_exploration_samples}"
            )
            import random
            return random.choice([v['id'] for v in variants])
        
        # ─────────────────────────────────────────────────────────────
        # Thompson Sampling with exploration bonus
        # ─────────────────────────────────────────────────────────────
        samples = []
        
        for variant in variants:
            # Choose which state to use
            if variant['use_segment']:
                state = variant['segment_state']
            else:
                state = variant['global_state']
            
            alpha = state['alpha']
            beta = state['beta']
            variant_samples = state['samples']
            
            # Base Thompson sample
            base_sample = np.random.beta(alpha, beta)
            
            # Calculate exploration bonus
            if self.exploration_bonus > 0 and variant_samples > 0:
                # UCB-style bonus
                bonus = self.exploration_bonus * np.sqrt(
                    np.log(total_samples + 1) / variant_samples
                )
            else:
                bonus = 0.0
            
            # Adjusted sample
            adjusted_sample = base_sample + bonus
            samples.append(adjusted_sample)
            
            logger.debug(
                f"Variant {variant['name']}: "
                f"base={base_sample:.3f}, bonus={bonus:.3f}, "
                f"adjusted={adjusted_sample:.3f}"
            )
        
        # Select highest adjusted sample
        selected_idx = int(np.argmax(samples))
        selected_id = variants[selected_idx]['id']
        
        logger.debug(f"Selected variant index {selected_idx}")
        
        return selected_id
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Override to add exploration metrics"""
        base_metrics = super().get_performance_metrics()
        
        base_metrics.update({
            'algorithm': 'adaptive_contextual_thompson',
            'exploration_bonus': self.exploration_bonus,
            'min_exploration_samples': self.min_exploration_samples
        })
        
        return base_metrics


class AdaptiveContextualConfig:
    """Configuration builder for adaptive contextual allocator"""
    
    @staticmethod
    def default() -> Dict[str, Any]:
        """Default configuration - balanced"""
        return {
            'context_features': ['source', 'device'],
            'min_samples_per_segment': 100,
            'exploration_bonus': 0.15,
            'min_exploration_samples': 100,
            'use_warm_start': True
        }
    
    @staticmethod
    def aggressive_exploration() -> Dict[str, Any]:
        """High exploration - for early experiments"""
        return {
            'context_features': ['source', 'device', 'country'],
            'min_samples_per_segment': 50,
            'exploration_bonus': 0.25,  # Higher bonus
            'min_exploration_samples': 50,
            'use_warm_start': True
        }
    
    @staticmethod
    def conservative_exploitation() -> Dict[str, Any]:
        """Low exploration - for mature experiments"""
        return {
            'context_features': ['source', 'device'],
            'min_samples_per_segment': 200,
            'exploration_bonus': 0.05,  # Lower bonus
            'min_exploration_samples': 200,
            'use_warm_start': True
        }
    
    @staticmethod
    def rich_context() -> Dict[str, Any]:
        """Many context features - detailed segmentation"""
        return {
            'context_features': ['source', 'device', 'country', 'hour', 'is_weekend'],
            'min_samples_per_segment': 150,
            'exploration_bonus': 0.15,
            'min_exploration_samples': 100,
            'use_warm_start': True
        }
