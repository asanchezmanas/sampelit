# UI Specs - Experiment Detail

**Archivo**: `experiment_detail_v2.html`  
**Endpoint**: `GET /analytics/experiment/{id}`

---

## Job del Usuario

> "Quiero entender qué variante gana, si puedo confiar en los datos, y qué debo hacer"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Volver                                                           │
│                                                                     │
│  Homepage CTA Test                                     🟢 Activo    │
│  Probando: Texto del botón principal                               │
│  Corriendo desde: 20 Dic (7 días)                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🏆 RESULTADO ACTUAL                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │   Variante B está ganando                                   │   │
│  │   94% de probabilidad de ser mejor que el control           │   │
│  │   ████████████████████████████░░░░                          │   │
│  │   +28% más conversiones                                     │   │
│  │   Equivale a ~€3,400/mes adicionales                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  📊 COMPARACIÓN DE VARIANTES                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CONTROL (Original)                                         │   │
│  │  "Comprar ahora"                                            │   │
│  │  5,234 visitantes → 267 compraron                           │   │
│  │  Conversión: 5.1%                                           │   │
│  │  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░           │   │
│  │                                                             │   │
│  │  VARIANTE B                                        🏆 Líder │   │
│  │  "¡Añadir al carrito!"                                      │   │
│  │  5,198 visitantes → 342 compraron                           │   │
│  │  Conversión: 6.6% (+28% vs control)                         │   │
│  │  █████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  🧠 OPTIMIZACIÓN INTELIGENTE                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Distribución actual del tráfico:                           │   │
│  │  Control      ████████░░░░░░░░░░░░░░░░░░░░  33%             │   │
│  │  Variante B   █████████████████████░░░░░░░  67% ← Ganadora  │   │
│  │                                                             │   │
│  │  💡 67 de cada 100 visitantes ven la mejor versión          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  🎯 RECOMENDACIÓN                                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ✅ Implementar Variante B                                  │   │
│  │  Con 94% de confianza, los datos son suficientes.           │   │
│  │  [Implementar Variante B]     [Seguir probando]             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Mapeo API → UI

### Endpoint: `GET /analytics/experiment/{id}`

```json
{
  "experiment_id": "...",
  "experiment_name": "Homepage CTA Test",
  "status": "active",
  "total_visitors": 10432,
  "total_conversions": 609,
  "overall_conversion_rate": 0.0584,
  "elements": [{
    "id": "...",
    "name": "CTA Button",
    "variants": [
      {
        "id": "...",
        "name": "Control",
        "is_control": true,
        "total_allocations": 5234,
        "total_conversions": 267,
        "conversion_rate": 0.051,
        "win_probability": 0.06,
        "allocation_weight": 0.33
      },
      {
        "id": "...",
        "name": "Variante B",
        "is_control": false,
        "total_allocations": 5198,
        "total_conversions": 342,
        "conversion_rate": 0.066,
        "win_probability": 0.94,
        "allocation_weight": 0.67
      }
    ]
  }],
  "created_at": "2024-12-20T10:00:00Z"
}
```

| Campo API | Componente UI | Formato/Lógica |
|-----------|---------------|----------------|
| `experiment_name` | Título | Directo |
| `status` | Badge | `active` → 🟢 Activo |
| `created_at` | Subtítulo | "Corriendo desde: 20 Dic (7 días)" |
| `variants[].win_probability` | Barra confianza | Mayor → "está ganando" |
| `variants[].conversion_rate` | Tasa | `5.1%` |
| `variants[].allocation_weight` | Barra tráfico | `67%` |

### Cálculos en Frontend

```javascript
// Uplift vs control
const control = variants.find(v => v.is_control);
const uplift = ((variant.conversion_rate - control.conversion_rate) / control.conversion_rate) * 100;
// Resultado: "+28%"

// Días corriendo
const days = Math.floor((Date.now() - new Date(created_at)) / (1000*60*60*24));
// Resultado: "7 días"

// Revenue estimado (si avg_order_value disponible)
const extraConversions = variant.total_conversions - (control.conversion_rate * variant.total_allocations);
const estimatedRevenue = extraConversions * avgOrderValue;
```

---

## Estados de Confianza

| Rango | Color | Estado | Recomendación |
|-------|-------|--------|---------------|
| 95%+ | 🟢 Verde | Ganador claro | "Implementar [Variante]" |
| 80-95% | 🟡 Amarillo | Prometedor | "Esperar ~X días más" |
| 60-80% | 🟠 Naranja | Aprendiendo | "Necesita más datos" |
| <60% | 🔴 Rojo | Sin diferencia | "Variantes muy similares" |

---

## Componente Alpine.js

```javascript
function experimentDetail() {
  return {
    loading: true,
    error: null,
    experiment: null,
    
    async init() {
      const id = new URLSearchParams(location.search).get('id');
      if (!id) { this.error = 'ID no proporcionado'; return; }
      
      try {
        const res = await APIClient.get(`/analytics/experiment/${id}`);
        this.experiment = res.data;
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
    
    get leader() {
      const variants = this.experiment?.elements[0]?.variants || [];
      return variants.reduce((a, b) => 
        a.win_probability > b.win_probability ? a : b
      );
    },
    
    get control() {
      return this.experiment?.elements[0]?.variants.find(v => v.is_control);
    },
    
    getUplift(variant) {
      if (!this.control || variant.is_control) return null;
      return ((variant.conversion_rate - this.control.conversion_rate) 
              / this.control.conversion_rate * 100).toFixed(1);
    },
    
    getRecommendation() {
      const conf = this.leader?.win_probability || 0;
      if (conf >= 0.95) return { action: 'implement', text: 'Implementar ' + this.leader.name };
      if (conf >= 0.80) return { action: 'wait', text: 'Esperar más datos' };
      return { action: 'continue', text: 'Continuar prueba' };
    }
  }
}
```

---

## Acciones del Usuario

| Acción | Endpoint | Resultado |
|--------|----------|-----------|
| Click "Implementar Variante" | `POST /experiments/{id}/complete` | Marca como completado, modal de confirmación |
| Click "Seguir probando" | - | Cierra panel de recomendación |
| Click "Pausar" | `PATCH /experiments/{id}` status=paused | Actualiza estado |
| Click "← Volver" | - | Navega a `experiments_v2.html` |

---

## Sección Colapsable: Detalles Técnicos

```html
<details>
  <summary class="cursor-pointer text-sm text-gray-500">
    🔧 Detalles técnicos (para debugging)
  </summary>
  <div class="mt-4 p-4 bg-gray-50 rounded-xl text-xs font-mono">
    <p>Experiment ID: {id}</p>
    <p>Algorithm: Thompson Sampling</p>
    <p>Prior: Beta(1,1)</p>
    <p>Total samples: {total_visitors}</p>
  </div>
</details>
```

Solo visible para usuarios avanzados. Colapsado por defecto.
