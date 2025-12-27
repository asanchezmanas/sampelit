# UI Specs - Dashboard

**Archivo**: `index_v2.html`  
**Endpoint**: `GET /analytics/global`

---

## Job del Usuario

> "Quiero saber en 5 segundos si mis experimentos van bien y cuánto dinero estoy ganando"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Buenos días, [Nombre]                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  💰 IMPACTO ESTE MES                                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ +€12,450    │ │ +23%        │ │ 3           │ │ 1 🏆        │   │
│  │ Revenue     │ │ Conversiones│ │ Tests       │ │ Ganador     │   │
│  │ adicional   │ │ vs control  │ │ activos     │ │ listo       │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│                                                                     │
│  📊 TUS EXPERIMENTOS                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Homepage CTA                          🟢 Ganador claro     │   │
│  │  ████████████████████░░░░ 94% confianza                     │   │
│  │  Variante B: +34% conversiones                              │   │
│  │  → Recomendación: IMPLEMENTAR                    [Ver más]  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  💡 ACCIÓN SUGERIDA                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  "Homepage CTA" tiene un ganador claro.                     │   │
│  │  Implementar Variante B podría generar +€4,200/mes          │   │
│  │  [Implementar ahora]                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Mapeo API → UI

### Endpoint: `GET /analytics/global`

```json
// Response
{
  "total_visitors": 24892,
  "total_conversions": 1048,
  "conversion_rate": 0.0421,
  "period": "30d"
}
```

| Campo API | Componente UI | Formato |
|-----------|---------------|---------|
| `total_visitors` | Tarjeta "Total Discovery" | `24,892` (separador miles) |
| `total_conversions` | Tarjeta "Yield Achieved" | `1,048` |
| `conversion_rate` | Tarjeta "Success Ratio" | `4.21%` (×100, 2 decimales) |

### Endpoint: `GET /experiments` (lista)

```json
// Response
{
  "experiments": [
    {
      "id": "...",
      "name": "Homepage CTA",
      "status": "active",
      "bayesian": {
        "leader": { "name": "Variante B", "confidence": 0.94 },
        "is_conclusive": true
      }
    }
  ]
}
```

| Campo API | Componente UI | Lógica |
|-----------|---------------|--------|
| `status` | Badge de estado | `active` → 🟢, `paused` → ⏸️ |
| `bayesian.leader.confidence` | Barra de progreso | Ancho = `confidence × 100%` |
| `bayesian.is_conclusive` | Recomendación | `true` → "IMPLEMENTAR" |

---

## Estados

### Loading
```html
<div class="animate-pulse">
  <div class="h-24 bg-gray-200 rounded-2xl"></div>
</div>
```

### Error
```html
<div class="bg-red-50 text-red-600 p-4 rounded-xl">
  No pudimos cargar tus datos. <button>Reintentar</button>
</div>
```

### Empty (sin experimentos)
```html
<div class="text-center py-12">
  <span class="material-symbols-outlined text-6xl text-gray-300">science</span>
  <h3>Sin experimentos aún</h3>
  <p>Crea tu primer experimento para empezar a optimizar</p>
  <a href="experiments_create_v2.html">Crear experimento</a>
</div>
```

---

## Componente Alpine.js

```javascript
function dashboardData() {
  return {
    loading: true,
    error: null,
    metrics: null,
    experiments: [],
    
    async init() {
      try {
        const [global, exps] = await Promise.all([
          APIClient.get('/analytics/global'),
          APIClient.get('/experiments')
        ]);
        this.metrics = global.data;
        this.experiments = exps.data.experiments;
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    
    // Helpers
    formatNumber(n) {
      return n.toLocaleString('es-ES');
    },
    formatPercent(n) {
      return (n * 100).toFixed(1) + '%';
    },
    getStatusColor(confidence) {
      if (confidence >= 0.95) return 'text-green-600';
      if (confidence >= 0.80) return 'text-yellow-600';
      return 'text-gray-400';
    }
  }
}
```

---

## Acciones del Usuario

| Acción | Resultado |
|--------|-----------|
| Click "Ver más" en experimento | Navega a `experiment_detail_v2.html?id={id}` |
| Click "Implementar ahora" | Abre modal de confirmación |
| Click "Crear experimento" | Navega a `experiments_create_v2.html` |

---

## Métricas a NO Mostrar

- Tiempo de respuesta del servidor
- Número de API calls
- IDs técnicos (UUIDs)
- Timestamps ISO
- Parámetros Bayesianos (alpha, beta)
