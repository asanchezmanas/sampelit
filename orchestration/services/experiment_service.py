# orchestration/services/experiment_service.py

"""
Experiment Management Service

Handles experiment lifecycle, variant allocation, and performance tracking.
Uses proprietary optimization algorithms for intelligent traffic distribution.
"""

from typing import Dict, Any, List, Optional
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.allocation_repository import AllocationRepository
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy
from .cache_service import CacheService
import logging

class ExperimentService:
    """
    Experiment management service with caching
    
    Coordinates experiment creation, traffic allocation, and conversion tracking
    using Samplit's proprietary optimization engine.
    """
    
    def __init__(self, db_manager):
        self.experiment_repo = ExperimentRepository(db_manager.pool)
        self.variant_repo = VariantRepository(db_manager.pool)
        self.allocation_repo = AllocationRepository(db_manager.pool)
        self.cache = CacheService()
        self.logger = logging.getLogger(__name__)
    
    async def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get experiment with caching
        """
        cache_key = f"experiment:{experiment_id}"
        cached = self.cache.get(cache_key)
        
        if cached:
            self.logger.debug(f"Cache hit: experiment {experiment_id}")
            return cached
        
        # Fetch from DB
        experiment = await self.experiment_repo.find_by_id(experiment_id)
        
        if experiment:
            # Cache for 5 minutes
            self.cache.set(cache_key, experiment, ttl=300)
        
        return experiment
    
    async def create_experiment(self,
                               user_id: str,
                               name: str,
                               variants_data: List[Dict[str, Any]],
                               description: Optional[str] = None,
                               config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create new experiment with variants
        
        Initializes optimization algorithm state for intelligent traffic distribution.
        """
        
        # Determine optimization strategy
        strategy = self._select_strategy(config)
        
        # Create experiment
        experiment_id = await self.experiment_repo.create({
            'user_id': user_id,
            'name': name,
            'description': description or '',
            'optimization_strategy': strategy.value,
            'config': config or {},
            'status': 'draft'
        })
        
        # Create variants with encrypted algorithm state
        variant_ids = []
        for variant_data in variants_data:
            # Initialize algorithm state for optimization
            initial_state = self._initialize_algorithm_state(strategy)
            
            variant_id = await self.variant_repo.create_variant(
                experiment_id=experiment_id,
                name=variant_data['name'],
                content=variant_data.get('content', {}),
                initial_algorithm_state=initial_state
            )
            
            variant_ids.append(variant_id)
        
        # Invalidate cache for user's experiments list
        self.cache.invalidate(f"user:{user_id}:experiments")
        
        self.logger.info(
            "Experiment created",
            experiment_id=experiment_id,
            variant_count=len(variant_ids),
            user_id=user_id
        )
        
        return {
            'experiment_id': experiment_id,
            'variant_ids': variant_ids,
            'strategy': strategy.value
        }
    
    def _select_strategy(self, config: Optional[Dict]) -> OptimizationStrategy:
        """
        Select optimization strategy based on config
        
        Auto-selects appropriate algorithm based on traffic patterns.
        """
        
        if not config:
            return OptimizationStrategy.ADAPTIVE  # Default: intelligent allocation
        
        # Auto-select based on expected traffic
        expected_traffic = config.get('expected_daily_traffic', 1000)
        
        if expected_traffic < 100:
            # Low traffic: use fast-learning strategy
            return OptimizationStrategy.FAST_LEARNING
        
        if config.get('is_funnel'):
            # Funnel: use sequential optimizer
            return OptimizationStrategy.SEQUENTIAL
        
        # Default: adaptive intelligent allocation
        return OptimizationStrategy.ADAPTIVE
    
    def _initialize_algorithm_state(self, 
                                    strategy: OptimizationStrategy) -> Dict[str, Any]:
        """
        Initialize algorithm state based on strategy
        
        State includes parameters for the optimization algorithm.
        Implementation details are proprietary.
        """
        
        if strategy == OptimizationStrategy.FAST_LEARNING:
            # Fast-learning strategy state
            return {
                'success_count': 0,
                'failure_count': 0,
                'samples': 0,
                'exploration_rate': 0.15,
                'algorithm_type': 'explore_exploit'
            }
        
        # Adaptive strategy state (default)
        return {
            'success_count': 1,  # Prior
            'failure_count': 1,  # Prior
            'samples': 0,
            'alpha': 1.0,
            'beta': 1.0,
            'algorithm_type': 'bayesian'
        }
    
    async def allocate_user_to_variant(self,
                                      experiment_id: str,
                                      user_identifier: str,
                                      context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Allocate user to variant using optimization algorithm
        
        Uses Samplit's proprietary intelligent allocation to maximize conversions.
        Returns consistent variant for same user (sticky allocation).
        """
        
        # ───────────────────────────────────
        # Check existing allocation (sticky)
        # ───────────────────────────────────
        existing = await self.allocation_repo.get_allocation(
            experiment_id, 
            user_identifier
        )
        
        if existing:
            variant_data = await self.variant_repo.get_variant_public_data(
                existing['variant_id']
            )
            
            self.logger.debug(
                "Existing allocation returned",
                experiment_id=experiment_id,
                variant_id=existing['variant_id']
            )
            
            return {
                'variant_id': existing['variant_id'],
                'variant': variant_data,
                'new_assignment': False,
                'allocation_id': existing['id']
            }
        
        # ───────────────────────────────────
        # Get experiment config (with cache)
        # ───────────────────────────────────
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
            
        strategy = OptimizationStrategy(experiment['optimization_strategy'])
        
        # ───────────────────────────────────
        # Get variants WITH algorithm state (cached)
        # ───────────────────────────────────
        cache_key = f"variants:{experiment_id}"
        variants = self.cache.get(cache_key)
        
        if not variants:
            # Get variants with decrypted algorithm state
            variants = await self.variant_repo.get_variants_for_optimization(
                experiment_id
            )
            # Cache for 1 minute (state changes frequently)
            self.cache.set(cache_key, variants, ttl=60)
        
        # ───────────────────────────────────
        # Get optimizer instance
        # ───────────────────────────────────
        optimizer = OptimizerFactory.create(strategy)
        
        # ───────────────────────────────────
        # Prepare options for optimizer
        # ───────────────────────────────────
        options = []
        for variant in variants:
            state = variant['algorithm_state']
            
            options.append({
                'id': variant['id'],
                'performance': variant['observed_conversion_rate'],
                'samples': state.get('samples', 0),
                '_internal_state': state  # ✅ Full state from database
            })
        
        # ───────────────────────────────────
        # SELECT VARIANT using optimization algorithm
        # ───────────────────────────────────
        selected_id = await optimizer.select(options, context or {})
        
        # ───────────────────────────────────
        # Update variant's algorithm state
        # ───────────────────────────────────
        selected_variant = next(v for v in variants if v['id'] == selected_id)
        updated_state = selected_variant['algorithm_state'].copy()
        updated_state['samples'] = updated_state.get('samples', 0) + 1
        
        await self.variant_repo.update_algorithm_state(
            variant_id=selected_id,
            new_state=updated_state
        )
        
        # ───────────────────────────────────
        # Increment allocation counter
        # ───────────────────────────────────
        await self.variant_repo.increment_allocation(selected_id)
        
        # ───────────────────────────────────
        # Store allocation record
        # ───────────────────────────────────
        allocation_id = await self.allocation_repo.create_allocation(
            experiment_id=experiment_id,
            variant_id=selected_id,
            user_identifier=user_identifier,
            context=context
        )
        
        # Invalidate cache
        self.cache.invalidate(cache_key)
        
        # Get public variant data
        variant_data = await self.variant_repo.get_variant_public_data(selected_id)
        
        self.logger.info(
            "New allocation created",
            experiment_id=experiment_id,
            variant_id=selected_id,
            user_identifier=user_identifier[:8] + "..."  # Partial for privacy
        )
        
        return {
            'variant_id': selected_id,
            'variant': variant_data,
            'new_assignment': True,
            'allocation_id': allocation_id
        }
    
    async def record_conversion(self,
                               experiment_id: str,
                               user_identifier: str,
                               value: float = 1.0) -> None:
        """
        Record conversion event
        
        Updates optimization algorithm with conversion data to improve
        future allocation decisions.
        """
        
        # ───────────────────────────────────
        # Get allocation
        # ───────────────────────────────────
        allocation = await self.allocation_repo.get_allocation(
            experiment_id,
            user_identifier
        )
        
        if not allocation or allocation.get('converted_at'):
            # Already converted or no allocation
            return
        
        variant_id = allocation['variant_id']
        
        # ───────────────────────────────────
        # Update allocation record
        # ───────────────────────────────────
        await self.allocation_repo.record_conversion(
            allocation['id'],
            value
        )
        
        # ───────────────────────────────────
        # Get variant with algorithm state
        # ───────────────────────────────────
        variant = await self.variant_repo.get_variant_with_algorithm_state(
            variant_id
        )
        
        state = variant['algorithm_state_decrypted']
        
        # ───────────────────────────────────
        # Update algorithm state with positive result
        # ───────────────────────────────────
        algorithm_type = state.get('algorithm_type', 'bayesian')
        
        if algorithm_type == 'bayesian':
            # Update success count
            state['success_count'] = state.get('success_count', 1) + 1
            
            # Recalculate distribution parameters
            total_samples = state.get('samples', 0)
            total_successes = state['success_count'] - 1  # Subtract prior
            total_failures = total_samples - total_successes
            
            state['failure_count'] = max(1, total_failures + 1)  # Add prior
            state['alpha'] = float(state['success_count'])
            state['beta'] = float(state['failure_count'])
            
        elif algorithm_type == 'explore_exploit':
            # Update success count for fast-learning
            state['success_count'] = state.get('success_count', 0) + 1
        
        # ───────────────────────────────────
        # Save updated state (encrypted)
        # ───────────────────────────────────
        await self.variant_repo.update_algorithm_state(
            variant_id=variant_id,
            new_state=state
        )
        
        # ───────────────────────────────────
        # Update public metrics
        # ───────────────────────────────────
        await self.variant_repo.increment_conversion(variant_id)
        
        # Invalidate cache
        self.cache.invalidate(f"variants:{experiment_id}")
        
        self.logger.info(
            "Conversion recorded",
            experiment_id=experiment_id,
            variant_id=variant_id,
            value=value
        )
