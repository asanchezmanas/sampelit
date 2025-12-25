# engine/core/allocators/_bayesian.py

"""
Adaptive Bayesian Allocator

Implementation: [REDACTED - PROPRIETARY]

This module implements Samplit's adaptive allocation algorithm
using advanced Bayesian inference methods.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import numpy as np
from .._base import BaseAllocator
from ..math._distributions import sample_posterior  # Ofuscado

class AdaptiveBayesianAllocator(BaseAllocator):
    """
    Proprietary adaptive allocation engine
    
    Note: Actual implementation details are confidential.
    This uses advanced statistical inference for optimal allocation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Parámetros sin nombres obvios
        self.learning_rate = config.get('learning_rate', 0.1)
        self.min_samples = config.get('min_samples', 30)
        
        # ✅ REMOVED: No más estado local
        # Solo usamos estado de BD
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select optimal option using proprietary algorithm
        
        ✅ FIXED: Now uses real state from database
        
        This method uses Samplit's adaptive Bayesian inference
        to balance exploration and exploitation.
        
        Implementation: [CONFIDENTIAL]
        """
        
        if not options:
            raise ValueError("No options provided")
        
        # ───────────────────────────────────
        # ✅ CALCULAR SCORES usando estado REAL de BD
        # ───────────────────────────────────
        allocation_scores = {}
        
        for option in options:
            opt_id = option['id']
            
            # ✅ USAR ESTADO DE LA BASE DE DATOS
            internal_state = option.get('_internal_state', {})
            
            # Obtener parámetros internos de BD
            success_count = internal_state.get('success_count', 1)
            failure_count = internal_state.get('failure_count', 1)
            samples = internal_state.get('samples', 0)
            
            # Calcular exploration bonus
            exploration_bonus = self._calculate_exploration_bonus(samples)
            
            # 🎲 SAMPLE from Beta distribution
            score = sample_posterior(
                success_count=success_count,
                failure_count=failure_count,
                exploration_bonus=exploration_bonus
            )
            
            allocation_scores[opt_id] = score
        
        # ───────────────────────────────────
        # Seleccionar el mejor
        # ───────────────────────────────────
        selected_id = max(allocation_scores, key=allocation_scores.get)
        
        # Log ofuscado 
        self._log_allocation(
            selected_id=selected_id,
            scores=allocation_scores,
            method="adaptive_bayesian"
        )
        
        return selected_id
    
    async def update(self, 
                    option_id: str, 
                    reward: float, 
                    context: Dict[str, Any]) -> None:
        """
        Update performance model with observed reward
        
        ✅ NOTE: State updates now handled by repository layer
        This method is for compatibility with base interface
        """
        # Estado se maneja en ExperimentService.record_conversion()
        # Este método queda para compatibilidad con interface
        pass
    
    def _calculate_exploration_bonus(self, samples: int) -> float:
        """
        Calculate exploration bonus
        
        ✅ FIXED: Uses samples count from database
        
        This encourages exploration of under-sampled options
        using proprietary heuristics.
        """
        if samples < self.min_samples:
            # UCB-style exploration bonus
            # Cuanto menos samples, mayor bonus
            return self.learning_rate * np.sqrt(
                np.log(samples + 2) / (samples + 1)
            )
        
        return 0.0
    
    def _log_allocation(self, **kwargs):
        """Log allocation decision (sanitized for security)"""
        # Solo loggear info no-sensible
        self.logger.info(
            "Variant allocated",
            variant=kwargs['selected_id'],
            method="samplit-adaptive"  # Genérico
            # NO loggear scores, algoritmo, etc.
        )

def create(config: Dict[str, Any]) -> AdaptiveBayesianAllocator:
    """Factory function"""
    return AdaptiveBayesianAllocator(config)
