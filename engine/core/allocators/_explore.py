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
    
    This uses a proprietary explore-exploit strategy
    optimized for sparse data situations.
    
    Note: Not traditional epsilon-greedy (enhanced version)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Parámetros ofuscados
        self.exploration_factor = config.get('exploration', 0.1)
        self.decay_rate = config.get('decay', 0.995)
        self.min_exploration = config.get('min_exploration', 0.01)
        
        self._performance_cache = {}
        self._exploration_schedule = self._init_schedule()
    
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select option using adaptive explore-exploit
        
        Implementation uses Samplit's enhanced exploration strategy
        with dynamic decay and contextual awareness.
        """
        
        # Actualizar tasa de exploración (epsilon decay)
        current_exploration = self._get_current_exploration_rate()
        
        # Decisión: explorar o explotar
        if random.random() < current_exploration:
            # EXPLORACIÓN: selección uniforme
            selected = self._explore(options)
            self._log_decision("explore", selected)
        else:
            # EXPLOTACIÓN: mejor performer actual
            selected = self._exploit(options)
            self._log_decision("exploit", selected)
        
        return selected
    
    def _explore(self, options: List[Dict]) -> str:
        """
        Exploration strategy (confidential implementation)
        
        Not pure random - uses smart exploration with
        under-sampling bias.
        """
        # Priorizar opciones con menos samples
        sample_counts = {
            opt['id']: self._get_sample_count(opt['id'])
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
        Exploitation strategy (proprietary)
        
        Selects best performing option with confidence weighting.
        """
        performance_scores = {}
        
        for option in options:
            opt_id = option['id']
            perf_data = self._performance_cache.get(opt_id, {})
            
            # Calcular score ajustado por confianza
            if perf_data.get('samples', 0) > 0:
                raw_rate = perf_data['successes'] / perf_data['samples']
                confidence = self._calculate_confidence(perf_data['samples'])
                performance_scores[opt_id] = raw_rate * confidence
            else:
                performance_scores[opt_id] = 0.0
        
        return max(performance_scores, key=performance_scores.get)
    
    def _get_current_exploration_rate(self) -> float:
        """Dynamic exploration rate with decay"""
        total_samples = sum(
            data.get('samples', 0)
            for data in self._performance_cache.values()
        )
        
        # Decay basado en experiencia
        decayed = self.exploration_factor * (self.decay_rate ** total_samples)
        
        return max(decayed, self.min_exploration)
    
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
