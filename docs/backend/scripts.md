# 🔧 Scripts de Mantenimiento

**Versión**: 1.0  
**Nivel**: Beginner-friendly 🟢

---

## 📁 Estructura

```
scripts/
├── seed_demo_v1.py       # Crea datos de demo
├── migrate_audit.py      # Migración tabla audit
├── migrate_users.py      # Migración usuarios
├── benchmark_cache.py    # Benchmark Redis vs PG
├── compare_allocators.py # Comparar Thompson vs Sequential
└── demo/                 # Scripts de demo
```

---

## 🌱 seed_demo_v1.py

Crea datos de demostración realistas.

```bash
python scripts/seed_demo_v1.py
```

**Qué hace:**
1. Crea usuario demo (demo@samplit.com / demo123456)
2. Crea 5 experimentos de ejemplo
3. Simula 14 días de tráfico (visitors + conversions)

---

## 🔄 migrate_audit.py

Crea la tabla de auditoría con hash chain.

```bash
python scripts/migrate_audit.py
```

El hash chain garantiza que nadie puede modificar registros históricos.

---

## 📊 benchmark_cache.py

Compara rendimiento de cache.

```bash
python scripts/benchmark_cache.py
```

**Output:**
```
Redis SET: 0.5ms (2000 ops/s)
Redis GET: 0.3ms (3333 ops/s)
PostgreSQL: 2.1ms (476 ops/s)
```

---

## 🔬 compare_allocators.py

Compara Thompson Sampling vs A/B clásico.

```bash
python scripts/compare_allocators.py
```

Demuestra cómo Thompson Sampling:
- Encuentra el ganador más rápido
- Reduce el "regret" (tráfico a variantes perdedoras)
- Maximiza conversiones totales

---

## 📚 Cuándo Usar Cada Script

| Script | Uso |
|--------|-----|
| `seed_demo_v1.py` | Setup inicial, demos a clientes |
| `migrate_*.py` | Instalación, actualizaciones |
| `benchmark_cache.py` | Decisiones de infraestructura |
| `compare_allocators.py` | Educación, validación |

