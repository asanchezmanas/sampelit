# scripts/benchmark_cache.py

"""
Benchmark cache performance

Measures:
- Allocations per second (with/without cache)
- Latency percentiles
- Hit rate
- Memory usage
"""

import asyncio
import time
import statistics
from typing import List
import psutil
import os

from orchestration.services.experiment_service import ExperimentService
from data_access.database import DatabaseManager
from engine.core.cache import get_cache


class AllocationBenchmark:
    """Benchmark allocation performance"""
    
    def __init__(self, service: ExperimentService, experiment_id: str):
        self.service = service
        self.experiment_id = experiment_id
        self.latencies: List[float] = []
    
    async def run_allocation(self, user_id: str) -> float:
        """Run single allocation and measure latency"""
        start = time.perf_counter()
        
        await self.service.allocate_user_to_variant(
            experiment_id=self.experiment_id,
            user_identifier=user_id,
            context={}
        )
        
        latency = (time.perf_counter() - start) * 1000  # ms
        self.latencies.append(latency)
        
        return latency
    
    async def run_benchmark(self, n_allocations: int = 1000):
        """Run full benchmark"""
        print(f"\n🔄 Running {n_allocations} allocations...")
        
        start_time = time.time()
        
        # Run allocations
        tasks = [
            self.run_allocation(f'user_{i}')
            for i in range(n_allocations)
        ]
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Calculate metrics
        throughput = n_allocations / elapsed
        
        p50 = statistics.median(self.latencies)
        p95 = statistics.quantiles(self.latencies, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(self.latencies, n=100)[98]  # 99th percentile
        avg = statistics.mean(self.latencies)
        
        return {
            'n_allocations': n_allocations,
            'elapsed_seconds': elapsed,
            'throughput_per_sec': throughput,
            'latency_avg_ms': avg,
            'latency_p50_ms': p50,
            'latency_p95_ms': p95,
            'latency_p99_ms': p99,
        }


async def benchmark_with_and_without_cache():
    """Compare performance with/without cache"""
    
    # Setup
    db = DatabaseManager()
    await db.connect()
    
    service = ExperimentService(db)
    
    # Create test experiment
    experiment_id = await create_test_experiment(service)
    
    print("="*70)
    print("CACHE PERFORMANCE BENCHMARK")
    print("="*70)
    
    # Benchmark 1: WITHOUT cache (cold start)
    print("\n📊 Benchmark 1: WITHOUT CACHE (cold DB queries)")
    
    cache = get_cache()
    await cache.clear()  # Clear cache
    
    benchmark1 = AllocationBenchmark(service, experiment_id)
    results_no_cache = await benchmark1.run_benchmark(n_allocations=100)
    
    # Benchmark 2: WITH cache (warm cache)
    print("\n📊 Benchmark 2: WITH CACHE (warmed)")
    
    # Warm cache
    variants = await service._fetch_variants_from_db(experiment_id)
    await service.cache.set_variants(experiment_id, variants)
    
    benchmark2 = AllocationBenchmark(service, experiment_id)
    results_with_cache = await benchmark2.run_benchmark(n_allocations=1000)
    
    # Print results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    print(f"\n{'Metric':<30} {'Without Cache':<20} {'With Cache':<20} {'Improvement':<15}")
    print("-"*85)
    
    metrics = [
        ('Throughput (ops/sec)', 'throughput_per_sec', '{:.0f}'),
        ('Avg Latency (ms)', 'latency_avg_ms', '{:.2f}'),
        ('P50 Latency (ms)', 'latency_p50_ms', '{:.2f}'),
        ('P95 Latency (ms)', 'latency_p95_ms', '{:.2f}'),
        ('P99 Latency (ms)', 'latency_p99_ms', '{:.2f}'),
    ]
    
    for label, key, fmt in metrics:
        val_no_cache = results_no_cache[key]
        val_with_cache = results_with_cache[key]
        
        # Calculate improvement
        if 'throughput' in key:
            improvement = (val_with_cache / val_no_cache - 1) * 100
            improvement_str = f"+{improvement:.0f}%"
        else:
            improvement = (1 - val_with_cache / val_no_cache) * 100
            improvement_str = f"-{improvement:.0f}%"
        
        print(
            f"{label:<30} "
            f"{fmt.format(val_no_cache):<20} "
            f"{fmt.format(val_with_cache):<20} "
            f"{improvement_str:<15}"
        )
    
    # Cache metrics
    cache_metrics = cache.get_metrics()
    
    print("\n" + "="*70)
    print("CACHE METRICS")
    print("="*70)
    
    print(f"Hit Rate: {cache_metrics['hit_rate_percent']:.1f}%")
    print(f"Hits: {cache_metrics['hits']}")
    print(f"Misses: {cache_metrics['misses']}")
    print(f"Current Size: {cache_metrics['current_size']}/{cache_metrics['max_size']}")
    
    # Memory usage
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    print(f"\nMemory Usage: {memory_mb:.1f} MB")
    
    print("\n" + "="*70)
    
    await db.disconnect()


async def create_test_experiment(service):
    """Create test experiment for benchmarking"""
    # Implementation depends on your service API
    pass


if __name__ == '__main__':
    asyncio.run(benchmark_with_and_without_cache())
```

**Output esperado:**
```
======================================================================
CACHE PERFORMANCE BENCHMARK
======================================================================

📊 Benchmark 1: WITHOUT CACHE (cold DB queries)
🔄 Running 100 allocations...

📊 Benchmark 2: WITH CACHE (warmed)
🔄 Running 1000 allocations...

======================================================================
RESULTS
======================================================================

Metric                         Without Cache        With Cache           Improvement    
-------------------------------------------------------------------------------------
Throughput (ops/sec)           192                  5847                 +2945%
Avg Latency (ms)               5.21                 0.17                 -97%
P50 Latency (ms)               4.85                 0.15                 -97%
P95 Latency (ms)               8.32                 0.25                 -97%
P99 Latency (ms)               12.45                0.42                 -97%

======================================================================
CACHE METRICS
======================================================================
Hit Rate: 99.9%
Hits: 999
Misses: 1
Current Size: 1/10000

Memory Usage: 45.3 MB

======================================================================
```

**Checklist Día 10:**
```
✅ Integrate cache in ExperimentService
✅ Add cache invalidation on conversion
✅ Create benchmark script
✅ Run benchmark: python scripts/benchmark_cache.py
✅ Document results in docs/performance/cache_benchmark.md
✅ Commit: "perf: integrate cache in experiment service"
```

---

## 🎉 **Fin de Fase 1 (Semana 1-2)**

**Recap de lo logrado:**
```
✅ Factory pattern extensible
✅ Enhanced BaseAllocator con métricas
✅ DB migrations para tracking
✅ Epsilon-Greedy implementado y testeado
✅ UCB (+ UCB1-Tuned) implementado y testeado
✅ Herramienta de comparación de algoritmos
✅ Sistema de cache inteligente (30x speedup)
✅ Benchmarks completos
```

**Métricas de éxito:**
- ✅ 3 algoritmos nuevos funcionando
- ✅ Test coverage > 90%
- ✅ Performance 30x mejor con cache
- ✅ Sistema extensible para futuros algoritmos

---

## 📅 **MES 2: Warm-Start (Semanas 3-6)**

### **Visión General**

**Objetivo:** Usar datos históricos para acelerar aprendizaje de experimentos nuevos.

**Valor de negocio:**
- ⚡ Experimentos convergen 60% más rápido
- 💰 Menos tráfico desperdiciado
- 🎯 Mejor experiencia de usuario (menos traffic a perdedores)

**Arquitectura:**
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  EXPERIMENTO ANTERIOR                                        │
│  ├─ Variant A: 120 conv / 1000 visits (12% CR)             │
│  └─ Variant B: 80 conv / 1000 visits (8% CR)               │
│                                                              │
│  ↓ EXTRACT LEARNINGS                                        │
│                                                              │
│  PRIORS INFORMADOS                                           │
│  ├─ Beta(12, 88) para "similar to A"                       │
│  └─ Beta(8, 92) para "similar to B"                        │
│                                                              │
│  ↓ APPLY TO NEW EXPERIMENT                                  │
│                                                              │
│  EXPERIMENTO NUEVO (con warm-start)                          │
│  ├─ Variant A': Starts with Beta(12, 88)  ← No Beta(1,1)  │
│  └─ Variant B': Starts with Beta(8, 92)                    │
│                                                              │
│  RESULTADO: Aprende en 200 samples vs 500                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
