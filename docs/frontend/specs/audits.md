# UI Specs - Audits & Downloads (Historial Verificable)

**Archivo**: `audits_v2.html`  
**Endpoints**:
- `GET /api/v1/audit/experiments/{id}/trail` - Lista de decisiones
- `GET /api/v1/audit/experiments/{id}/stats` - Métricas agregadas
- `GET /api/v1/audit/experiments/{id}/proof-of-fairness` - Certificado
- `GET /api/v1/audit/experiments/{id}/export/csv` - Descarga CSV
- `GET /api/v1/audit/experiments/{id}/export/json` - Descarga JSON
- `GET /api/v1/downloads/audit-log/{id}` - CSV/Excel
- `GET /api/v1/downloads/results/{id}` - Reporte Excel completo

---

## Propósito (Transparencia)

> **Cada decisión del algoritmo queda registrada con timestamp, hash y secuencia. El usuario puede descargar y verificar que no hubo manipulación.**

---

## Jobs del Usuario

1. "Quiero ver todas las decisiones que tomó el algoritmo"
2. "Quiero verificar que no se manipularon los datos"
3. "Quiero descargar todo para auditoría interna/externa"
4. "Quiero un certificado de que el proceso fue justo"

---

## Wireframe Principal

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔒 Historial Verificable                                          │
│  Cada decisión registrada. Inmutable. Auditable.                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ✓ INTEGRIDAD VERIFICADA                                     │  │
│  │                                                              │  │
│  │  12,847 decisiones  •  0 violaciones  •  0 gaps             │  │
│  │                                                              │  │
│  │  [📄 Certificado de Fairness]  [📥 Descargar Todo]          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Experimento: [CTA Homepage ▼]                                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  #      Hora       Tipo         Variante    Hash     Estado  │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  12847  09:45:23   Asignación   Var B       a3f2...  ✓       │  │
│  │  12846  09:45:21   Conversión   Var B       b8c1...  ✓       │  │
│  │  12845  09:45:18   Asignación   Var B       d4e9...  ✓       │  │
│  │  12844  09:45:15   Asignación   Control     f7a2...  ✓       │  │
│  │  ...                                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ← Anterior    Página 1 de 128    Siguiente →                      │
│                                                                     │
│  FORMATOS DE DESCARGA:                                             │
│  [CSV] [JSON] [Excel con análisis]                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API: Audit Trail

### `GET /api/v1/audit/experiments/{id}/trail`

**Response:**
```json
[
  {
    "id": "rec_001",
    "visitor_id": "vis_abc123",
    "selected_variant_id": "var_002",
    "segment_key": "default",
    "decision_timestamp": "2024-12-27T09:45:23Z",
    "conversion_observed": true,
    "conversion_timestamp": "2024-12-27T09:47:15Z",
    "conversion_value": 45.00,
    "decision_hash": "a3f2c8d1e9b7...",
    "sequence_number": 12847,
    "algorithm_version": "adaptive-optimizer-v2.1"
  }
]
```

| Campo | UI | Uso |
|-------|-----|-----|
| `sequence_number` | # | Orden cronológico |
| `decision_timestamp` | Hora | Solo hora (HH:MM:SS) |
| `conversion_observed` | Tipo | Si true → "Conversión", else "Asignación" |
| `selected_variant_id` | Variante | Nombre de la variante |
| `decision_hash` | Hash | Primeros 8 caracteres |
| `algorithm_version` | (oculto) | Solo en detalles técnicos |

---

## API: Stats (Métricas Agregadas)

### `GET /api/v1/audit/experiments/{id}/stats`

**Response:**
```json
{
  "total_decisions": 12847,
  "conversions": 687,
  "pending_conversions": 0,
  "conversion_rate": 0.0535,
  "chain_integrity": true,
  "earliest_decision": "2024-12-20T10:00:00Z",
  "latest_decision": "2024-12-27T09:45:23Z"
}
```

---

## API: Proof of Fairness (Certificado)

### `GET /api/v1/audit/experiments/{id}/proof-of-fairness`

**Response:**
```json
{
  "is_fair": true,
  "checks": {
    "chain_integrity": { "passed": true, "total_records": 12847 },
    "temporal_sequence": { "passed": true, "violations": 0 },
    "log_continuity": { "passed": true, "gaps": 0 }
  },
  "evidence": {
    "generated_at": "2024-12-27T09:50:00Z",
    "algorithm": "adaptive-optimizer-v2.1",
    "integrity_hash": "final_abc123..."
  }
}
```

### Certificado UI

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│             🏆 CERTIFICADO DE FAIRNESS                       │
│                                                              │
│  Experimento: CTA Homepage                                   │
│  Generado: 27 Dic 2024, 09:50                                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ✓ Integridad de cadena    12,847 registros válidos   │ │
│  │  ✓ Secuencia temporal      0 violaciones              │ │
│  │  ✓ Continuidad del log     0 gaps                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Hash de integridad: final_abc123...                         │
│                                                              │
│  [📥 Descargar PDF]   [📤 Compartir]                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Descargas Disponibles

| Endpoint | Formato | Contenido |
|----------|---------|-----------|
| `/audit/.../export/csv` | CSV | Audit trail completo |
| `/audit/.../export/json` | JSON | Audit trail estructurado |
| `/downloads/audit-log/{id}?fmt=csv` | CSV | Con headers descriptivos |
| `/downloads/audit-log/{id}?fmt=xlsx` | Excel | Formateado con columnas |
| `/downloads/results/{id}` | Excel | Reporte completo con análisis |

### Contenido del Excel de Resultados

1. **Hoja 1: Resumen**
   - Métricas principales
   - Comparación vs baseline

2. **Hoja 2: Variantes**
   - Tabla de rendimiento por variante
   - Gráfico de conversiones

3. **Hoja 3: Audit Trail**
   - Todos los registros
   - Con timestamps y hashes

4. **Hoja 4: Verificación**
   - Proof of fairness
   - Checks de integridad

---

## Scripts de Demo (`scripts/demo/`)

Para generar datos de demostración:

| Script | Propósito |
|--------|-----------|
| `audit_demo.py` | Demo completo del sistema de auditoría |
| `run_demo_with_audit_trail.py` | Simulación con registro de cada decisión |
| `run_demo_single_element.py` | Demo simple de un elemento |
| `run_demo_multielement.py` | Demo con múltiples elementos |

### Ejemplo de uso:

```bash
# Generar demo con auditoría completa
python scripts/demo/run_demo_with_audit_trail.py

# Salida: audit_trail_export.json, audit_results.xlsx
```

---

## Componente Alpine.js

```javascript
function auditsView() {
  return {
    loading: true,
    experimentId: null,
    trail: [],
    stats: null,
    fairness: null,
    pagination: { page: 1, limit: 50, total: 0 },
    
    async init() {
      this.experimentId = new URLSearchParams(location.search).get('id');
      await Promise.all([
        this.loadTrail(),
        this.loadStats(),
        this.loadFairness()
      ]);
      this.loading = false;
    },
    
    async loadTrail() {
      const res = await APIClient.get(
        `/audit/experiments/${this.experimentId}/trail?limit=${this.pagination.limit}`
      );
      this.trail = res.data;
    },
    
    async loadStats() {
      const res = await APIClient.get(
        `/audit/experiments/${this.experimentId}/stats`
      );
      this.stats = res.data;
    },
    
    async loadFairness() {
      const res = await APIClient.get(
        `/audit/experiments/${this.experimentId}/proof-of-fairness`
      );
      this.fairness = res.data;
    },
    
    // Descargas
    downloadCSV() {
      window.open(`/api/v1/audit/experiments/${this.experimentId}/export/csv`);
    },
    downloadJSON() {
      window.open(`/api/v1/audit/experiments/${this.experimentId}/export/json`);
    },
    downloadExcel() {
      window.open(`/api/v1/downloads/results/${this.experimentId}`);
    },
    
    // Helpers
    formatTime(iso) {
      return new Date(iso).toLocaleTimeString('es-ES');
    },
    truncateHash(hash) {
      return hash.slice(0, 8) + '...';
    },
    getEventType(record) {
      return record.conversion_observed ? 'Conversión' : 'Asignación';
    }
  }
}
```

---

## Verificaciones de Integridad

| Check | Qué verifica | Si falla |
|-------|--------------|----------|
| **Chain Integrity** | Cada hash depende del anterior | Los datos fueron alterados |
| **Temporal Sequence** | Decision timestamp < Conversion timestamp | Conversión retroactiva (fraude) |
| **Log Continuity** | Sequence numbers consecutivos | Registros eliminados |

---

## Por qué es importante

1. **Cumplimiento legal**: GDPR requiere trazabilidad
2. **Confianza del cliente**: Pueden verificar independientemente
3. **Diferenciación**: La mayoría de herramientas NO ofrecen esto
4. **Auditorías externas**: Consultores/inversores lo piden
