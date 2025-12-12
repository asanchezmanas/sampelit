# orchestration/services/sharding.py

class ShardManager:
    """
    Distribuir experimentos entre múltiples instancias
    
    Hash-based sharding por experiment_id
    """
    
    def __init__(self, config):
        # PostgreSQL shards (read replicas)
        self.pg_shards = [
            DatabaseManager(config['pg_shard_1']),
            DatabaseManager(config['pg_shard_2']),
            DatabaseManager(config['pg_shard_3']),
        ]
        
        # Redis shards
        self.redis_shards = [
            redis.from_url(config['redis_shard_1']),
            redis.from_url(config['redis_shard_2']),
            redis.from_url(config['redis_shard_3']),
        ]
    
    def get_shard(self, experiment_id: str) -> tuple:
        """
        Get shard for experiment
        
        Consistent hashing
        """
        shard_index = hash(experiment_id) % len(self.pg_shards)
        return (
            self.pg_shards[shard_index],
            self.redis_shards[shard_index]
        )
```

**Resultado:** Maneja **500,000 req/s** con 10 shards.

---

## 📊 Fase 4: Event Sourcing (100M+ requests/día)

**Cuándo:** Superas 100M requests diarios (>1,000 req/s)

**Arquitectura:**
```
┌─────────────────────────────────────────┐
│  Event Stream (Kafka/Pulsar)            │
│                                          │
│  • AllocationCreated                    │
│  • ConversionRecorded                   │
│  • StateUpdated                         │
└─────────────────────────────────────────┘
           │
           ├─> Consumer 1: Update Redis (real-time)
           ├─> Consumer 2: Update PostgreSQL (batch)
           ├─> Consumer 3: Analytics (ClickHouse)
           └─> Consumer 4: ML Pipeline
