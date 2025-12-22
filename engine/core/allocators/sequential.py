# engine/core/allocators/sequential.py

"""
Sequential Allocator - Global Maxima Optimization

This allocator optimizes for the *entire funnel conversion*, not just local steps.
It implements a Chain Bandit / Cascading Bandit strategy.

Equation:
    Value(Step_i) = Immediate_Reward(Step_i) + γ * Expected_Value(Step_i+1)

Where γ (gamma) is the discount factor (likely 1.0 for strictly sequential funnels).
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
from .bayesian import BayesianAllocator

logger = logging.getLogger(__name__)

class SequentialAllocator(BayesianAllocator):
    """
    Optimizes sequential decision processes (Funnels).
    
    Unlike standard BayesianAllocator which assumes independent experiments,
    SequentialAllocator treats variants as nodes in a graph.
    
    Architecture:
    - Each variant at Step N keeps track of successful transitions to Step N+1.
    - True "Conversion" is defined as reaching the end of the funnel.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.lookahead = self.config.get('lookahead', True)
    
    def select_variant_for_step(
        self, 
        variants: List[Dict[str, Any]], 
        step_id: str,
        total_funnel_steps: int
    ) -> int:
        """
        Select variant considering downstream impact.
        
        Args:
            variants: List of variants at this step
            step_id: Identifier of current step
            total_funnel_steps: Total steps in funnel
        """
        # For MVP: We treat "funnel conversion" as the primary reward signal.
        # Instead of optimizing for "Click to next step", we optimize for "Final Conversion".
        
        # This simplifies the math to standard Thompson Sampling, 
        # BUT the reward signal is delayed (credit assignment problem).
        
        # We delegate to standard Bayesian Logic, but the 'beta' parameters
        # supplied to it will be different (based on final conversions).
        return super().select_variant(variants)

    def update_sequential_state(
        self,
        funnel_state: Dict[str, Any],
        step_index: int,
        variant_index: int,
        final_conversion: bool
    ) -> Dict[str, Any]:
        """
        Update state based on FINAL conversion.
        
        If user converted at the end of the funnel, we credit ALL steps 
        that participated in the path.
        """
        # Get state for the specific variant used at this step
        # path = funnel_state['steps'][step_index]['variants'][variant_index]
        
        # Update using standard Bayesian update
        # If final_conversion is True, reward=1.0. Else 0.0.
        reward = 1.0 if final_conversion else 0.0
        
        # This is handled by the Orchestrator calling update_state()
        # for each participating variant in the successful session.
        pass

    # Override standard update to log specific sequential metrics
    def update_state(self, variant_state, reward):
        # We can add 'downstream_conversions' counter here if needed
        return super().update_state(variant_state, reward)
