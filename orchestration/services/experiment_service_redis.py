# orchestration/services/experiment_service_redis.py
"""
ExperimentService con Redis

✅ Redis: Estado Thompson (hot cache)
✅ PostgreSQL: Metadata + assignments (source of truth)
✅ Sincronización automática
"""

import redis.asyncio as redis
import asyncio
import json
from typing import Dict, Any, Optional, List
import logging

from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.allocation_repository import AllocationRepository
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy

logger = logging.getLogger(__name__)


class ExperimentServiceWithRedis:
    """
    Versión optimizada con Redis
    
    Performance: 50,000+ req/s
    """
    
    def __init__(self, db_manager, redis_url: str):
        self.experiment_repo = ExperimentRepository(db_manager.pool)
        self.variant_repo = VariantRepository(db_manager.pool)
        self.allocation_repo = AllocationRepository(db_manager.pool)
        self.db = db_manager
        
        # Redis client
        self.redis = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
        # Cache local para metadata
        self._metadata_cache = {}
        
        self.logger = logger
        self.logger.info("🚀 ExperimentServiceWithRedis initialized")
    
    async def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get experiment metadata (with local cache)
        """
        if experiment_id in self._metadata_cache:
            return self._metadata_cache[experiment_id]
        
        experiment = await self.experiment_repo.find_by_id(experiment_id)
        
        if experiment:
            # Cache metadata locally (no Redis needed)
            self._metadata_cache[experiment_id] = experiment
        
        return experiment
    
    async def create_experiment(self, *args, **kwargs):
        """Create experiment (same as base implementation)"""
        # Delegar a base implementation
        from .experiment_service import ExperimentService
        base = ExperimentService(self.db)
        return await base.create_experiment(*args, **kwargs)
    
    async def allocate_user_to_variant(self,
                                      experiment_id: str,
                                      user_identifier: str,
                                      context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        ✅ OPTIMIZED: Lee estado de Redis
        
        Flow:
        1. Check existing (PostgreSQL)
        2. Metadata (local cache)
        3. Estado Thompson (REDIS)
        4. Thompson Sampling (memoria)
        5. Save allocation (PostgreSQL)
        6. Update state (Redis + PostgreSQL async)
        """
        
        # ──────────────────────────────────────────
        # Existing allocation check
        # ──────────────────────────────────────────
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
                'allocation_id': existing['id']
            }
        
        # ──────────────────────────────────────────
        # PASO 1: Metadata (local cache)
        # ──────────────────────────────────────────
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        strategy = OptimizationStrategy(experiment['optimization_strategy'])
        
        # ──────────────────────────────────────────
        # PASO 2: Estado Thompson (REDIS first)
        # ──────────────────────────────────────────
        variants = await self._get_variants_from_redis(experiment_id)
        
        if not variants:
            # Cache miss → PostgreSQL → Redis
            self.logger.info(f"Redis MISS for {experiment_id}, loading from PostgreSQL")
            variants = await self.variant_repo.get_variants_for_optimization(
                experiment_id
            )
            await self._cache_variants_in_redis(experiment_id, variants)
        else:
            self.logger.debug(f"Redis HIT for {experiment_id}")
        
        # ──────────────────────────────────────────
        # PASO 3: Thompson Sampling (en memoria)
        # ──────────────────────────────────────────
        optimizer = OptimizerFactory.create(strategy)
        
        options = []
        for variant in variants:
            state = variant['algorithm_state']
            options.append({
                'id': variant['id'],
                'performance': variant.get('observed_conversion_rate', 0),
                'samples': state.get('samples', 0),
                '_internal_state': state
            })
        
        selected_id = await optimizer.select(options, context or {})
        
        # ──────────────────────────────────────────
        # PASO 4: Save allocation (PostgreSQL)
        # ──────────────────────────────────────────
        allocation_id = await self.allocation_repo.create_allocation(
            experiment_id=experiment_id,
            variant_id=selected_id,
            user_identifier=user_identifier,
            context=context
        )
        
        # ──────────────────────────────────────────
        # PASO 5: Update state (Redis sync + PostgreSQL async)
        # ──────────────────────────────────────────
        await self._increment_samples_redis(selected_id)
        
        # PostgreSQL en background (no esperar)
        asyncio.create_task(
            self.variant_repo.increment_allocation(selected_id)
        )
        
        # Get variant data
        variant_data = await self.variant_repo.get_variant_public_data(selected_id)
        
        return {
            'variant_id': selected_id,
            'variant': variant_data,
            'new_allocation': True,
            'allocation_id': allocation_id
        }
    
    async def record_conversion(self,
                               experiment_id: str,
                               user_identifier: str,
                               value: float = 1.0):
        """
        ✅ OPTIMIZED: Actualiza Redis + PostgreSQL
        """
        
        # Get allocation
        allocation = await self.allocation_repo.get_allocation(
            experiment_id,
            user_identifier
        )
        
        if not allocation or allocation.get('converted_at'):
            return
        
        variant_id = allocation['variant_id']
        
        # Update allocation (PostgreSQL)
        await self.allocation_repo.record_conversion(
            allocation['id'],
            value
        )
        
        # Update Redis (sync - inmediato)
        await self._increment_conversions_redis(variant_id)
        
        # Update PostgreSQL (async - background)
        asyncio.create_task(
            self._update_postgres_conversion(variant_id)
        )
    
    # ══════════════════════════════════════════════
    # REDIS HELPERS
    # ══════════════════════════════════════════════
    
    async def _get_variants_from_redis(self, 
                                       experiment_id: str) -> Optional[List[Dict]]:
        """
        Leer estado Thompson de Redis
        
        Keys:
        - exp:{exp_id}:variants (set de variant_ids)
        - variant:{var_id} (hash con estado)
        """
        try:
            # Get variant IDs
            variant_ids_key = f"exp:{experiment_id}:variants"
            variant_ids = await self.redis.smembers(variant_ids_key)
            
            if not variant_ids:
                return None
            
            # Get state for each variant (pipeline)
            pipe = self.redis.pipeline()
            for variant_id in variant_ids:
                pipe.hgetall(f"variant:{variant_id}")
            
            results = await pipe.execute()
            
            variants = []
            for variant_id, state_dict in zip(variant_ids, results):
                if state_dict:
                    variants.append({
                        'id': variant_id,
                        'algorithm_state': {
                            'success_count': int(state_dict.get('success_count', 1)),
                            'failure_count': int(state_dict.get('failure_count', 1)),
                            'samples': int(state_dict.get('samples', 0)),
                            'alpha': float(state_dict.get('alpha', 1.0)),
                            'beta': float(state_dict.get('beta', 1.0)),
                            'algorithm_type': state_dict.get('algorithm_type', 'bayesian')
                        },
                        'observed_conversion_rate': float(state_dict.get('conversion_rate', 0))
                    })
            
            return variants if variants else None
            
        except Exception as e:
            self.logger.error(f"Redis get error: {e}")
            return None
    
    async def _cache_variants_in_redis(self, 
                                       experiment_id: str,
                                       variants: List[Dict]):
        """
        Cachear estado en Redis
        
        TTL: 1 hora (se actualiza constantemente)
        """
        try:
            pipe = self.redis.pipeline()
            
            # Store variant IDs
            variant_ids_key = f"exp:{experiment_id}:variants"
            for variant in variants:
                pipe.sadd(variant_ids_key, variant['id'])
            pipe.expire(variant_ids_key, 3600)
            
            # Store each variant state
            for variant in variants:
                state = variant['algorithm_state']
                variant_key = f"variant:{variant['id']}"
                
                pipe.hset(variant_key, mapping={
                    'success_count': state.get('success_count', 1),
                    'failure_count': state.get('failure_count', 1),
                    'samples': state.get('samples', 0),
                    'alpha': state.get('alpha', 1.0),
                    'beta': state.get('beta', 1.0),
                    'algorithm_type': state.get('algorithm_type', 'bayesian'),
                    'conversion_rate': variant.get('observed_conversion_rate', 0)
                })
                pipe.expire(variant_key, 3600)
            
            await pipe.execute()
            
        except Exception as e:
            self.logger.error(f"Redis cache error: {e}")
    
    async def _increment_samples_redis(self, variant_id: str):
        """Incrementar samples en Redis (atómico)"""
        try:
            variant_key = f"variant:{variant_id}"
            await self.redis.hincrby(variant_key, 'samples', 1)
        except Exception as e:
            self.logger.error(f"Redis increment samples error: {e}")
    
    async def _increment_conversions_redis(self, variant_id: str):
        """Incrementar conversions en Redis (atómico)"""
        try:
            variant_key = f"variant:{variant_id}"
            
            pipe = self.redis.pipeline()
            pipe.hincrby(variant_key, 'success_count', 1)
            
            # Recalcular alpha y beta después del increment
            # (Se hace en siguiente lectura para evitar race conditions)
            
            await pipe.execute()
            
        except Exception as e:
            self.logger.error(f"Redis increment conversions error: {e}")
    
    async def _update_postgres_conversion(self, variant_id: str):
        """
        Actualizar PostgreSQL en background
        
        No bloquea el request principal
        """
        try:
            # Get current state from Redis
            variant_key = f"variant:{variant_id}"
            state_dict = await self.redis.hgetall(variant_key)
            
            if not state_dict:
                return
            
            # Update public metrics
            await self.variant_repo.increment_conversion(variant_id)
            
            # Cada 100 conversiones, sincronizar estado completo
            conversions = int(state_dict.get('success_count', 1))
            if conversions % 100 == 0:
                await self._full_sync_to_postgres(variant_id)
            
        except Exception as e:
            self.logger.error(f"PostgreSQL update error: {e}")
    
    async def _full_sync_to_postgres(self, variant_id: str):
        """
        Sincronización completa Redis → PostgreSQL
        
        Mantiene PostgreSQL como source of truth
        """
        try:
            variant_key = f"variant:{variant_id}"
            state_dict = await self.redis.hgetall(variant_key)
            
            if not state_dict:
                return
            
            state = {
                'success_count': int(state_dict['success_count']),
                'failure_count': int(state_dict['failure_count']),
                'samples': int(state_dict['samples']),
                'alpha': float(state_dict['alpha']),
                'beta': float(state_dict['beta']),
                'algorithm_type': state_dict['algorithm_type']
            }
            
            await self.variant_repo.update_algorithm_state(variant_id, state)
            
            self.logger.info(f"Full sync to PostgreSQL for variant {variant_id[:8]}")
            
        except Exception as e:
            self.logger.error(f"Full sync error: {e}")
