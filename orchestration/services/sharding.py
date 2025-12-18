# orchestration/services/sharding.py
"""
Sharding Service - ROADMAP FEATURE

⚠️ NOT IMPLEMENTED YET

Sharding es necesario solo para >100M requests/día.
La arquitectura actual escala bien hasta ese punto usando:
- PostgreSQL con índices optimizados
- Redis opcional para caching
- Connection pooling

STATUS: Roadmap v2.0
PRIORITY: Low (necesario solo en hyper-scale)

Este archivo existe para:
1. Prevenir ImportErrors si algún código lo referencia
2. Documentar claramente que es una feature futura
3. Proporcionar placeholder para implementación futura
"""


class ShardManager:
    """
    Sharding Manager - Placeholder
    
    Distribuir experimentos entre múltiples instancias PostgreSQL
    usando consistent hashing.
    
    EJEMPLO DE USO FUTURO:
    
    ```python
    shard_manager = ShardManager(config={
        'pg_shards': [
            'postgresql://host1/db',
            'postgresql://host2/db',
            'postgresql://host3/db',
        ],
        'redis_shards': [
            'redis://host1:6379',
            'redis://host2:6379',
            'redis://host3:6379',
        ]
    })
    
    # Get shard for experiment
    pg_shard, redis_shard = shard_manager.get_shard(experiment_id)
    
    # Use shard-specific connection
    async with pg_shard.acquire() as conn:
        # ...
    ```
    
    CUANDO IMPLEMENTAR:
    - Traffic > 100M requests/día
    - Database size > 500GB
    - Single PostgreSQL instance hitting limits
    
    IMPLEMENTACIÓN:
    - Usar consistent hashing (hashring)
    - Virtual nodes para balanceo
    - Automatic rebalancing en shard add/remove
    - Cross-shard queries con scatter-gather pattern
    """
    
    def __init__(self, config):
        """
        Initialize sharding (NOT IMPLEMENTED)
        
        Args:
            config: Dict with 'pg_shards' and 'redis_shards'
            
        Raises:
            NotImplementedError: Always (feature not implemented)
        """
        raise NotImplementedError(
            "❌ Sharding no implementado en esta versión.\n\n"
            "La arquitectura actual escala hasta 100M requests/día sin sharding.\n"
            "Si necesitas más capacidad:\n"
            "1. Verifica que estás usando Redis caching\n"
            "2. Optimiza índices de PostgreSQL\n"
            "3. Considera read replicas\n"
            "4. Si aún necesitas sharding, contacta al equipo de arquitectura.\n\n"
            "Roadmap: v2.0 (Q2 2026)"
        )
    
    def get_shard(self, experiment_id: str):
        """
        Get shard for experiment (NOT IMPLEMENTED)
        
        Args:
            experiment_id: Experiment ID
            
        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Sharding not implemented")


# Para compatibilidad con imports
__all__ = ['ShardManager']


# ============================================================================
# NOTAS DE IMPLEMENTACIÓN FUTURA
# ============================================================================

"""
ALGORITMO: Consistent Hashing

1. Hash ring con virtual nodes:
   - Cada shard físico → N nodos virtuales (N=150 recomendado)
   - Distribuye carga uniformemente
   - Minimiza data movement en add/remove

2. Routing:
   - hash(experiment_id) → posición en ring
   - Encontrar siguiente nodo en ring → shard

3. Replication:
   - Primary + 2 replicas en diferentes shards
   - Read from replicas, write to primary
   - Eventual consistency con conflict resolution

EJEMPLO CÓDIGO:

```python
import hashlib
from bisect import bisect_right

class ConsistentHash:
    def __init__(self, nodes, virtual_nodes=150):
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        
        for node in nodes:
            self.add_node(node)
    
    def add_node(self, node):
        for i in range(self.virtual_nodes):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key):
        if not self.ring:
            return None
        
        hash_key = self._hash(key)
        idx = bisect_right(self.sorted_keys, hash_key)
        
        if idx == len(self.sorted_keys):
            idx = 0
        
        return self.ring[self.sorted_keys[idx]]
    
    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
```

MIGRACIÓN:

Cuando implementar sharding:

1. Setup:
   - Deploy N PostgreSQL instances
   - Deploy N Redis instances
   - Configure consistent hashing

2. Migration:
   - Script para mover experiments a shards
   - Basado en hash(experiment_id)
   - Proceso incremental, sin downtime

3. Application changes:
   - ShardManager en ServiceFactory
   - Router layer para cross-shard queries
   - Updated repositories para multi-shard operations

4. Monitoring:
   - Shard balance metrics
   - Cross-shard query latency
   - Rebalancing triggers

COSTO:
- 3 PostgreSQL shards: ~$500/mo cada uno
- 3 Redis shards: ~$100/mo cada uno
- Total: ~$1,800/mo
- Break-even: ~200M requests/mes

ALTERNATIVAS:
Antes de sharding, considerar:
1. Vertical scaling (más CPU/RAM)
2. Read replicas (scale reads)
3. Table partitioning (PostgreSQL nativo)
4. Archive old experiments (reduce DB size)
"""
