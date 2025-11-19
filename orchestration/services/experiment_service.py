# orchestration/services/experiment_service.py

from typing import Dict, Any, List, Optional
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.allocation_repository import AllocationRepository
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy
import logging

class ExperimentService:
    """
    Experiment management service
    
    Orquesta entre:
    - Data layer (Supabase via repositories)
    - Optimization engine (algoritmos ofuscados)
    - Public API
    """
    
    def __init__(self, db_manager):
        self.experiment_repo = ExperimentRepository(db_manager.pool)
        self.variant_repo = VariantRepository(db_manager.pool)
        self.allocation_repo = AllocationRepository(db_manager.pool)
        self.logger = logging.getLogger(__name__)
    
    async def create_experiment(self,
                               user_id: str,
                               name: str,
                               variants_data: List[Dict[str, Any]],
                               config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create new experiment with variants
        
        Automatically initializes algorithm state (encrypted)
        """
        
        # Determine optimization strategy
        strategy = self._select_strategy(config)
        
        # Create experiment
        experiment_id = await self.experiment_repo.create({
            'user_id': user_id,
            'name': name,
            'description': '',
            'optimization_strategy': strategy.value,
            'config': config or {},
            'status': 'draft'
        })
        
        # Create variants with encrypted algorithm state
        variant_ids = []
        for variant_data in variants_data:
            # Initialize algorithm state (Thompson Sampling params)
            initial_state = self._initialize_algorithm_state(strategy)
            
            variant_id = await self.variant_repo.create_variant(
                experiment_id=experiment_id,
                name=variant_data['name'],
                content=variant_data.get('content', {}),
                initial_algorithm_state=initial_state
            )
            
            variant_ids.append(variant_id)
        
        return {
            'experiment_id': experiment_id,
            'variant_ids': variant_ids,
            'strategy': strategy.value
        }
    
    def _select_strategy(self, config: Optional[Dict]) -> OptimizationStrategy:
        """
        Select optimization strategy based on config
        
        This is where we decide Thompson vs Epsilon vs Sequential
        but client never knows which we chose
        """
        
        if not config:
            return OptimizationStrategy.ADAPTIVE  # Default: Thompson
        
        # Auto-select based on expected traffic
        expected_traffic = config.get('expected_daily_traffic', 1000)
        
        if expected_traffic < 100:
            # Low traffic: use Epsilon-Greedy
            return OptimizationStrategy.FAST_LEARNING
        
        if config.get('is_funnel'):
            # Funnel: use sequential optimizer
            return OptimizationStrategy.SEQUENTIAL
        
        # Default: Thompson Sampling
        return OptimizationStrategy.ADAPTIVE
    
    def _initialize_algorithm_state(self, 
                                    strategy: OptimizationStrategy) -> Dict[str, Any]:
        """
        Initialize algorithm state based on strategy
        
        This returns Thompson Sampling params, Epsilon params, etc.
        pero con nombres genéricos
        """
        
        if strategy == OptimizationStrategy.FAST_LEARNING:
            # Epsilon-Greedy state
            return {
                'success_count': 0,
                'failure_count': 0,
                'samples': 0,
                'exploration_rate': 0.15,  # No llamarlo "epsilon"
                'algorithm_type': 'explore_exploit'  # Genérico
            }
        
        # Thompson Sampling state (default)
        return {
            'success_count': 1,  # Prior (alpha en Thompson)
            'failure_count': 1,  # Prior (beta en Thompson)
            'samples': 0,
            'algorithm_type': 'bayesian'  # Genérico
        }
    
    async def allocate_user_to_variant(self,
                                      experiment_id: str,
                                      user_identifier: str,
                                      context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Allocate user to variant using optimization algorithm
        
        Flow:
        1. Check existing allocation
        2. Get variants with decrypted state
        3. Use optimizer to select
        4. Update algorithm state (encrypted)
        5. Store allocation
        """
        
        # Check existing allocation
        existing = await self.allocation_repo.get_allocation(
            experiment_id, 
            user_identifier
        )
        
        if existing:
            # Return existing allocation
            variant_data = await self.variant_repo.get_variant_public_data(
                existing['variant_id']
            )
            return {
                'variant_id': existing['variant_id'],
                'variant': variant_data,
                'new_allocation': False
            }
        
        # Get experiment config
        experiment = await self.experiment_repo.find_by_id(experiment_id)
        strategy = OptimizationStrategy(experiment['optimization_strategy'])
        
        # Get variants WITH algorithm state (decrypted)
        variants = await self.variant_repo.get_variants_for_optimization(
            experiment_id
        )
        
        # Get optimizer
        optimizer = OptimizerFactory.create(strategy)
        
        # Prepare options for optimizer
        options = []
        for variant in variants:
            state = variant['algorithm_state']
            
            options.append({
                'id': variant['id'],
                'performance': variant['observed_conversion_rate'],
                'samples': state.get('samples', 0),
                # Internal state for optimizer (sin exponer nombres)
                '_internal_state': state
            })
        
        # SELECT VARIANT (aquí está el Thompson Sampling)
        selected_id = await optimizer.select(options, context or {})
        
        # Update variant's algorithm state
        # (increment allocation counter en state cifrado)
        selected_variant = next(v for v in variants if v['id'] == selected_id)
        updated_state = selected_variant['algorithm_state'].copy()
        updated_state['samples'] = updated_state.get('samples', 0) + 1
        
        await self.variant_repo.update_algorithm_state(
            variant_id=selected_id,
            new_state=updated_state
        )
        
        # Store allocation
        await self.allocation_repo.create_allocation(
            experiment_id=experiment_id,
            variant_id=selected_id,
            user_identifier=user_identifier,
            context=context
        )
        
        # Get public variant data
        variant_data = await self.variant_repo.get_variant_public_data(selected_id)
        
        return {
            'variant_id': selected_id,
            'variant': variant_data,
            'new_allocation': True
        }
    
    async def record_conversion(self,
                               experiment_id: str,
                               user_identifier: str,
                               value: float = 1.0) -> None:
        """
        Record conversion
        
        Updates:
        1. Allocation record
        2. Variant metrics
        3. Algorithm state (encrypted)
        """
        
        # Get allocation
        allocation = await self.allocation_repo.get_allocation(
            experiment_id,
            user_identifier
        )
        
        if not allocation or allocation['converted_at']:
            return  # Already converted or no allocation
        
        variant_id = allocation['variant_id']
        
        # Update allocation
        await self.allocation_repo.record_conversion(
            allocation['id'],
            value
        )
        
        # Get variant with state
        variant = await self.variant_repo.get_variant_with_algorithm_state(
            variant_id
        )
        
        # Update algorithm state
        state = variant['algorithm_state_decrypted']
        
        # Update based on algorithm type
        if state.get('algorithm_type') == 'bayesian':
            # Thompson Sampling update (pero ofuscado)
            state['success_count'] = state.get('success_count', 1) + 1
        elif state.get('algorithm_type') == 'explore_exploit':
            # Epsilon-Greedy update
            state['success_count'] = state.get('success_count', 0) + 1
        
        # Save updated state (encrypted)
        await self.variant_repo.update_algorithm_state(
            variant_id=variant_id,
            new_state=state
        )
        
        # Update public metrics (via DB function - no expone estado)
        await self.variant_repo.increment_conversion(variant_id)
