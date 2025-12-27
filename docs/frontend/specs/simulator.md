# UI Specs - Simulator Avanzado (Transparencia)

**Archivos**: `simulator_v2.html`, `simulator-landing.html`  
**Endpoints**:
- `POST /api/v1/simulator/forecast` - Proyección con datos personalizados
- `GET /api/v1/simulator/summary` - Simulación rápida
- `POST /api/v1/demo/verify-integrity` - Verificación con CSV

---

## Propósito (Transparencia)

> **El usuario puede probar el algoritmo con SUS propios datos (o sintéticos) y ver exactamente qué pasaría, con documentos verificables.**

---

## Jobs del Usuario

1. "Quiero subir mi CSV de datos históricos y ver qué hubiera pasado"
2. "Quiero simular con datos sintéticos similares a mi negocio"
3. "Quiero un documento que pruebe que el algoritmo funciona"

---

## Wireframe: Simulator Avanzado

```
┌─────────────────────────────────────────────────────────────────────┐
│  🎮 Simulador de Impacto                                           │
│  Prueba el algoritmo con tus datos antes de implementar            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ¿CÓMO QUIERES PROBAR?                                       │  │
│  │                                                              │  │
│  │  ┌────────────────┐     ┌────────────────┐                   │  │
│  │  │ 📊 DATOS       │     │ 🎲 DATOS       │                   │  │
│  │  │    PROPIOS     │     │    SINTÉTICOS  │                   │  │
│  │  │                │     │                │                   │  │
│  │  │ Sube tu CSV    │     │ Configura un   │                   │  │
│  │  │ con histórico  │     │ escenario      │                   │  │
│  │  └────────────────┘     └────────────────┘                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Modo 1: Datos Sintéticos

```
┌─────────────────────────────────────────────────────────────────────┐
│  CONFIGURA TU ESCENARIO                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Número de variantes: [3 ▼]                                        │
│                                                                     │
│  ┌───────────────┬─────────────────┬─────────────────┐             │
│  │  VARIANTE     │  TASA CONVERSIÓN│  TICKET MEDIO   │             │
│  ├───────────────┼─────────────────┼─────────────────┤             │
│  │  Control      │  [====○===] 5%  │  [€____45____]  │             │
│  │  Variante B   │  [======○=] 7%  │  [€____45____]  │             │
│  │  Variante C   │  [===○====] 4%  │  [€____45____]  │             │
│  └───────────────┴─────────────────┴─────────────────┘             │
│                                                                     │
│  Visitantes por día: [○══════════] 1,000                           │
│  Días de prueba: [14]                                              │
│                                                                     │
│  [▶ SIMULAR IMPACTO]                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Request

```json
POST /api/v1/simulator/forecast
{
  "traffic_daily": 1000,
  "baseline_cr": 0.05,
  "uplift": 0.20,
  "confidence_target": 0.95,
  "variants": [
    { "name": "Control", "cr": 0.05, "avg_order_value": 45 },
    { "name": "Variante B", "cr": 0.07, "avg_order_value": 45 },
    { "name": "Variante C", "cr": 0.04, "avg_order_value": 45 }
  ]
}
```

---

## Modo 2: Subir CSV

```
┌─────────────────────────────────────────────────────────────────────┐
│  SUBE TUS DATOS                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │        📁 Arrastra tu CSV aquí o haz click                   │  │
│  │                                                              │  │
│  │        Formato esperado:                                     │  │
│  │        visitor_id, variant, converted, value                 │  │
│  │                                                              │  │
│  │        [Ver ejemplo de CSV]                                  │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ⚠️ Tus datos no se almacenan. Se procesan en memoria y se borran. │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Formato CSV Esperado

```csv
visitor_id,variant,converted,value
v001,Control,0,0
v002,Variante B,1,45
v003,Control,1,89
v004,Variante B,1,45
```

---

## Resultados de Simulación

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 RESULTADO DE LA SIMULACIÓN                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────┐  ┌────────────────────────────┐    │
│  │  📊 TEST TRADICIONAL       │  │  🧠 OPTIMIZACIÓN           │    │
│  │     (50/50/50)             │  │     INTELIGENTE            │    │
│  │                            │  │                            │    │
│  │  Conversiones:    512      │  │  Conversiones:    687      │    │
│  │  Revenue:         €23,040  │  │  Revenue:         €30,915  │    │
│  │                            │  │                            │    │
│  │  Días para decidir: 28     │  │  Días para decidir: 12     │    │
│  └────────────────────────────┘  └────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  💰 IMPACTO NETO                                             │  │
│  │                                                              │  │
│  │  +175 conversiones extra (+34%)                              │  │
│  │  +€7,875 revenue adicional                                   │  │
│  │  -16 días menos para decidir                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  [📥 Descargar Documento de Verificación]  [🔄 Nueva simulación]   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Documento de Verificación (PDF/JSON)

### Endpoint: `POST /api/v1/demo/verify-integrity`

Genera un **Certificado de Transparencia** que incluye:

```json
{
  "integrity_verified": true,
  "protocol_steps": [
    {
      "order": 1,
      "title": "Validación de Datos de Entrada",
      "description": "Se verificó la integridad del CSV y la distribución de datos",
      "evidence": {
        "total_rows": 10000,
        "variants_detected": 3,
        "conversion_rate_by_variant": {...}
      }
    },
    {
      "order": 2,
      "title": "Aislamiento del Algoritmo",
      "description": "El algoritmo NO tiene acceso previo a los resultados finales",
      "evidence": {
        "blind_processing": true,
        "no_lookahead": true
      }
    },
    {
      "order": 3,
      "title": "Ejecución Paso a Paso",
      "description": "Cada decisión del algoritmo está registrada",
      "evidence": {
        "decisions_logged": 10000,
        "traffic_allocation_evolution": [...]
      }
    }
  ],
  "performance_benchmark": {
    "traditional": { "conversions": 512, "revenue": 23040 },
    "optimized": { "conversions": 687, "revenue": 30915 },
    "uplift_percent": 34
  }
}
```

---

## Componente Alpine.js

```javascript
function simulatorAdvanced() {
  return {
    mode: 'synthetic', // 'synthetic' | 'csv'
    loading: false,
    results: null,
    
    // Synthetic mode
    variants: [
      { name: 'Control', cr: 5, aov: 45 },
      { name: 'Variante B', cr: 7, aov: 45 }
    ],
    trafficDaily: 1000,
    days: 14,
    
    // CSV mode
    csvFile: null,
    
    addVariant() {
      const letter = String.fromCharCode(65 + this.variants.length);
      this.variants.push({ name: `Variante ${letter}`, cr: 5, aov: 45 });
    },
    
    async runSynthetic() {
      this.loading = true;
      const res = await APIClient.post('/simulator/forecast', {
        traffic_daily: this.trafficDaily,
        variants: this.variants.map(v => ({
          name: v.name,
          cr: v.cr / 100,
          avg_order_value: v.aov
        }))
      });
      this.results = res.data;
      this.loading = false;
    },
    
    async runCSV(file) {
      this.loading = true;
      const formData = new FormData();
      formData.append('matrix', file);
      formData.append('session_logs', file); // Simplified
      
      const res = await APIClient.post('/demo/verify-integrity', formData);
      this.results = res.data;
      this.loading = false;
    },
    
    async downloadCertificate() {
      const blob = new Blob([JSON.stringify(this.results, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'samplit_verification_certificate.json';
      a.click();
    }
  }
}
```

---

## Principios de Transparencia

| Principio | Cómo se implementa |
|-----------|-------------------|
| **No almacenamos datos** | CSV se procesa en memoria, se borra al terminar |
| **Algoritmo ciego** | No tiene acceso a resultados futuros |
| **Todo documentado** | Cada paso genera evidence exportable |
| **Reproducible** | Mismo input → mismo output |
