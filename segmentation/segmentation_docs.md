# Segmentación Auto-Adaptativa - Documentación

## 📋 Índice

1. [Qué es](#qué-es)
2. [Cómo funciona](#cómo-funciona)
3. [Instalación](#instalación)
4. [Configuración](#configuración)
5. [Uso desde UI](#uso-desde-ui)
6. [Uso desde API](#uso-desde-api)
7. [Casos de Uso](#casos-de-uso)
8. [Performance](#performance)

---

## 🎯 Qué es

Sistema de segmentación que **automáticamente detecta** si tu experimento tiene suficiente tráfico para segmentar, y te permite:

### Modo 1: Context-Aware (SIEMPRE activo)
- ✅ Captura contexto rico (UTMs, device, geo, time, etc.)
- ✅ Analytics por dimensión
- ✅ Sin requisitos de tráfico

### Modo 2: Segmentación Manual
- ✅ Tú eliges: "Quiero segmentar por source"
- ✅ Thompson Sampling independiente por cada source
- ✅ Requiere: **1,000 visitors/día**

### Modo 3: Clustering Automático
- ✅ Sistema descubre segmentos ocultos con K-means
- ✅ "Instagram mobile users aged 25-34"
- ✅ Requiere: **10,000 visitors/día**

---

## 🔧 Cómo funciona

### Detección Automática

```python
# Cada 6 horas (cron job)
for experiment in active_experiments:
    visitors_per_day = calculate_traffic(experiment)
    
    if visitors_per_day >= 1000 and segmentation_not_enabled:
        # 💡 CREAR RECOMENDACIÓN
        create_recommendation(
            "Tu experimento tiene 1,200 visitors/día. "
            "Segmentación podría mejorar conversión 25%."
        )
    
    if visitors_per_day >= 10000:
        # 💡 SUGERIR CLUSTERING
        create_recommendation(
            "Con 12,500 visitors/día puedes usar auto-clustering "
            "para descubrir segmentos ocultos (+35% lift)."
        )
```

### Auto-Activación (Opcional)

Si el usuario habilita "auto-activation":

```python
if auto_activation_enabled:
    if visitors_per_day >= threshold:
        # ✅ ACTIVAR AUTOMÁTICAMENTE
        enable_segmentation(mode='manual', segment_by=['source'])
        notify_user("Segmentación activada automáticamente!")
```

---

## 📦 Instalación

### 1. Ejecutar Schema

```bash
# Aplicar cambios de base de datos
psql -U postgres -d samplit < schema_segmentation.sql
```

### 2. Instalar dependencias Python

```bash
pip install --break-system-packages scikit-learn==1.3.0
pip install --break-system-packages scipy==1.11.0
pip install --break-system-packages user-agents==2.2.0
```

### 3. Actualizar main.py

```python
# main.py - Añadir router

from public_api.routers import segmentation_config

app.include_router(
    segmentation_config.router,
    prefix=f"{settings.API_PREFIX}/segmentation",
    tags=["Segmentation"]
)
```

### 4. Configurar Cron Job (Eligibility Check)

```python
# scripts/check_eligibility.py

import asyncio
from data_access.database import DatabaseManager, get_database
from orchestration.services.segmentation import EligibilityService

async def check_all_experiments():
    db = await get_database()
    eligibility_service = EligibilityService(db.pool)
    
    # Get all active experiments
    async with db.pool.acquire() as conn:
        experiments = await conn.fetch(
            "SELECT id FROM experiments WHERE status = 'active'"
        )
    
    for exp in experiments:
        exp_id = str(exp['id'])
        
        # Update traffic stats
        await eligibility_service.update_experiment_traffic_stats(exp_id)
        
        # Check auto-activation
        result = await eligibility_service.check_and_auto_activate(exp_id)
        
        if result:
            print(f"✅ Auto-activated segmentation for {exp_id}")

if __name__ == "__main__":
    asyncio.run(check_all_experiments())
```

**Cron (cada 6 horas):**
```bash
0 */6 * * * cd /app && python scripts/check_eligibility.py
```

---

## ⚙️ Configuración

### A. Desde Experiment Creation

```typescript
// Frontend: Create Experiment

const config = {
  name: "Homepage CTA Test",
  variants: [...],
  config: {
    segmentation: {
      enabled: true,
      mode: 'manual',  // 'disabled', 'manual', 'auto'
      segment_by: ['source'],  // o ['source', 'device']
      auto_activation: true,  // Auto-enable cuando llegue a threshold
      auto_activation_threshold: 1000  // visitors/día
    }
  }
};

POST /api/v1/experiments
```

### B. Configurar Después

```typescript
// Dashboard: Segmentation Settings

PUT /api/v1/segmentation/{experiment_id}/config
{
  "mode": "manual",
  "segment_by": ["source"],
  "auto_activation_enabled": true,
  "auto_activation_threshold": 1000
}
```

### C. Ver Recomendaciones

```typescript
GET /api/v1/segmentation/{experiment_id}/recommendations

// Response:
{
  "recommendations": [
    {
      "type": "enable_segmentation",
      "title": "🎯 Enable Segmentation",
      "description": "Your experiment has 1,200 daily visitors across 3 sources. Segmentation could improve conversion by 25%.",
      "expected_lift": 25.0,
      "confidence": 0.8,
      "action": {
        "type": "enable",
        "config": {
          "mode": "manual",
          "segment_by": ["source"]
        }
      }
    }
  ]
}
```

---

## 🎨 Uso desde UI

### Dashboard: Experiment Settings → Segmentation Tab

```
┌──────────────────────────────────────────┐
│  Segmentation Settings                    │
├──────────────────────────────────────────┤
│                                           │
│  Traffic Analysis                         │
│  ├─ Daily Visitors: 1,250                │
│  ├─ Status: ✅ Eligible for Segmentation│
│  └─ Quality: Medium                       │
│                                           │
│  ┌─────────────────────────────────────┐│
│  │ 💡 Recommendation                   ││
│  │                                      ││
│  │ Your experiment qualifies for        ││
│  │ segmentation. Expected improvement:  ││
│  │ +25% conversion                      ││
│  │                                      ││
│  │ [Accept] [Dismiss]                   ││
│  └─────────────────────────────────────┘│
│                                           │
│  Mode:                                    │
│  ( ) Disabled                             │
│  (•) Manual Segmentation                  │
│  ( ) Auto-Clustering                      │
│                                           │
│  Segment By:                              │
│  [x] Source (instagram, google, etc)      │
│  [ ] Device (mobile, desktop)             │
│  [ ] Geography                            │
│                                           │
│  Auto-Activation:                         │
│  [x] Enable when traffic reaches 1000/day │
│                                           │
│  [Save Configuration]                     │
└──────────────────────────────────────────┘
```

### Ver Performance por Segmento

```
┌──────────────────────────────────────────┐
│  Segment Performance                      │
├──────────────────────────────────────────┤
│                                           │
│  Instagram Traffic                        │
│  ├─ Visitors: 450                        │
│  ├─ Conversions: 45                      │
│  └─ CR: 10.0% ⬆️ (+25% vs avg)          │
│                                           │
│  Google Traffic                           │
│  ├─ Visitors: 600                        │
│  ├─ Conversions: 30                      │
│  └─ CR: 5.0% ⬇️ (-38% vs avg)           │
│                                           │
│  Direct Traffic                           │
│  ├─ Visitors: 200                        │
│  ├─ Conversions: 16                      │
│  └─ CR: 8.0% ⬆️ (baseline)              │
│                                           │
└──────────────────────────────────────────┘
```

---

## 🔌 Uso desde API

### 1. Check Eligibility

```bash
GET /api/v1/segmentation/{experiment_id}/eligibility

# Response:
{
  "eligible_for_segmentation": true,
  "eligible_for_clustering": false,
  "avg_daily_visitors": 1250.5,
  "traffic_quality": "medium",
  "recommendations": [...]
}
```

### 2. Enable Segmentation

```bash
PUT /api/v1/segmentation/{experiment_id}/config
Content-Type: application/json

{
  "mode": "manual",
  "segment_by": ["source"],
  "min_samples_per_segment": 100
}
```

### 3. View Segment Performance

```bash
GET /api/v1/segmentation/{experiment_id}/segments

# Response:
[
  {
    "segment_key": "source:instagram",
    "display_name": "Instagram Traffic",
    "allocations": 450,
    "conversions": 45,
    "conversion_rate": 0.10,
    "characteristics": {"source": "instagram"}
  },
  {
    "segment_key": "source:google",
    "display_name": "Google Traffic",
    "allocations": 600,
    "conversions": 30,
    "conversion_rate": 0.05,
    "characteristics": {"source": "google"}
  }
]
```

### 4. Train Clustering Model

```bash
POST /api/v1/segmentation/{experiment_id}/clustering/train

# Response:
{
  "status": "success",
  "n_clusters": 4,
  "algorithm": "kmeans",
  "silhouette_score": 0.45,
  "samples_trained_on": 5000
}
```

### 5. Get Cluster Performance

```bash
GET /api/v1/segmentation/{experiment_id}/segments?type=auto

# Response:
[
  {
    "segment_key": "cluster_0",
    "display_name": "Instagram Mobile Users",
    "conversion_rate": 0.12,
    "characteristics": {
      "source_instagram": 0.9,
      "device_mobile": 0.85,
      "is_weekend": 0.6
    }
  },
  {
    "segment_key": "cluster_1",
    "display_name": "Business Hours Desktop",
    "conversion_rate": 0.08,
    ...
  }
]
```

---

## 💡 Casos de Uso

### Caso 1: E-commerce con múltiples sources

```
Problema:
- Tráfico de Instagram convierte 12%
- Tráfico de Google Ads convierte 4%
- Promedio global: 7%
- Thompson Sampling aprende 7% = pierde oportunidades

Solución:
1. Enable manual segmentation by source
2. Thompson Sampling aprende:
   - Instagram: "Variante B = 12%"
   - Google: "Variante A = 6%"
3. Resultado: Conversion global sube a 9.5% (+35% lift)
```

### Caso 2: SaaS con usuarios de diferentes industrias

```
Problema:
- No sabes a priori qué segmentos existen
- "Usuarios healthcare se comportan diferente a fintech"

Solución:
1. Enable auto-clustering
2. Sistema descubre automáticamente:
   - Cluster 0: Healthcare professionals (CR: 15%)
   - Cluster 1: Fintech startups (CR: 8%)
   - Cluster 2: SMB generalists (CR: 5%)
3. Adapta mensajes por cluster
```

### Caso 3: Newsletter con múltiples listas

```
Contexto: Email marketing
Segmentos: engagement score, subscriber age, list

Configuración:
{
  "channel": "email",
  "mode": "manual",
  "segment_by": ["email_list", "engagement_score"]
}

Resultado:
- Lista "Premium": Subject "Exclusive offer" → 25% open
- Lista "Free": Subject "Limited time" → 18% open
```

---

## 📊 Performance

### Impacto Esperado

| Tráfico | Segmentación | Lift Esperado |
|---------|--------------|---------------|
| <1K/día | Context-aware | +0% (solo insights) |
| 1K-5K/día | Manual | +20-30% |
| 5K-10K/día | Manual + | +25-40% |
| 10K+/día | Auto-clustering | +30-50% |

### Overhead

- **Database**: +3 tablas, ~50MB por 1M assignments
- **API latency**: +5-10ms por request (caching mitigates)
- **Training time**: 2-10s para clustering (async, no bloquea)

### Optimization Tips

```python
# 1. Cache segments aggressively
cache.set(f"variants:{exp_id}:{segment_key}", variants, ttl=60)

# 2. Batch eligibility checks
# No check on every request, sino cada 6h via cron

# 3. Lazy cluster training
# Solo train cuando mode='auto' se activa

# 4. Index optimization
CREATE INDEX idx_assignments_segment_context 
ON assignments(experiment_id, segment_key, (context->>'source'));
```

---

## 🔐 Seguridad

### Estado Thompson Sampling SIEMPRE cifrado

```python
# engine/state/encryption.py

encrypted_state = self.encryptor.encrypt_state({
    'alpha': 5.0,     # ⚠️ NUNCA visible en API
    'beta': 3.0,      # ⚠️ NUNCA visible en API
    'samples': 100
})

# Store in DB as BYTEA
```

### Segmentos NO exponen algoritmo

```json
// ✅ OK - Usuario ve esto:
{
  "segment_key": "source:instagram",
  "conversion_rate": 0.10,
  "allocations": 450
}

// ❌ NUNCA exponer:
{
  "alpha": 5.0,
  "beta": 3.0,
  "thompson_score": 0.625
}
```

---

## 🚀 Next Steps

1. **Phase 1 (Now)**: Deploy context-aware
2. **Phase 2 (2 weeks)**: Manual segmentation UI
3. **Phase 3 (1 month)**: Auto-clustering
4. **Phase 4 (3 months)**: Contextual bandits (advanced)

---

## 📞 Support

- Docs: https://docs.samplit.com/segmentation
- Email: support@samplit.com
- Slack: #segmentation-help
