# engine/core/allocators/_explore.py

"""
Explore-Exploit Allocator

Optimized for low-traffic scenarios where fast learning is critical.

Implementation: [PROPRIETARY]
"""

from typing import Dict, Any, List
from .._base import BaseAllocator
import random

class ExploreExploitAllocator(BaseAllocator):
    """
    Fast-learning allocator for low-traffic scenarios
    
    ✅ FIXED: Now uses real state from database
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Parámetros ofuscados
        self.exploration_factor = config.get('exploration', 0.1)
        self.decay_rate = config.get('decay', 0.995)
        self.min_exploration = config.get('min_exploration', 0.01)
        
        # ✅ REMOVED: No más cache local
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select option using adaptive explore-exploit
        
        ✅ FIXED: Uses real state from database
        """
        
        # ───────────────────────────────────
        # Calcular tasa de exploración dinámica
        # ───────────────────────────────────
        total_samples = sum(
            opt.get('_internal_state', {}).get('samples', 0)
            for opt in options
        )
        
        current_exploration = self.exploration_factor * (self.decay_rate ** total_samples)
        current_exploration = max(current_exploration, self.min_exploration)
        
        # ───────────────────────────────────
        # Decisión: explorar o explotar
        # ───────────────────────────────────
        if random.random() < current_exploration:
            # EXPLORACIÓN: priorizar bajo-sampled
            selected = self._explore(options)
            self._log_decision("explore", selected)
        else:
            # EXPLOTACIÓN: mejor performer
            selected = self._exploit(options)
            self._log_decision("exploit", selected)
        
        return selected
    
    def _explore(self, options: List[Dict]) -> str:
        """
        Exploration strategy
        
        ✅ FIXED: Uses samples from database state
        """
        # Priorizar opciones con menos samples
        sample_counts = {
            opt['id']: opt.get('_internal_state', {}).get('samples', 0)
            for opt in options
        }
        
        min_samples = min(sample_counts.values())
        
        # Candidatos con menos muestras
        under_sampled = [
            opt_id for opt_id, count in sample_counts.items()
            if count <= min_samples * 1.5
        ]
        
        return random.choice(under_sampled) if under_sampled else random.choice([o['id'] for o in options])
    
    def _exploit(self, options: List[Dict]) -> str:
        """
        Exploitation strategy
        
        ✅ FIXED: Uses real performance from database
        """
        performance_scores = {}
        
        for option in options:
            opt_id = option['id']
            state = option.get('_internal_state', {})
            
            samples = state.get('samples', 0)
            success_count = state.get('success_count', 1)
            
            if samples > 0:
                # Conversion rate observado
                raw_rate = (success_count - 1) / samples  # -1 por el prior
                
                # Confidence penalty (menos samples = menos confianza)
                confidence = min(1.0, samples / 100.0)
                
                performance_scores[opt_id] = raw_rate * (0.5 + 0.5 * confidence)
            else:
                performance_scores[opt_id] = 0.0
        
        return max(performance_scores, key=performance_scores.get)
    
    async def update(self, option_id: str, reward: float, context: Dict[str, Any]):
        """Update handled by repository layer"""
        pass
    
    def _log_decision(self, decision_type: str, selected_id: str):
        """Sanitized logging"""
        self.logger.info(
            "Low-traffic allocation",
            variant=selected_id,
            phase=decision_type,  
            method="samplit-fast"
        )

def create(config: Dict[str, Any]) -> ExploreExploitAllocator:
    return ExploreExploitAllocator(config)
