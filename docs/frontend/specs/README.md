# UI Specs por Vista

Especificaciones detalladas para cada vista del frontend.  
Cada spec incluye: wireframe, mapeo API → UI, estados, y componente Alpine.js.

---

## Índice

### Vistas Principales

| Vista | Archivo | Spec |
|-------|---------|------|
| Dashboard | `index_v2.html` | [dashboard.md](./dashboard.md) |
| Experiments List | `experiments_v2.html` | [experiments_list.md](./experiments_list.md) |
| Experiment Detail | `experiment_detail_v2.html` | [experiment_detail.md](./experiment_detail.md) |
| Create Experiment | `experiments_create_v2.html` | [experiment_create.md](./experiment_create.md) |
| Analytics | `analytics_v2.html` | [analytics.md](./analytics.md) |
| Audits | `audits_v2.html` | [audits.md](./audits.md) |

### Funcionalidades de Transparencia 🔒

| Vista | Archivo | Spec | Descripción |
|-------|---------|------|-------------|
| Simulator Avanzado | `simulator_v2.html` | [simulator.md](./simulator.md) | CSV + datos sintéticos + documentos verificación |
| Public Dashboard | `/public-dashboard/*` | [public_dashboard.md](./public_dashboard.md) | Demo en vivo con datos reales ofuscados |

---

## Estructura de cada Spec

Cada archivo incluye:

1. **Job del Usuario** - Qué quiere lograr
2. **Wireframe** - ASCII art del layout
3. **Mapeo API → UI** - Qué endpoint usar y cómo transformar datos
4. **Estados** - Loading, Error, Empty
5. **Componente Alpine.js** - Código listo para copiar
6. **Acciones** - Qué pasa cuando el usuario interactúa

---

## Pendientes

- [ ] Visual Editor (`visual_editor_v2.html`)
- [ ] Funnel Builder (`funnel_builder_v2.html`)
