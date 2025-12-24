# infrastructure/monitoring/health_checks.py

"""
Health Check System

Provides detailed health status for:
- Database connectivity
- Redis connectivity
- Cache performance
- System resources
"""

from typing import Dict, Any, List
from enum import Enum
import asyncio
import psutil
import time
import logging

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Individual health check"""
    
    def __init__(self, name: str, check_func, timeout: float = 5.0):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
    
    async def run(self) -> Dict[str, Any]:
        """Run health check with timeout"""
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_func(),
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            return {
                'name': self.name,
                'status': HealthStatus.HEALTHY,
                'duration_ms': duration * 1000,
                'details': result
            }
        
        except asyncio.TimeoutError:
            return {
                'name': self.name,
                'status': HealthStatus.UNHEALTHY,
                'duration_ms': self.timeout * 1000,
                'error': f'Timeout after {self.timeout}s'
            }
        
        except Exception as e:
            duration = time.time() - start_time
            
            return {
                'name': self.name,
                'status': HealthStatus.UNHEALTHY,
                'duration_ms': duration * 1000,
                'error': str(e)
            }


class HealthCheckService:
    """
    Aggregates multiple health checks
    
    Provides:
    - Individual component status
    - Overall system status
    - Performance metrics
    """
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
    
    def register_check(
        self,
        name: str,
        check_func,
        timeout: float = 5.0
    ):
        """Register a health check"""
        check = HealthCheck(name, check_func, timeout)
        self.checks.append(check)
        logger.info(f"Registered health check: {name}")
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks in parallel
        
        Returns:
            {
                'status': 'healthy' | 'degraded' | 'unhealthy',
                'timestamp': ISO timestamp,
                'checks': [...],
                'summary': {...}
            }
        """
        start_time = time.time()
        
        # Run all checks in parallel
        results = await asyncio.gather(*[
            check.run() for check in self.checks
        ])
        
        total_duration = time.time() - start_time
        
        # Determine overall status
        statuses = [r['status'] for r in results]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        # Count by status
        healthy_count = sum(1 for s in statuses if s == HealthStatus.HEALTHY)
        degraded_count = sum(1 for s in statuses if s == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for s in statuses if s == HealthStatus.UNHEALTHY)
        
        from datetime import datetime
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': results,
            'summary': {
                'total_checks': len(results),
                'healthy': healthy_count,
                'degraded': degraded_count,
                'unhealthy': unhealthy_count,
                'total_duration_ms': total_duration * 1000
            }
        }


# ========================================================================
# STANDARD HEALTH CHECKS
# ========================================================================

async def check_database_health(db_pool) -> Dict[str, Any]:
    """Check database connectivity and performance"""
    
    start = time.time()
    
    async with db_pool.acquire() as conn:
        # Simple query
        await conn.fetchval("SELECT 1")
        
        # Check pool stats
        pool_size = db_pool.get_size()
        pool_free = db_pool.get_idle_size()
    
    query_time = (time.time() - start) * 1000
    
    return {
        'connection_successful': True,
        'query_time_ms': query_time,
        'pool_size': pool_size,
        'pool_free': pool_free,
        'pool_utilization_percent': ((pool_size - pool_free) / pool_size * 100) if pool_size > 0 else 0
    }


async def check_redis_health(redis_client) -> Dict[str, Any]:
    """Check Redis connectivity and performance"""
    
    if not redis_client:
        return {'enabled': False}
    
    start = time.time()
    
    # Ping Redis
    await redis_client.ping()
    
    # Get info
    info = await redis_client.info('stats')
    memory = await redis_client.info('memory')
    
    ping_time = (time.time() - start) * 1000
    
    return {
        'connection_successful': True,
        'ping_time_ms': ping_time,
        'total_keys': await redis_client.dbsize(),
        'memory_used_mb': memory.get('used_memory', 0) / 1024 / 1024,
        'keyspace_hits': info.get('keyspace_hits', 0),
        'keyspace_misses': info.get('keyspace_misses', 0)
    }


async def check_system_resources() -> Dict[str, Any]:
    """Check system resources (CPU, memory, disk)"""
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_available_mb': memory.available / 1024 / 1024,
        'disk_percent': disk.percent,
        'disk_free_gb': disk.free / 1024 / 1024 / 1024
    }


# ========================================================================
# FACTORY FUNCTION
# ========================================================================

def create_health_check_service(
    db_pool,
    redis_client=None
) -> HealthCheckService:
    """
    Create health check service with standard checks
    
    Args:
        db_pool: Database connection pool
        redis_client: Optional Redis client
    
    Returns:
        Configured HealthCheckService
    """
    service = HealthCheckService()
    
    # Register standard checks
    service.register_check(
        'database',
        lambda: check_database_health(db_pool),
        timeout=5.0
    )
    
    if redis_client:
        service.register_check(
            'redis',
            lambda: check_redis_health(redis_client),
            timeout=3.0
        )
    
    service.register_check(
        'system',
        check_system_resources,
        timeout=2.0
    )
    
    return service
