# orchestration/services/experiment_service_redis.py
"""
ExperimentService con Redis para estado hot

✅ Redis: Estado Engine (actualizado en tiempo real)
✅ PostgreSQL: Metadata + asignaciones (source of truth)
"""

import redis.asyncio as redis
import json
from typing import Dict, Any, Optional, List

class ExperimentServiceWithRedis:
    """
    Versión escalable con Redis
    
    Usar cuando: >1M requests/día
    """
    
    def __init__(self, db_manager, redis_url: str):
        self.experiment_repo = ExperimentRepository(db_manager.pool)
        self.variant_repo = VariantRepository(db_manager.pool)
        self.allocation_repo = AllocationRepository(db_manager.pool)
        
        # Redis client
        self.redis = redis.from_url(redis_url, decode_responses=True)
        
        self.logger = logging.getLogger(__name__)
    
    async def allocate_user_to_variant(self,
                                      experiment_id: str,
                                      user_identifier: str,
                                      context: Optional[Dict] = None):
        """
        ✅ OPTIMIZED: Lee estado de Redis, fallback a PostgreSQL
        """
        
        # Check existing allocation (PostgreSQL)
        existing = await self.allocation_repo.get_allocation(
            experiment_id, 
            user_identifier
        )
        
        if existing:
            return self._format_existing_allocation(existing)
        
        # ──────────────────────────────────────────
        # PASO 1: Metadata (PostgreSQL + cache local)
        # ──────────────────────────────────────────
        experiment = await self._get_experiment_cached(experiment_id)
        strategy = OptimizationStrategy(experiment['optimization_strategy'])
        
        # ──────────────────────────────────────────
        # PASO 2: Estado Engine (REDIS first)
        # ──────────────────────────────────────────
        variants = await self._get_variants_from_redis(experiment_id)
        
        if not variants:
            # Cache miss → PostgreSQL → Redis
            variants = await self.variant_repo.get_variants_for_optimization(
                experiment_id
            )
            await self._cache_variants_in_redis(experiment_id, variants)
            self.logger.info(f"Redis cache miss, loaded from PostgreSQL")
        else:
            self.logger.debug(f"Redis cache hit for {experiment_id}")
        
        # Engine (en memoria)
        optimizer = OptimizerFactory.create(strategy)
        options = self._prepare_options(variants)
        selected_id = await optimizer.select(options, context or {})
        
        # ──────────────────────────────────────────
        # PASO 3: Guardar asignación (PostgreSQL)
        # ──────────────────────────────────────────
        allocation_id = await self.allocation_repo.create_allocation(
            experiment_id=experiment_id,
            variant_id=selected_id,
            user_identifier=user_identifier,
            context=context
        )
        
        # ──────────────────────────────────────────
        # PASO 4: Actualizar estado (Redis + PostgreSQL async)
        # ──────────────────────────────────────────
        await self._update_variant_state(
            experiment_id=experiment_id,
            variant_id=selected_id,
            allocation=True,
            conversion=False
        )
        
        # Increment counter (PostgreSQL async - no wait)
        asyncio.create_task(
            self.variant_repo.increment_allocation(selected_id)
        )
        
        return {
            'variant_id': selected_id,
            'allocation_id': allocation_id,
            'new_allocation': True
        }
    
    async def _get_variants_from_redis(self, 
                                       experiment_id: str) -> Optional[List[Dict]]:
        """
        Leer estado Engine de Redis
        
        Key format: variants:{experiment_id}:{variant_id}
        """
        try:
            # Get all variant IDs for experiment
            variant_ids_key = f"exp:{experiment_id}:variants"
            variant_ids = await self.redis.smembers(variant_ids_key)
            
            if not variant_ids:
                return None
            
            # Get state for each variant (pipeline para eficiencia)
            pipe = self.redis.pipeline()
            for variant_id in variant_ids:
                pipe.hgetall(f"variant:{variant_id}")
            
            results = await pipe.execute()
            
            variants = []
            for variant_id, state_dict in zip(variant_ids, results):
                if state_dict:
                    # Reconstruct variant with state
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
            
            # Store variant IDs set
            variant_ids_key = f"exp:{experiment_id}:variants"
            for variant in variants:
                pipe.sadd(variant_ids_key, variant['id'])
            
            pipe.expire(variant_ids_key, 3600)  # 1 hour
            
            # Store each variant state
            for variant in variants:
                state = variant['algorithm_state']
                variant_key = f"variant:{variant['id']}"
                
                pipe.hset(variant_key, mapping={
                    'success_count': state['success_count'],
                    'failure_count': state['failure_count'],
                    'samples': state['samples'],
                    'alpha': state['alpha'],
                    'beta': state['beta'],
                    'algorithm_type': state['algorithm_type'],
                    'conversion_rate': variant.get('observed_conversion_rate', 0)
                })
                
                pipe.expire(variant_key, 3600)  # 1 hour
            
            await pipe.execute()
            
        except Exception as e:
            self.logger.error(f"Redis cache error: {e}")
    
    async def _update_variant_state(self,
                                    experiment_id: str,
                                    variant_id: str,
                                    allocation: bool = False,
                                    conversion: bool = False):
        """
        Actualizar estado en Redis Y PostgreSQL
        
        Redis: Inmediato (sincrónico)
        PostgreSQL: Async (no esperar)
        """
        try:
            # ──────────────────────────────────────────
            # Redis: Actualización atómica
            # ──────────────────────────────────────────
            variant_key = f"variant:{variant_id}"
            
            pipe = self.redis.pipeline()
            
            if allocation:
                pipe.hincrby(variant_key, 'samples', 1)
            
            if conversion:
                pipe.hincrby(variant_key, 'success_count', 1)
                # Recalcular alpha/beta
                # (Se hace en siguiente lectura para evitar race conditions)
            
            await pipe.execute()
            
            # ──────────────────────────────────────────
            # PostgreSQL: Async (no bloquear)
            # ──────────────────────────────────────────
            if allocation or conversion:
                asyncio.create_task(
                    self._sync_state_to_postgres(variant_id, conversion)
                )
            
        except Exception as e:
            self.logger.error(f"State update error: {e}")
    
    async def _sync_state_to_postgres(self, variant_id: str, conversion: bool):
        """
        Sincronizar estado Redis → PostgreSQL
        
        Esto corre en background, no bloquea el request
        """
        try:
            if conversion:
                await self.variant_repo.increment_conversion(variant_id)
            else:
                await self.variant_repo.increment_allocation(variant_id)
            
            # Cada 100 asignaciones, sincronizar estado completo
            # (Para mantener PostgreSQL como source of truth)
            variant_key = f"variant:{variant_id}"
            samples = int(await self.redis.hget(variant_key, 'samples') or 0)
            
            if samples % 100 == 0:
                await self._full_sync_to_postgres(variant_id)
                
        except Exception as e:
            self.logger.error(f"Postgres sync error: {e}")
    
    async def _full_sync_to_postgres(self, variant_id: str):
        """
        Sincronización completa Redis → PostgreSQL
        
        Llamado cada 100 asignaciones o cuando Redis se reinicia
        """
        try:
            # Leer estado de Redis
            variant_key = f"variant:{variant_id}"
            state_dict = await self.redis.hgetall(variant_key)
            
            if not state_dict:
                return
            
            # Construir estado completo
            state = {
                'success_count': int(state_dict['success_count']),
                'failure_count': int(state_dict['failure_count']),
                'samples': int(state_dict['samples']),
                'alpha': float(state_dict['alpha']),
                'beta': float(state_dict['beta']),
                'algorithm_type': state_dict['algorithm_type']
            }
            
            # Guardar en PostgreSQL (encriptado)
            await self.variant_repo.update_algorithm_state(variant_id, state)
            
            self.logger.info(f"Full sync to PostgreSQL for variant {variant_id}")
            
        except Exception as e:
            self.logger.error(f"Full sync error: {e}")
