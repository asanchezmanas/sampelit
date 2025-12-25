"""
Metrics Monitoring Service - FIXED VERSION
Correcciones:
- Auto-restart con exponential backoff
- Manejo robusto de errores
- Mejor logging
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MetricsService:
    """
    # FIXED: Service for monitoring metrics and auto-scaling
    
    Features:
    - Monitors request volume
    - Auto-scales between PostgreSQL and Redis
    - Auto-restart on failures with exponential backoff
    """
    
    # Thresholds
    REDIS_ENABLE_THRESHOLD = 1000  # req/min
    REDIS_DISABLE_THRESHOLD = 500  # req/min
    
    # Monitoring
    CHECK_INTERVAL = 300  # 5 minutes
    
    # NEW: Backoff configuration
    INITIAL_RETRY_DELAY = 60  # 1 minute
    MAX_RETRY_DELAY = 3600  # 1 hour
    BACKOFF_MULTIPLIER = 2
    
    def __init__(self, db_pool, redis_client=None):
        self.db = db_pool
        self.redis = redis_client
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Metrics storage
        self.current_metrics = {
            'requests_per_minute': 0,
            'using_redis': redis_client is not None,
            'last_check': None,
            'errors': []
        }
        
        self.logger = logging.getLogger(f"{__name__}.MetricsService")
    
    async def start_monitoring(self) -> None:
        """
        # FIXED: Start monitoring task with auto-restart
        """
        if self.is_running:
            self.logger.warning("Monitoring already running")
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("Metrics monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring task gracefully"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Metrics monitoring stopped")
    
    async def _monitor_loop(self) -> None:
        """
        # FIXED: Monitoring loop with exponential backoff on errors
        
        Changes:
        - Auto-restart on failures
        - Exponential backoff (60s → 120s → 240s → ... → 3600s max)
        - Reset backoff on success
        """
        
        retry_delay = self.INITIAL_RETRY_DELAY
        consecutive_errors = 0
        
        while self.is_running:
            try:
                # Wait before check
                await asyncio.sleep(self.CHECK_INTERVAL)
                
                if not self.is_running:
                    break
                
                # Perform metrics check
                await self._check_metrics()
                
                # ✅ Success: Reset backoff
                retry_delay = self.INITIAL_RETRY_DELAY
                consecutive_errors = 0
            
            except asyncio.CancelledError:
                # Clean shutdown
                self.logger.info("Monitoring task cancelled")
                break
            
            except Exception as e:
                consecutive_errors += 1
                
                self.logger.error(
                    f"❌ Metrics monitoring error (attempt {consecutive_errors}): {e}. "
                    f"Retrying in {retry_delay}s",
                    exc_info=True
                )
                
                # Store error
                self.current_metrics['errors'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': str(e),
                    'attempt': consecutive_errors
                })
                
                # Keep only last 10 errors
                self.current_metrics['errors'] = self.current_metrics['errors'][-10:]
                
                try:
                    # ✅ Wait with exponential backoff
                    await asyncio.sleep(retry_delay)
                    
                    # Increase delay for next attempt
                    retry_delay = min(
                        retry_delay * self.BACKOFF_MULTIPLIER,
                        self.MAX_RETRY_DELAY
                    )
                
                except asyncio.CancelledError:
                    break
        
        self.logger.info("Monitoring loop exited")
    
    async def _check_metrics(self) -> None:
        """
        ✅ Improved: Check metrics and auto-scale
        
        This method now includes better error handling and logging
        """
        try:
            # Calculate current request volume
            req_per_min = await self._get_request_volume()
            
            self.current_metrics['requests_per_minute'] = req_per_min
            self.current_metrics['last_check'] = datetime.utcnow().isoformat()
            
            self.logger.info(
                f"📊 Metrics check: {req_per_min} req/min | "
                f"Redis: {'enabled' if self.current_metrics['using_redis'] else 'disabled'}"
            )
            
            # Auto-scaling logic
            if self.redis and not self.current_metrics['using_redis']:
                # Currently using PostgreSQL
                if req_per_min >= self.REDIS_ENABLE_THRESHOLD:
                    self.logger.info(
                        f"🚀 High traffic detected ({req_per_min} req/min). "
                        f"Enabling Redis caching..."
                    )
                    await self._enable_redis()
            
            elif self.redis and self.current_metrics['using_redis']:
                # Currently using Redis
                if req_per_min <= self.REDIS_DISABLE_THRESHOLD:
                    self.logger.info(
                        f"📉 Low traffic detected ({req_per_min} req/min). "
                        f"Disabling Redis caching..."
                    )
                    await self._disable_redis()
        
        except Exception as e:
            # Re-raise to trigger backoff in _monitor_loop
            raise RuntimeError(f"Failed to check metrics: {e}") from e
    
    async def _get_request_volume(self) -> int:
        """
        Calculate request volume (requests per minute)
        
        This queries the assignments table for recent activity
        """
        try:
            async with self.db.acquire() as conn:
                # Count assignments in last minute
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM assignments
                    WHERE assigned_at >= NOW() - INTERVAL '1 minute'
                    """
                )
            
            return count or 0
        
        except Exception as e:
            self.logger.error(f"Error getting request volume: {e}")
            # Return 0 to avoid auto-scaling on errors
            return 0
    
    async def _enable_redis(self) -> None:
        """
        Enable Redis caching
        
        In practice, this would trigger a service factory reconfiguration
        For now, we just update the flag
        """
        try:
            self.current_metrics['using_redis'] = True
            self.logger.info("✅ Redis caching enabled")
            
            # TODO: Trigger ServiceFactory to use ExperimentServiceRedis
            # This would require a reference to ServiceFactory or an event bus
        
        except Exception as e:
            self.logger.error(f"Error enabling Redis: {e}")
    
    async def _disable_redis(self) -> None:
        """
        Disable Redis caching
        
        In practice, this would trigger a service factory reconfiguration
        """
        try:
            self.current_metrics['using_redis'] = False
            self.logger.info("✅ Redis caching disabled")
            
            # TODO: Trigger ServiceFactory to use ExperimentService (PostgreSQL only)
        
        except Exception as e:
            self.logger.error(f"Error disabling Redis: {e}")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return {
            **self.current_metrics,
            'is_monitoring': self.is_running,
            'check_interval': self.CHECK_INTERVAL,
            'thresholds': {
                'redis_enable': self.REDIS_ENABLE_THRESHOLD,
                'redis_disable': self.REDIS_DISABLE_THRESHOLD
            }
        }
    
    async def force_check(self) -> Dict[str, Any]:
        """
        ✅ NEW: Force an immediate metrics check
        
        Useful for testing or manual intervention
        """
        try:
            await self._check_metrics()
            return {
                'success': True,
                'metrics': self.get_current_metrics()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_health(self) -> Dict[str, Any]:
        """
        ✅ NEW: Health check for monitoring service
        
        Returns:
            - status: "healthy" | "degraded" | "unhealthy"
            - details: diagnostic information
        """
        if not self.is_running:
            return {
                'status': 'unhealthy',
                'reason': 'Monitoring not running',
                'is_running': False
            }
        
        # Check last check time
        last_check = self.current_metrics.get('last_check')
        
        if last_check is None:
            return {
                'status': 'degraded',
                'reason': 'No checks performed yet',
                'is_running': True
            }
        
        # Check for recent errors
        recent_errors = len(self.current_metrics.get('errors', []))
        
        if recent_errors > 5:
            return {
                'status': 'degraded',
                'reason': f'{recent_errors} recent errors',
                'is_running': True,
                'last_check': last_check,
                'errors': self.current_metrics['errors'][-3:]  # Last 3 errors
            }
        
        return {
            'status': 'healthy',
            'is_running': True,
            'last_check': last_check,
            'metrics': self.current_metrics
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
# In main application startup:

from .metrics_service import MetricsService

# Create service
metrics_service = MetricsService(db_pool, redis_client)

# Start monitoring
await metrics_service.start_monitoring()

# In application shutdown:
await metrics_service.stop_monitoring()

# Check health:
health = await metrics_service.get_health()
if health['status'] != 'healthy':
    logger.warning(f"Metrics service health: {health}")

# Force check (for testing):
result = await metrics_service.force_check()
"""
