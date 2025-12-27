# UI Specs - Audits (Historial Verificable)

**Archivo**: `audits_v2.html`  
**Endpoint**: `GET /audit/experiments/{id}`

---

## Job del Usuario

> "Quiero ver que las decisiones del sistema son reales y auditables"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔒 Historial Verificable                                          │
│  Todas las decisiones quedan registradas. Nadie puede modificarlas.│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ✓ INTEGRIDAD VERIFICADA                                    │   │
│  │  Total decisiones: 12,847     Estado: Todo correcto ✓       │   │
│  │  [📥 Descargar evidencia]  [🔍 Verificar integridad]        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Experimento: [CTA Homepage ▼]                   Buscar: [____]    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  #     Fecha          Tipo          Detalles         Estado │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  127   09:45:23       Asignación    → Variante B     ✓      │   │
│  │  126   09:45:21       Conversión    → €45.00         ✓      │   │
│  │  125   09:45:18       Asignación    → Variante B     ✓      │   │
│  │  124   09:45:15       Asignación    → Control        ✓      │   │
│  │  123   09:44:58       Conversión    → €89.00         ✓      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ← Anterior    Página 1 de 128    Siguiente →                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Mapeo API → UI

### Endpoint: `GET /audit/experiments/{id}?page=1&limit=50`

**Response:**
```json
{
  "experiment_id": "...",
  "experiment_name": "CTA Homepage",
  "total_events": 12847,
  "integrity_verified": true,
  "events": [
    {
      "id": 127,
      "timestamp": "2024-12-27T09:45:23Z",
      "event_type": "assignment",
      "variant_name": "Variante B",
      "session_id": "sess_abc123",
      "verified": true
    },
    {
      "id": 126,
      "timestamp": "2024-12-27T09:45:21Z",
      "event_type": "conversion",
      "variant_name": "Variante B",
      "value": 45.00,
      "verified": true
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 128,
    "limit": 50
  }
}
```

| Campo API | Componente UI | Formato |
|-----------|---------------|---------|
| `total_events` | Banner | "12,847 decisiones" |
| `integrity_verified` | Badge | ✓ o ⚠️ |
| `events[].timestamp` | Columna Fecha | "09:45:23" (solo hora) |
| `events[].event_type` | Columna Tipo | "Asignación" o "Conversión" |
| `events[].variant_name` | Columna Detalles | "→ Variante B" |
| `events[].value` | Columna Detalles | "→ €45.00" (si conversión) |

---

## Componente Alpine.js

```javascript
function auditsView() {
  return {
    loading: true,
    experiments: [],
    selectedExperiment: null,
    events: [],
    pagination: { page: 1, total_pages: 1 },
    search: '',
    
    async init() {
      // Cargar lista de experimentos
      const res = await APIClient.get('/experiments');
      this.experiments = res.data.experiments;
      if (this.experiments.length > 0) {
        this.selectedExperiment = this.experiments[0].id;
        await this.loadEvents();
      }
      this.loading = false;
    },
    
    async loadEvents() {
      const res = await APIClient.get(
        `/audit/experiments/${this.selectedExperiment}?page=${this.pagination.page}`
      );
      this.events = res.data.events;
      this.pagination = res.data.pagination;
    },
    
    async changePage(delta) {
      this.pagination.page += delta;
      await this.loadEvents();
    },
    
    formatTime(iso) {
      return new Date(iso).toLocaleTimeString('es-ES');
    },
    
    getEventLabel(type) {
      return type === 'assignment' ? 'Asignación' : 'Conversión';
    },
    
    getEventIcon(type) {
      return type === 'assignment' ? 'person_add' : 'paid';
    },
    
    async downloadEvidence() {
      const res = await APIClient.get(
        `/audit/experiments/${this.selectedExperiment}/export`,
        { responseType: 'blob' }
      );
      // Trigger download
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_${this.selectedExperiment}.csv`;
      a.click();
    }
  }
}
```

---

## Tipos de Eventos

| Tipo | Icono | Color | Descripción |
|------|-------|-------|-------------|
| `assignment` | `person_add` | Azul | Usuario asignado a variante |
| `conversion` | `paid` | Verde | Conversión registrada |
| `error` | `warning` | Amarillo | Error en procesamiento |

---

## Filtros

```html
<div class="flex gap-4">
  <!-- Selector de experimento -->
  <select x-model="selectedExperiment" @change="loadEvents()">
    <template x-for="exp in experiments">
      <option :value="exp.id" x-text="exp.name"></option>
    </template>
  </select>
  
  <!-- Búsqueda -->
  <input type="text" 
         x-model="search" 
         placeholder="Buscar por session ID...">
</div>
```

---

## Por Qué Es Importante Esta Vista

Esta vista es clave para:
1. **Confianza**: El cliente ve que los datos son reales
2. **Compliance**: Auditorías internas/externas
3. **Debugging**: Encontrar problemas específicos
4. **Diferenciación**: Pocos competidores ofrecen esto

---

## Banner de Integridad

```html
<div class="p-4 rounded-xl" 
     :class="integrity_verified ? 'bg-green-50' : 'bg-yellow-50'">
  <div class="flex items-center gap-3">
    <span class="material-symbols-outlined text-2xl"
          :class="integrity_verified ? 'text-green-600' : 'text-yellow-600'"
          x-text="integrity_verified ? 'verified' : 'warning'"></span>
    <div>
      <h3 class="font-bold" x-text="integrity_verified ? 'Integridad Verificada' : 'Verificación Pendiente'"></h3>
      <p class="text-sm text-gray-500" x-text="total_events.toLocaleString() + ' decisiones registradas'"></p>
    </div>
  </div>
</div>
```
