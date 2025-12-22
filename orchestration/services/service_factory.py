# orchestration/services/service_factory.py
"""
Service Factory con Auto-Switch

Decide automáticamente qué implementación usar:
- ExperimentService (PostgreSQL puro)
- ExperimentServiceWithRedis (Redis + PostgreSQL)
"""

import os
import logging
from typing import Optional
from .experiment_service import ExperimentService
from .experiment_service_redis import ExperimentServiceWithRedis
from .metrics_service import MetricsService

logger = logging.getLogger(__name__)


class ServiceFactory:
    """
    Factory que decide automáticamente la implementación
    
    Criterios:
    1. Variable de entorno REDIS_URL presente
    2. Threshold de 1M req/día alcanzado
    3. Flag manual FORCE_REDIS=true
    """
    
    _instance: Optional['ServiceFactory'] = None
    _service: Optional[ExperimentService] = None
    _metrics: Optional[MetricsService] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_funnel_service(cls, db_manager) -> 'FunnelService':
        """
        Get Funnel Service instance
        """
        if not cls._funnel_service:
            from orchestration.services.funnel_service import FunnelService
            cls._funnel_service = FunnelService(db_manager)
        return cls._funnel_service

    @classmethod
    async def create_experiment_service(cls, db_manager):
        """
        Crear servicio de experimentos
        
        Auto-detecta si usar Redis o no
        """
        
        # ──────────────────────────────────────────
        # PASO 1: Verificar configuración
        # ──────────────────────────────────────────
        redis_url = os.getenv('REDIS_URL')
        force_redis = os.getenv('FORCE_REDIS', 'false').lower() == 'true'
        
        # ──────────────────────────────────────────
        # PASO 2: Inicializar métricas
        # ──────────────────────────────────────────
        if cls._metrics is None:
            cls._metrics = MetricsService(db_manager)
            await cls._metrics.start_monitoring()
        
        # ──────────────────────────────────────────
        # PASO 3: Decidir implementación
        # ──────────────────────────────────────────
        
        # Caso 1: Redis forzado manualmente
        if force_redis and redis_url:
            logger.info("🔴 FORCE_REDIS=true → Using Redis implementation")
            cls._service = ExperimentServiceWithRedis(db_manager, redis_url)
            return cls._service
        
        # Caso 2: Redis disponible Y threshold alcanzado
        if redis_url:
            should_use_redis = await cls._metrics.should_use_redis()
            
            if should_use_redis:
                logger.warning(
                    "🚀 AUTO-SWITCH ACTIVATED: Threshold reached, using Redis implementation"
                )
                
                # Crear servicio con Redis
                cls._service = ExperimentServiceWithRedis(db_manager, redis_url)
                
                # Migrar estado actual a Redis
                await cls._migrate_to_redis(db_manager, cls._service)
                
                return cls._service
            else:
                metrics = await cls._metrics.get_current_metrics()
                logger.info(
                    f"📊 Using PostgreSQL implementation "
                    f"({metrics['last_24h']:,}/{metrics['threshold']:,} req/day)"
                )
        
        # Caso 3: PostgreSQL puro (default)
        if redis_url:
            logger.info("💡 Redis available but threshold not reached - using PostgreSQL")
            logger.info("   → Will auto-switch when reaching 1M requests/day")
        else:
            logger.info("📦 Using PostgreSQL implementation (Redis not configured)")
        
        cls._service = ExperimentService(db_manager)
        return cls._service
    
    @classmethod
    async def _migrate_to_redis(cls, db_manager, redis_service):
        """
        Migrar estado actual de PostgreSQL a Redis
        
        Se ejecuta automáticamente en el primer switch
        """
        logger.info("🔄 Migrating current state to Redis...")
        
        try:
            from data_access.repositories.variant_repository import VariantRepository
            var_repo = VariantRepository(db_manager.pool)
            
            # Obtener todos los experimentos activos
            async with db_manager.pool.acquire() as conn:
                active_experiments = await conn.fetch(
                    """
                    SELECT DISTINCT id 
                    FROM experiments 
                    WHERE status = 'active'
                    """
                )
            
            migrated_count = 0
            
            for exp_row in active_experiments:
                exp_id = str(exp_row['id'])
                
                # Obtener variantes con estado
                variants = await var_repo.get_variants_for_optimization(exp_id)
                
                # Cachear en Redis
                await redis_service._cache_variants_in_redis(exp_id, variants)
                
                migrated_count += len(variants)
                
                logger.info(f"   Migrated experiment {exp_id}: {len(variants)} variants")
            
            logger.info(f"✅ Migration complete: {migrated_count} variants migrated to Redis")
            
        except Exception as e:
            logger.error(f"Migration error: {e}", exc_info=True)
            logger.warning("⚠️  Continuing with empty Redis cache, will populate on demand")
    
    @classmethod
    async def get_metrics(cls):
        """Obtener métricas actuales"""
        if cls._metrics:
            return await cls._metrics.get_current_metrics()
        return {}
    
    @classmethod
    async def shutdown(cls):
        """Shutdown gracefully"""
        if cls._metrics:
            await cls._metrics.stop_monitoring()
