# infrastructure/monitoring/prometheus_metrics.py

"""
Prometheus Metrics Exporter

Expone métricas de la aplicación en formato Prometheus
para monitoreo y alerting.
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    CollectorRegistry, generate_latest,
    CONTENT_TYPE_LATEST
)
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Centralized metrics collector for Samplit
    
    Metrics Categories:
    - Request metrics (throughput, latency)
    - Allocator metrics (selections, conversions)
    - Database metrics (pool, queries)
    - Cache metrics (hit rate, evictions)
    - Business metrics (experiments, variants)
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        # ================================================================
        # REQUEST METRICS
        # ================================================================
        
        self.http_requests_total = Counter(
            'samplit_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'samplit_http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        # ================================================================
        # ALLOCATION METRICS
        # ================================================================
        
        self.allocations_total = Counter(
            'samplit_allocations_total',
            'Total variant allocations',
            ['experiment_id', 'variant_id', 'algorithm'],
            registry=self.registry
        )
        
        self.conversions_total = Counter(
            'samplit_conversions_total',
            'Total conversions',
            ['experiment_id', 'variant_id'],
            registry=self.registry
        )
        
        self.allocation_duration_seconds = Histogram(
            'samplit_allocation_duration_seconds',
            'Allocation decision latency',
            ['algorithm'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
            registry=self.registry
        )
        
        # ================================================================
        # DATABASE METRICS
        # ================================================================
        
        self.db_pool_size = Gauge(
            'samplit_db_pool_size',
            'Database connection pool size',
            registry=self.registry
        )
        
        self.db_pool_available = Gauge(
            'samplit_db_pool_available',
            'Available database connections',
            registry=self.registry
        )
        
        self.db_query_duration_seconds = Histogram(
            'samplit_db_query_duration_seconds',
            'Database query latency',
            ['query_type'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self.registry
        )
        
        self.db_errors_total = Counter(
            'samplit_db_errors_total',
            'Database errors',
            ['error_type'],
            registry=self.registry
        )
        
        # ================================================================
        # CACHE METRICS
        # ================================================================
        
        self.cache_hits_total = Counter(
            'samplit_cache_hits_total',
            'Cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'samplit_cache_misses_total',
            'Cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            'samplit_cache_size',
            'Current cache size',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_evictions_total = Counter(
            'samplit_cache_evictions_total',
            'Cache evictions',
            ['cache_type'],
            registry=self.registry
        )
        
        # ================================================================
        # BUSINESS METRICS
        # ================================================================
        
        self.experiments_active = Gauge(
            'samplit_experiments_active',
            'Number of active experiments',
            registry=self.registry
        )
        
        self.experiments_total = Counter(
            'samplit_experiments_total',
            'Total experiments created',
            ['status'],
            registry=self.registry
        )
        
        self.variants_total = Gauge(
            'samplit_variants_total',
            'Total variants across all experiments',
            registry=self.registry
        )
        
        # ================================================================
        # SYSTEM INFO
        # ================================================================
        
        self.build_info = Info(
            'samplit_build',
            'Build information',
            registry=self.registry
        )
        
        logger.info("Prometheus metrics collector initialized")
    
    # ====================================================================
    # HELPER METHODS
    # ====================================================================
    
    def record_allocation(
        self,
        experiment_id: str,
        variant_id: str,
        algorithm: str,
        duration_seconds: float
    ):
        """Record an allocation event"""
        self.allocations_total.labels(
            experiment_id=experiment_id,
            variant_id=variant_id,
            algorithm=algorithm
        ).inc()
        
        self.allocation_duration_seconds.labels(
            algorithm=algorithm
        ).observe(duration_seconds)
    
    def record_conversion(self, experiment_id: str, variant_id: str):
        """Record a conversion event"""
        self.conversions_total.labels(
            experiment_id=experiment_id,
            variant_id=variant_id
        ).inc()
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration_seconds: float
    ):
        """Record HTTP request"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_seconds)
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        self.cache_hits_total.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        self.cache_misses_total.labels(cache_type=cache_type).inc()
    
    def update_db_pool_stats(self, size: int, available: int):
        """Update database pool metrics"""
        self.db_pool_size.set(size)
        self.db_pool_available.set(available)
    
    def record_db_query(self, query_type: str, duration_seconds: float):
        """Record database query"""
        self.db_query_duration_seconds.labels(
            query_type=query_type
        ).observe(duration_seconds)
    
    def set_build_info(self, version: str, commit: str, build_date: str):
        """Set build information"""
        self.build_info.info({
            'version': version,
            'commit': commit,
            'build_date': build_date
        })
    
    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest(self.registry)


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    
    return _metrics_collector
