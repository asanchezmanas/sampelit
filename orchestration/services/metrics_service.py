# orchestration/services/metrics_service.py
"""
Servicio de Métricas y Auto-Scaling

Cuenta requests y decide cuándo activar Redis
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Contador de requests con detección de threshold
    
    Propósito:
    - Contar requests/día
    - Detectar cuándo superar 1M/día
    - Triggear auto-switch a Redis
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self._daily_count = 0
        self._last_reset = datetime.now()
        self._threshold_reached = False
        
        # Configuración
        self.DAILY_THRESHOLD = 1_000_000  # 1M requests/día
        self.CHECK_INTERVAL = 3600  # Verificar cada hora
        
        # Estado
        self._monitoring_task = None
    
    async def start_monitoring(self):
        """
        Iniciar monitoreo en background
        
        Corre cada hora para:
        - Contar requests del día
        - Verificar threshold
        - Actualizar métricas en BD
        """
        logger.info("🔍 Starting metrics monitoring...")
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Detener monitoreo"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Loop de monitoreo"""
        while True:
            try:
                await asyncio.sleep(self.CHECK_INTERVAL)
                await self._check_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics monitoring error: {e}", exc_info=True)
    
    async def _check_metrics(self):
        """
        Verificar métricas y detectar threshold
        """
        try:
            # Contar requests de las últimas 24h
            async with self.db.pool.acquire() as conn:
                daily_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) 
                    FROM assignments 
                    WHERE assigned_at >= NOW() - INTERVAL '24 hours'
                    """
                )
            
            self._daily_count = daily_count
            
            logger.info(f"📊 Daily requests: {daily_count:,}")
            
            # ──────────────────────────────────────────
            # Detectar threshold
            # ──────────────────────────────────────────
            if daily_count >= self.DAILY_THRESHOLD and not self._threshold_reached:
                logger.warning(
                    f"🚨 THRESHOLD REACHED! "
                    f"Daily requests: {daily_count:,} >= {self.DAILY_THRESHOLD:,}"
                )
                
                self._threshold_reached = True
                
                # Guardar en BD para persistencia
                await self._save_threshold_event()
                
                logger.info("✅ Redis auto-switch will activate on next restart")
            
            # Calcular proyección
            hours_passed = 24  # Últimas 24h
            projected_daily = daily_count
            
            if projected_daily > self.DAILY_THRESHOLD * 0.8:  # 80% del threshold
                logger.warning(
                    f"⚠️  Approaching threshold: {projected_daily:,} "
                    f"({projected_daily/self.DAILY_THRESHOLD*100:.1f}%)"
                )
            
            # Guardar métricas
            await self._save_metrics(daily_count)
            
        except Exception as e:
            logger.error(f"Check metrics error: {e}", exc_info=True)
    
    async def _save_threshold_event(self):
        """
        Guardar evento de threshold alcanzado
        
        Esto persiste la decisión de usar Redis
        """
        try:
            async with self.db.pool.acquire() as conn:
                # Crear tabla si no existe
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id SERIAL PRIMARY KEY,
                        metric_type VARCHAR(50) NOT NULL,
                        metric_value BIGINT,
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
                
                # Insertar evento
                await conn.execute(
                    """
                    INSERT INTO system_metrics (metric_type, metric_value, metadata)
                    VALUES ('threshold_reached', $1, $2)
                    """,
                    self._daily_count,
                    json.dumps({
                        'threshold': self.DAILY_THRESHOLD,
                        'actual': self._daily_count,
                        'recommendation': 'enable_redis'
                    })
                )
                
                logger.info("💾 Threshold event saved to database")
                
        except Exception as e:
            logger.error(f"Save threshold event error: {e}")
    
    async def _save_metrics(self, daily_count: int):
        """Guardar métricas del día"""
        try:
            async with self.db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO system_metrics (metric_type, metric_value, metadata)
                    VALUES ('daily_requests', $1, $2)
                    """,
                    daily_count,
                    json.dumps({'timestamp': datetime.now().isoformat()})
                )
        except Exception as e:
            logger.error(f"Save metrics error: {e}")
    
    async def should_use_redis(self) -> bool:
        """
        Verificar si deberíamos usar Redis
        
        Returns:
            True si hemos superado threshold
        """
        try:
            async with self.db.pool.acquire() as conn:
                # Verificar si alguna vez alcanzamos threshold
                threshold_event = await conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM system_metrics 
                        WHERE metric_type = 'threshold_reached'
                        ORDER BY created_at DESC
                        LIMIT 1
                    )
                    """
                )
                
                return threshold_event or self._threshold_reached
                
        except Exception as e:
            logger.error(f"Check Redis requirement error: {e}")
            return False
    
    async def get_current_metrics(self) -> Dict:
        """
        Obtener métricas actuales
        
        Para dashboard/monitoring
        """
        try:
            async with self.db.pool.acquire() as conn:
                # Últimas 24h
                last_24h = await conn.fetchval(
                    """
                    SELECT COUNT(*) 
                    FROM assignments 
                    WHERE assigned_at >= NOW() - INTERVAL '24 hours'
                    """
                )
                
                # Última hora
                last_hour = await conn.fetchval(
                    """
                    SELECT COUNT(*) 
                    FROM assignments 
                    WHERE assigned_at >= NOW() - INTERVAL '1 hour'
                    """
                )
                
                # Proyección diaria basada en última hora
                projected = last_hour * 24
                
                return {
                    'last_24h': last_24h,
                    'last_hour': last_hour,
                    'projected_daily': projected,
                    'threshold': self.DAILY_THRESHOLD,
                    'threshold_percentage': (last_24h / self.DAILY_THRESHOLD * 100),
                    'redis_recommended': last_24h >= self.DAILY_THRESHOLD,
                    'redis_activated': self._threshold_reached
                }
                
        except Exception as e:
            logger.error(f"Get metrics error: {e}")
            return {}
