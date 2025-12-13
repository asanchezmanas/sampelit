# orchestration/services/segmented_experiment_service.py

"""
Segmented Experiment Service

Extends ExperimentService with segmentation capabilities.
Replaces the original service when segmentation is active.
"""

from typing import Dict, Any, List, Optional
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.allocation_repository import AllocationRepository
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy
from .cache_service import CacheService
from .segmentation import (
    ContextExtractor,
    ChannelType,
    SegmentationService,
    ClusteringService
)
import logging

logger = logging.getLogger(__name__)

class SegmentedExperimentService:
    """
    Experiment service with segmentation support
    
    ✅ Extends original service with:
    - Context extraction and normalization
    - Manual segmentation
    - Auto-clustering
    - Per-segment Thompson Sampling
    """
    
    def __init__(self, db_manager):
        # Original repos
        self.experiment_repo = ExperimentRepository(db_manager.pool)
        self.variant_repo = VariantRepository(db_manager.pool)
        self.allocation_repo = AllocationRepository(db_manager.pool)
        self.cache = CacheService()
        
        # Segmentation services
        self.context_extractor = ContextExtractor()
        self.segmentation_service = SegmentationService(db_manager.pool)
        self.clustering_service = ClusteringService(db_manager.pool)
        
        self.logger = logging.getLogger(__name__)
        self.db_pool = db_manager.pool
    
    async def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment with caching"""
        cache_key = f"experiment:{experiment_id}"
        cached = self.cache.get(cache_key)
        
        if cached:
            self.logger.debug(f"Cache hit for experiment {experiment_id}")
            return cached
        
        experiment = await self.experiment_repo.find_by_id(experiment_id)
        
        if experiment:
            self.cache.set(cache_key, experiment, ttl=300)
        
        return experiment
    
    async def create_experiment(
        self,
        user_id: str,
        name: str,
        variants_data: List[Dict[str, Any]],
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create experiment with optional segmentation config
        
        config can include:
        {
            'segmentation': {
                'enabled': True,
                'mode': 'manual',  # or 'auto'
                'segment_by': ['source', 'device'],
                'auto_activation': True,
                'auto_activation_threshold': 1000
            }
        }
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
            initial_state = self._initialize_algorithm_state(strategy)
            
            variant_id = await self.variant_repo.create_variant(
                experiment_id=experiment_id,
                name=variant_data['name'],
                content=variant_data.get('content', {}),
                initial_algorithm_state=initial_state
            )
            
            variant_ids.append(variant_id)
        
        # Setup segmentation config
        segmentation_config = config.get('segmentation', {}) if config else {}
        if segmentation_config.get('enabled'):
            await self._setup_segmentation_config(experiment_id, segmentation_config)
        
        self.cache.invalidate(f"user:{user_id}:experiments")
        
        return {
            'experiment_id': experiment_id,
            'variant_ids': variant_ids,
            'strategy': strategy.value
        }
    
    async def _setup_segmentation_config(
        self, 
        experiment_id: str, 
        config: Dict
    ) -> None:
        """Setup segmentation configuration for experiment"""
        
        mode = config.get('mode', 'disabled')
        segment_by = config.get('segment_by', [])
        auto_activation = config.get('auto_activation', False)
        auto_activation_threshold = config.get('auto_activation_threshold', 1000)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO experiment_segmentation_config (
                    experiment_id, mode, segment_by,
                    auto_activation_enabled, auto_activation_threshold
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (experiment_id) DO UPDATE SET
                    mode = EXCLUDED.mode,
                    segment_by = EXCLUDED.segment_by,
                    auto_activation_enabled = EXCLUDED.auto_activation_enabled,
                    auto_activation_threshold = EXCLUDED.auto_activation_threshold
                """,
                experiment_id,
                mode,
                segment_by,
                auto_activation,
                auto_activation_threshold
            )
    
    def _select_strategy(self, config: Optional[Dict]) -> OptimizationStrategy:
        """Select optimization strategy"""
        if not config:
            return OptimizationStrategy.ADAPTIVE
        
        expected_traffic = config.get('expected_daily_traffic', 1000)
        
        if expected_traffic < 100:
            return OptimizationStrategy.FAST_LEARNING
        
        if config.get('is_funnel'):
            return OptimizationStrategy.SEQUENTIAL
        
        return OptimizationStrategy.ADAPTIVE
    
    def _initialize_algorithm_state(
        self, 
        strategy: OptimizationStrategy
    ) -> Dict[str, Any]:
        """Initialize algorithm state"""
        if strategy == OptimizationStrategy.FAST_LEARNING:
            return {
                'success_count': 0,
                'failure_count': 0,
                'samples': 0,
                'exploration_rate': 0.15,
                'algorithm_type': 'explore_exploit'
            }
        
        return {
            'success_count': 1,
            'failure_count': 1,
            'samples': 0,
            'alpha': 1.0,
            'beta': 1.0,
            'algorithm_type': 'bayesian'
        }
    
    async def allocate_user_to_variant(
        self,
        experiment_id: str,
        user_identifier: str,
        context: Optional[Dict] = None,
        channel: ChannelType = ChannelType.WEB
    ) -> Dict[str, Any]:
        """
        ✅ ENHANCED: Allocate user with segmentation support
        
        Flow:
        1. Extract and normalize context
        2. Determine segment (manual/auto/disabled)
        3. Thompson Sampling PER SEGMENT
        4. Create allocation with segment_key
        """
        
        # Check existing allocation
        existing = await self.allocation_repo.get_allocation(
            experiment_id, 
            user_identifier
        )
        
        if existing:
            variant_data = await self.variant_repo.get_variant_public_data(
                existing['variant_id']
            )
            return {
                'variant_id': existing['variant_id'],
                'variant': variant_data,
                'new_allocation': False,
                'allocation_id': existing['id'],
                'segment_key': existing.get('segment_key', 'default')
            }
        
        # Extract and normalize context
        normalized_context = self.context_extractor.extract(
            channel=channel,
            raw_data=context or {}
        )
        
        # Get experiment config
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Check if clustering is enabled
        async with self.db_pool.acquire() as conn:
            seg_config = await conn.fetchrow(
                "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
                experiment_id
            )
        
        # If auto-clustering, predict cluster
        if seg_config and seg_config['mode'] == 'auto':
            predicted_cluster = await self.clustering_service.predict_cluster(
                experiment_id,
                normalized_context
            )
            if predicted_cluster:
                normalized_context['_predicted_cluster'] = predicted_cluster
        
        # Determine segment
        segment_key = await self.segmentation_service.get_segment_key(
            experiment_id,
            normalized_context
        )
        
        # Ensure segment exists
        await self.segmentation_service.ensure_segment_exists(
            experiment_id,
            segment_key,
            normalized_context
        )
        
        # Get variants FOR THIS SEGMENT
        strategy = OptimizationStrategy(experiment['optimization_strategy'])
        
        # Try cache first
        cache_key = f"variants:{experiment_id}:{segment_key}"
        variants = self.cache.get(cache_key)
        
        if not variants:
            variants = await self._get_variants_for_segment(
                experiment_id,
                segment_key
            )
            self.cache.set(cache_key, variants, ttl=60)
        
        # Get optimizer
        optimizer = OptimizerFactory.create(strategy)
        
        # Prepare options
        options = []
        for variant in variants:
            state = variant['algorithm_state']
            
            options.append({
                'id': variant['id'],
                'performance': variant['observed_conversion_rate'],
                'samples': state.get('samples', 0),
                '_internal_state': state
            })
        
        # SELECT VARIANT (Thompson Sampling for THIS segment)
        selected_id = await optimizer.select(options, normalized_context or {})
        
        # Update variant's algorithm state
        selected_variant = next(v for v in variants if v['id'] == selected_id)
        updated_state = selected_variant['algorithm_state'].copy()
        updated_state['samples'] = updated_state.get('samples', 0) + 1
        
        await self._update_variant_segment_state(
            variant_id=selected_id,
            segment_key=segment_key,
            new_state=updated_state
        )
        
        # Increment allocation counter (for THIS segment)
        await self._increment_variant_segment_allocation(selected_id, segment_key)
        
        # Store allocation WITH segment_key
        allocation_id = await self._create_allocation_with_segment(
            experiment_id=experiment_id,
            variant_id=selected_id,
            user_identifier=user_identifier,
            segment_key=segment_key,
            context=normalized_context
        )
        
        # Invalidate cache
        self.cache.invalidate(cache_key)
        
        # Get public variant data
        variant_data = await self.variant_repo.get_variant_public_data(selected_id)
        
        return {
            'variant_id': selected_id,
            'variant': variant_data,
            'new_allocation': True,
            'allocation_id': allocation_id,
            'segment_key': segment_key
        }
    
    async def _get_variants_for_segment(
        self,
        experiment_id: str,
        segment_key: str
    ) -> List[Dict[str, Any]]:
        """
        Get variants with algorithm state for specific segment
        
        Creates segment-specific variant records if they don't exist
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, name, content,
                    algorithm_state,
                    total_allocations, total_conversions,
                    observed_conversion_rate,
                    is_active
                FROM variants
                WHERE experiment_id = $1 
                  AND segment_key = $2 
                  AND is_active = true
                """,
                experiment_id,
                segment_key
            )
        
        variants = []
        for row in rows:
            variant = dict(row)
            
            # Decrypt algorithm state
            if row['algorithm_state']:
                from engine.state.encryption import get_encryptor
                encryptor = get_encryptor()
                state = encryptor.decrypt_state(row['algorithm_state'])
                variant['algorithm_state'] = state
            else:
                variant['algorithm_state'] = {
                    'alpha': 1.0,
                    'beta': 1.0,
                    'samples': 0,
                    'algorithm_type': 'bayesian'
                }
            
            variants.append(variant)
        
        # If no variants for this segment, create them
        if not variants and segment_key != 'default':
            variants = await self._initialize_variants_for_segment(
                experiment_id,
                segment_key
            )
        
        return variants
    
    async def _initialize_variants_for_segment(
        self,
        experiment_id: str,
        segment_key: str
    ) -> List[Dict[str, Any]]:
        """
        Initialize variants for new segment
        
        Clones from default segment
        """
        
        logger.info(f"Initializing variants for new segment: {segment_key}")
        
        # Get default variants
        async with self.db_pool.acquire() as conn:
            default_variants = await conn.fetch(
                """
                SELECT id, element_id, variant_order, name, content
                FROM element_variants
                WHERE element_id IN (
                    SELECT id FROM experiment_elements WHERE experiment_id = $1
                )
                AND segment_key = 'default'
                """,
                experiment_id
            )
        
        # Create segment-specific copies
        variants = []
        for default_var in default_variants:
            # Initialize state
            initial_state = {
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'alpha': 1.0,
                'beta': 1.0,
                'algorithm_type': 'bayesian'
            }
            
            # Encrypt
            from engine.state.encryption import get_encryptor
            encryptor = get_encryptor()
            encrypted_state = encryptor.encrypt_state(initial_state)
            
            async with self.db_pool.acquire() as conn:
                variant_id = await conn.fetchval(
                    """
                    INSERT INTO element_variants (
                        element_id, variant_order, segment_key,
                        name, content, algorithm_state,
                        total_allocations, total_conversions
                    ) VALUES ($1, $2, $3, $4, $5, $6, 0, 0)
                    RETURNING id
                    """,
                    default_var['element_id'],
                    default_var['variant_order'],
                    segment_key,
                    default_var['name'],
                    default_var['content'],
                    encrypted_state
                )
            
            variants.append({
                'id': str(variant_id),
                'name': default_var['name'],
                'content': default_var['content'],
                'algorithm_state': initial_state,
                'total_allocations': 0,
                'total_conversions': 0,
                'observed_conversion_rate': 0.0,
                'is_active': True
            })
        
        return variants
    
    async def _update_variant_segment_state(
        self,
        variant_id: str,
        segment_key: str,
        new_state: Dict[str, Any]
    ) -> None:
        """Update algorithm state for variant in specific segment"""
        
        from engine.state.encryption import get_encryptor
        encryptor = get_encryptor()
        encrypted_state = encryptor.encrypt_state(new_state)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE element_variants
                SET 
                    algorithm_state = $1,
                    updated_at = NOW()
                WHERE id = $2 AND segment_key = $3
                """,
                encrypted_state,
                variant_id,
                segment_key
            )
    
    async def _increment_variant_segment_allocation(
        self,
        variant_id: str,
        segment_key: str
    ) -> None:
        """Increment allocation count for variant in segment"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE element_variants
                SET 
                    total_allocations = total_allocations + 1,
                    updated_at = NOW()
                WHERE id = $1 AND segment_key = $2
                """,
                variant_id,
                segment_key
            )
    
    async def _create_allocation_with_segment(
        self,
        experiment_id: str,
        variant_id: str,
        user_identifier: str,
        segment_key: str,
        context: Dict
    ) -> str:
        """Create allocation with segment tracking"""
        
        import json
        
        async with self.db_pool.acquire() as conn:
            allocation_id = await conn.fetchval(
                """
                INSERT INTO assignments 
                (experiment_id, variant_id, user_id, segment_key, context)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                experiment_id,
                variant_id,
                user_identifier,
                segment_key,
                json.dumps(context or {})
            )
        
        return str(allocation_id)
    
    async def record_conversion(
        self,
        experiment_id: str,
        user_identifier: str,
        value: float = 1.0
    ) -> None:
        """Record conversion (segment-aware)"""
        
        allocation = await self.allocation_repo.get_allocation(
            experiment_id,
            user_identifier
        )
        
        if not allocation or allocation.get('converted_at'):
            return
        
        variant_id = allocation['variant_id']
        segment_key = allocation.get('segment_key', 'default')
        
        # Update allocation
        await self.allocation_repo.record_conversion(
            allocation['id'],
            value
        )
        
        # Get variant with state FOR THIS SEGMENT
        async with self.db_pool.acquire() as conn:
            variant_row = await conn.fetchrow(
                """
                SELECT algorithm_state
                FROM element_variants
                WHERE id = $1 AND segment_key = $2
                """,
                variant_id,
                segment_key
            )
        
        if not variant_row:
            logger.warning(f"Variant {variant_id} not found for segment {segment_key}")
            return
        
        # Decrypt and update state
        from engine.state.encryption import get_encryptor
        encryptor = get_encryptor()
        state = encryptor.decrypt_state(variant_row['algorithm_state'])
        
        # Update Thompson Sampling parameters
        if state.get('algorithm_type') == 'bayesian':
            state['success_count'] = state.get('success_count', 1) + 1
            
            total_samples = state.get('samples', 0)
            total_successes = state['success_count']
            total_failures = total_samples - (total_successes - 1) + state.get('failure_count', 1)
            
            state['alpha'] = float(total_successes)
            state['beta'] = float(total_failures)
        
        # Save updated state
        await self._update_variant_segment_state(
            variant_id=variant_id,
            segment_key=segment_key,
            new_state=state
        )
        
        # Update public metrics (for THIS segment)
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE element_variants
                SET 
                    total_conversions = total_conversions + 1,
                    conversion_rate = 
                        (total_conversions + 1)::DECIMAL / 
                        GREATEST(total_allocations, 1)::DECIMAL,
                    updated_at = NOW()
                WHERE id = $1 AND segment_key = $2
                """,
                variant_id,
                segment_key
            )
        
        # Update segment performance cache
        await self.segmentation_service.update_segment_performance(
            experiment_id,
            segment_key
        )
        
        # Invalidate cache
        self.cache.invalidate(f"variants:{experiment_id}:{segment_key}")
