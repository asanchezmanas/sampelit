# UI Specs - Experiments List

**Archivo**: `experiments_v2.html`  
**Endpoint**: `GET /api/v1/experiments`

---

## Job del Usuario

> "Quiero ver todos mis experimentos de un vistazo y actuar rápido"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Command Center → Discovery Lab                                    │
│                                                                     │
│  Experiments                                     [+ New Discovery]  │
│  Manage, analyze, and scale your optimization experiments.         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Inventory    Show [10 ▼]                    [🔍 Filter...]       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Name ↕         Status    Traffic    Integrity  Created  Act  │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ 🔬 CTA Test   🟢 Running  12,847     +5.2% ↗    Dec 20   ···  │  │
│  │    /homepage                         4 variants              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ 🔬 Pricing    🟡 Paused   8,234      +2.1% ↗    Dec 15   ···  │  │
│  │    /pricing                          2 variants              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ 📊 Checkout   ✓ Completed 45,000     +12% ↗     Nov 28   ···  │  │
│  │    /checkout                         3 variants              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Showing 1 to 10 of 24 instances   [← 1 2 3 →]                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Mapeo API → UI

### Endpoint: `GET /api/v1/experiments`

**Response:**
```json
{
  "data": [
    {
      "id": "exp_001",
      "name": "CTA Test",
      "url": "https://example.com/homepage",
      "status": "active",
      "total_visitors": 12847,
      "overall_conversion_rate": 0.052,
      "variant_count": 4,
      "created_at": "2024-12-20T10:00:00Z"
    }
  ]
}
```

| Campo API | Componente UI | Formato/Lógica |
|-----------|---------------|----------------|
| `name` | Título fila | Directo |
| `url` | Subtítulo | Solo pathname (`/homepage`) |
| `status` | Badge | `active`→🟢, `paused`→🟡, `completed`→✓, `draft`→🔵 |
| `total_visitors` | Traffic | `12,847` (con separadores) |
| `overall_conversion_rate` | Integrity | `+5.2%` (×100, con signo) |
| `variant_count` | Subtítulo | `4 variants` |
| `created_at` | Created | `Dec 20` (fecha corta) |

---

## Estados de Status

| API Value | UI | Color | Icono |
|-----------|-----|-------|-------|
| `active` | Running | Verde | 🟢 |
| `paused` | Paused | Amarillo | 🟡 |
| `completed` | Completed | Gris | ✓ |
| `draft` | Draft | Azul | 🔵 |

---

## Funcionalidades

### Sorting (Ya implementado)
- Click en header → ordena ascendente
- Click de nuevo → ordena descendente
- Columnas: Name, Status, Traffic, Integrity, Created

### Filtrado (Ya implementado)
- Input de búsqueda filtra por `name` y `url`
- En tiempo real mientras escribe

### Paginación (Ya implementado)
- Selector: 5, 10, 25 por página
- Navegación: Previous, números, Next

---

## Acciones por Fila

| Icono | Acción | Resultado |
|-------|--------|-----------|
| 👁️ | Ver | Navega a `experiment_detail_v2.html?id={id}` |
| ✏️ | Editar | Navega a `experiments_create_v2.html?id={id}` |
| 🗑️ | Eliminar | Modal de confirmación |

---

## Componente Alpine.js (Existente)

```javascript
function experimentsTable() {
  return {
    search: '',
    currentPage: 1,
    perPage: 10,
    sortColumn: 'created',
    sortDirection: 'desc',
    data: [],
    
    async init() {
      this.client = new APIClient();
      await this.fetchExperiments();
    },
    
    async fetchExperiments() {
      try {
        const response = await this.client.get('/experiments');
        this.data = response.data;
      } catch (error) {
        console.error('Failed to fetch experiments:', error);
        this.data = [];
      }
    },
    
    sortBy(column) {
      if (this.sortColumn === column) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortColumn = column;
        this.sortDirection = 'asc';
      }
      this.currentPage = 1;
    },
    
    get sortedData() { /* sorting logic */ },
    get filteredData() { /* filter by search */ },
    get paginatedData() { /* pagination logic */ },
    get totalPages() { /* calculation */ },
    
    prevPage() { if (this.currentPage > 1) this.currentPage--; },
    nextPage() { if (this.currentPage < this.totalPages) this.currentPage++; },
    goToPage(page) { this.currentPage = page; }
  };
}
```

---

## Estado: Empty

```html
<div x-show="data.length === 0" class="text-center py-16">
  <span class="material-symbols-outlined text-6xl text-gray-300">science</span>
  <h3 class="mt-4 text-lg font-bold text-gray-900">No experiments yet</h3>
  <p class="mt-2 text-sm text-gray-500">Create your first experiment to start optimizing</p>
  <a href="experiments_create_v2.html" class="mt-6 inline-flex btn-primary">
    Create First Experiment
  </a>
</div>
```

---

## Estado: Loading

```html
<div x-show="loading" class="animate-pulse">
  <div class="h-16 bg-gray-100 rounded-xl mb-2"></div>
  <div class="h-16 bg-gray-100 rounded-xl mb-2"></div>
  <div class="h-16 bg-gray-100 rounded-xl"></div>
</div>
```

---

## Mejoras Pendientes

- [ ] Añadir estado de error con retry
- [ ] Bulk actions (pausar/eliminar múltiples)
- [ ] Filtros por status (dropdown)
- [ ] Exportar lista a CSV
