# 🔍 Sistema de Auditoría en Tiempo Real

## 📋 Índice

1. [Problema que Resuelve](#problema-que-resuelve)
2. [Arquitectura](#arquitectura)
3. [Qué SÍ se Revela](#qué-sí-se-revela)
4. [Qué NO se Revela](#qué-no-se-revela)
5. [Prueba Criptográfica](#prueba-criptográfica)
6. [Casos de Uso](#casos-de-uso)
7. [Ejemplos](#ejemplos)

---

## 🎯 Problema que Resuelve

### Dilema del AB Testing Adaptativo

```
┌─────────────────────────────────────────────────────────┐
│  CLIENTE quiere:                                        │
│  ✅ Transparencia total                                 │
│  ✅ Poder auditar el algoritmo                          │
│  ✅ Verificar que no hay trampa                         │
│                                                          │
│  PROVEEDOR necesita:                                    │
│  ✅ Proteger propiedad intelectual                      │
│  ✅ Evitar que la competencia copie el algoritmo        │
│  ✅ No revelar parámetros internos                      │
└─────────────────────────────────────────────────────────┘
```

### Solución: "Decision-First Logging"

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  1. ALGORITMO DECIDE → Variante B                           │
│                                                              │
│  2. SE REGISTRA DECISIÓN (con timestamp)                    │
│     "A las 10:30:00 elegí Variante B para user_123"        │
│                                                              │
│  3. USUARIO VE VARIANTE B                                   │
│                                                              │
│  4. USUARIO CONVIERTE (o no)                                │
│                                                              │
│  5. SE REGISTRA RESULTADO (con timestamp)                   │
│     "A las 10:31:23 user_123 convirtió"                    │
│                                                              │
│  ✅ PRUEBA: decision_timestamp < conversion_timestamp       │
│     Por lo tanto, el algoritmo NO vio el resultado          │
│     antes de decidir                                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Key Insight:** No necesitas ver el algoritmo para verificar que funciona honestamente.

---

## 🏗️ Arquitectura

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. DATABASE: algorithm_audit_trail                        │
│     - Registra cada decisión                               │
│     - Blockchain-style hash chain                          │
│     - Inmutable (append-only)                              │
│                                                             │
│  2. SERVICE: AuditService                                  │
│     - log_decision() → registra decisión                   │
│     - log_conversion() → registra resultado                │
│     - verify_integrity() → verifica cadena                 │
│                                                             │
│  3. API: /api/v1/audit/*                                   │
│     - GET /trail → ver decisiones                          │
│     - GET /stats → estadísticas                            │
│     - GET /integrity → verificar                           │
│     - GET /export → exportar CSV                           │
│     - GET /proof-of-fairness → prueba completa             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  CLIENT REQUEST                                               │
│  ↓                                                            │
│  ExperimentService.allocate_user()                            │
│  ↓                                                            │
│  Adaptive Strategy →elige variante                           │
│  ↓                                                            │
│  AuditService.log_decision()  ← REGISTRA AQUÍ               │
│  │                                                            │
│  │  ✅ visitor_id                                            │
│  │  ✅ selected_variant_id                                   │
│  │  ✅ decision_timestamp                                    │
│  │  ✅ decision_hash                                         │
│  │  ❌ alpha, beta (NO se registran)                         │
│  │  ❌ probabilidades (NO se registran)                      │
│  │                                                            │
│  ↓                                                            │
│  RETURN assignment                                            │
│  ↓                                                            │
│  Usuario ve variante                                          │
│  ↓                                                            │
│  Usuario convierte (o no)                                     │
│  ↓                                                            │
│  ExperimentService.record_conversion()                        │
│  ↓                                                            │
│  AuditService.log_conversion()  ← ACTUALIZA AQUÍ            │
│  │                                                            │
│  │  ✅ conversion_observed = true                            │
│  │  ✅ conversion_timestamp                                  │
│  │  ✅ conversion_value                                      │
│  │                                                            │
│  ↓                                                            │
│  VERIFICACIÓN AUTOMÁTICA:                                     │
│  decision_timestamp < conversion_timestamp                    │
│  (si no se cumple → ERROR)                                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## ✅ Qué SÍ se Revela

### 1. Decisiones del Algoritmo

```json
{
  "visitor_id": "user_12345",
  "selected_variant_id": "variant_abc",
  "decision_timestamp": "2024-01-15T10:30:00Z"
}
```

**Por qué está bien:** El cliente DEBE saber qué variante vio cada usuario. Es su derecho.

### 2. Resultados Observados

```json
{
  "conversion_observed": true,
  "conversion_timestamp": "2024-01-15T10:31:23Z",
  "conversion_value": 49.99
}
```

**Por qué está bien:** Son datos del cliente, no nuestros.

### 3. Pruebas de Integridad

```json
{
  "decision_hash": "a4f2b9c1...",
  "previous_hash": "9e8d7c6b...",
  "sequence_number": 1523
}
```

**Por qué está bien:** Prueba que no hay trampa, sin revelar cómo funciona el algoritmo.

### 4. Metadata Pública

```json
{
  "algorithm_version": "adaptive-optimizer-v2.1",
  "decision_to_conversion_seconds": 83.0
}
```

**Por qué está bien:** Info general que no revela implementación.

---

## ❌ Qué NO se Revela

### 1. Parámetros Internos

```python
# ❌ NUNCA se registra:
{
  "alpha": 15.2,
  "beta": 102.8,
  "probability": 0.129
}
```

**Por qué:** Esto ES la propiedad intelectual. Revelar alpha/beta permitiría a la competencia copiar el algoritmo.

### 2. Cálculos Internos

```python
# ❌ NUNCA se registra:
{
  "adaptive_sample": 0.156,
  "expected_value": 0.128,
  "ucb_score": 0.234
}
```

**Por qué:** Estos cálculos son el "secreto" del algoritmo.

### 3. Estado Completo

```python
# ❌ NUNCA se registra:
{
  "variant_states": {
    "A": {"alpha": 10, "beta": 90},
    "B": {"alpha": 15, "beta": 85},
    "C": {"alpha": 12, "beta": 88}
  }
}
```

**Por qué:** Con esta info, la competencia podría replicar el experimento exactamente.

### 4. Contexto Sensible

```python
# ❌ NUNCA se registra:
{
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "cookies": {...}
}
```

**Por qué:** Privacidad. Además, no es necesario para auditoría.

**Qué SÍ hacemos:**

```python
{
  "context_hash": "a4f2b9c1...",  # Hash del contexto
  "user_agent_hash": "9e8d7c6b..."  # Hash del user agent
}
```

Esto permite verificar unicidad sin exponer datos privados.

---

## 🔐 Prueba Criptográfica: Hash Chain

### Concepto: Blockchain para Audit Trail

Cada registro incluye el hash del registro anterior, creando una cadena inmutable.

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  RECORD 1                                                     │
│  ┌─────────────────────────────────────────┐                │
│  │ visitor: user_1                         │                │
│  │ variant: A                              │                │
│  │ timestamp: 10:30:00                     │                │
│  │ previous_hash: NULL (primera entrada)   │                │
│  │ hash: SHA256(user_1 + A + 10:30 + NULL)│                │
│  │     = "a4f2b9c1..."                     │                │
│  └─────────────────────────────────────────┘                │
│                    ↓                                          │
│  RECORD 2                                                     │
│  ┌─────────────────────────────────────────┐                │
│  │ visitor: user_2                         │                │
│  │ variant: B                              │                │
│  │ timestamp: 10:30:05                     │                │
│  │ previous_hash: "a4f2b9c1..."  ← link   │                │
│  │ hash: SHA256(user_2 + B + 10:30:05 + a4f2)│             │
│  │     = "9e8d7c6b..."                     │                │
│  └─────────────────────────────────────────┘                │
│                    ↓                                          │
│  RECORD 3                                                     │
│  ┌─────────────────────────────────────────┐                │
│  │ visitor: user_3                         │                │
│  │ variant: A                              │                │
│  │ timestamp: 10:30:10                     │                │
│  │ previous_hash: "9e8d7c6b..."  ← link   │                │
│  │ hash: SHA256(user_3 + A + 10:30:10 + 9e8d)│             │
│  │     = "3c2b1a0f..."                     │                │
│  └─────────────────────────────────────────┘                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### ¿Qué pasa si alguien intenta hacer trampa?

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  INTENTO DE MODIFICAR RECORD 2                                │
│                                                               │
│  RECORD 2 (modificado)                                        │
│  ┌─────────────────────────────────────────┐                │
│  │ variant: B → C  (cambiado!)            │                │
│  │ previous_hash: "a4f2b9c1..."           │                │
│  │ hash: "9e8d7c6b..." (VIEJO, no cambia)│                │
│  └─────────────────────────────────────────┘                │
│                    ↓                                          │
│  RECORD 3                                                     │
│  ┌─────────────────────────────────────────┐                │
│  │ previous_hash: "9e8d7c6b..." ← NO COINCIDE!│            │
│  │                                          │                │
│  │ El hash de Record 2 ahora sería:        │                │
│  │ SHA256(user_2 + C + ...) = "x1y2z3..."  │                │
│  │                                          │                │
│  │ Pero previous_hash dice "9e8d7c6b..."   │                │
│  │                                          │                │
│  │ ❌ VERIFICACIÓN FALLA                   │                │
│  └─────────────────────────────────────────┘                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Resultado:** Es imposible modificar el pasado sin que se detecte.

### Verificación de Integridad

```sql
-- Función SQL que verifica la cadena
CREATE FUNCTION verify_audit_chain(experiment_id UUID)
RETURNS TABLE (
    sequence_number BIGINT,
    is_valid BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH chain AS (
        SELECT 
            sequence_number,
            decision_hash,
            previous_hash,
            LAG(decision_hash) OVER (ORDER BY sequence_number) 
                as prev_record_hash
        FROM algorithm_audit_trail
        WHERE experiment_id = $1
        ORDER BY sequence_number
    )
    SELECT 
        sequence_number,
        previous_hash = prev_record_hash as is_valid
    FROM chain;
END;
$$ LANGUAGE plpgsql;
```

---

## 📊 Casos de Uso

### 1. Cliente Quiere Auditar

**Escenario:** Cliente sospecha que el algoritmo no es justo.

**Solución:**

```bash
# 1. Obtener audit trail
GET /api/v1/audit/experiments/{id}/trail

# 2. Verificar timestamps
Verificar que TODAS las filas:
decision_timestamp < conversion_timestamp

# 3. Verificar integridad
GET /api/v1/audit/experiments/{id}/integrity

# 4. Exportar a CSV
GET /api/v1/audit/experiments/{id}/export

# 5. Análisis externo
Cliente puede contratar auditor externo para revisar CSV
```

**Qué puede verificar el cliente:**

✅ Todas las decisiones están registradas  
✅ Decisiones se tomaron ANTES de ver conversiones  
✅ No hay alteraciones (hash chain válido)  
✅ No hay decisiones duplicadas  
✅ Sequence numbers son continuos  

**Qué NO puede ver:**

❌ Cómo funciona el algoritmo internamente  
❌ Parámetros Internos  
❌ Probabilidades calculadas  

### 2. Compliance / Regulación

**Escenario:** Auditoría SOC2 o ISO 27001.

**Solución:**

```bash
# Generar prueba de fairness
GET /api/v1/audit/experiments/{id}/proof-of-fairness

Response:
{
  "is_fair": true,
  "checks": {
    "chain_integrity": {"passed": true},
    "timestamp_order": {"passed": true},
    "sequence_continuity": {"passed": true},
    "no_duplicates": {"passed": true}
  },
  "evidence": {
    "total_records": 50000,
    "verification_timestamp": "2024-01-15T15:30:00Z"
  }
}
```

Este JSON puede incluirse en reportes de compliance.

### 3. Comparación con Competencia

**Escenario:** Cliente pregunta "¿Cómo sé que tu algoritmo es mejor que X?"

**Respuesta:**

```
Nosotros:
✅ Audit trail completo
✅ Prueba criptográfica de integridad
✅ API de auditoría en tiempo real
✅ Exportación a CSV
✅ Verificación de fairness

Competidor X:
❌ Solo te muestran resultados finales
❌ No puedes auditar decisiones individuales
❌ No hay prueba de que no hagan trampa
```

### 4. Investigación de Anomalías

**Escenario:** Los resultados no coinciden con expectativas.

**Solución:**

```bash
# 1. Ver estadísticas
GET /api/v1/audit/experiments/{id}/stats

# 2. Ver trail completo
GET /api/v1/audit/experiments/{id}/trail?limit=10000

# 3. Analizar patrones
- ¿Hay sesgo temporal? (ciertas horas)
- ¿Hay visitantes con múltiples asignaciones?
- ¿Hay conversiones sospechosamente rápidas?

# 4. Verificar integridad
GET /api/v1/audit/experiments/{id}/integrity
```

---

## 💡 Ejemplos

### Ejemplo 1: Verificación Manual

```python
import requests
import pandas as pd

# 1. Obtener audit trail
response = requests.get(
    'https://api.samplit.com/v1/audit/experiments/abc-123/export',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

# 2. Cargar en pandas
df = pd.read_csv(response.content)

# 3. Verificar timestamps
invalid = df[
    df['conversion_timestamp'].notna() &
    (df['decision_timestamp'] >= df['conversion_timestamp'])
]

print(f"Registros con timestamps inválidos: {len(invalid)}")
# Esperado: 0

# 4. Verificar secuencia continua
df = df.sort_values('sequence_number')
gaps = df['sequence_number'].diff() > 1

print(f"Gaps en secuencia: {gaps.sum()}")
# Esperado: 0

# 5. Verificar duplicados
duplicates = df.groupby('visitor_id').size()
duplicates = duplicates[duplicates > 1]

print(f"Visitantes con múltiples asignaciones: {len(duplicates)}")
# Esperado: 0 (o justificable si hay re-asignaciones)
```

### Ejemplo 2: Dashboard de Auditoría

```javascript
// React component
function AuditDashboard({ experimentId }) {
  const [stats, setStats] = useState(null);
  const [integrity, setIntegrity] = useState(null);
  
  useEffect(() => {
    // 1. Cargar estadísticas
    fetch(`/api/v1/audit/experiments/${experimentId}/stats`)
      .then(r => r.json())
      .then(setStats);
    
    // 2. Verificar integridad
    fetch(`/api/v1/audit/experiments/${experimentId}/integrity`)
      .then(r => r.json())
      .then(setIntegrity);
  }, [experimentId]);
  
  return (
    <div>
      <h2>Auditoría del Experimento</h2>
      
      {/* Estadísticas */}
      <div>
        <p>Total decisiones: {stats?.total_decisions}</p>
        <p>Conversiones: {stats?.conversions}</p>
        <p>Tasa de conversión: {stats?.conversion_rate}%</p>
      </div>
      
      {/* Estado de integridad */}
      <div>
        <p>Integridad de cadena: 
          {integrity?.is_valid ? '✅ Válida' : '❌ Inválida'}
        </p>
        {!integrity?.is_valid && (
          <div>
            <p>Registros con problemas:</p>
            <ul>
              {integrity.invalid_records.map(r => (
                <li key={r.sequence_number}>
                  Secuencia #{r.sequence_number}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* Botón de exportación */}
      <button onClick={() => {
        window.location.href = 
          `/api/v1/audit/experiments/${experimentId}/export`;
      }}>
        Exportar Audit Trail
      </button>
    </div>
  );
}
```

### Ejemplo 3: Integración con Código Cliente

```typescript
// SDK de Samplit con auditoría integrada
import Samplit from 'samplit-sdk';

const samplit = new Samplit({
  apiKey: 'YOUR_API_KEY',
  audit: {
    enabled: true,  // Activa auditoría automática
    context: {
      include: ['user_agent', 'referer'],  // Se hashearán
      exclude: ['ip_address']  // No se envía por privacidad
    }
  }
});

// Uso normal
const assignment = await samplit.allocate({
  experimentId: 'exp_123',
  visitorId: 'user_456'
});

// ✅ La auditoría se registra automáticamente:
// - decision_timestamp: AHORA
// - selected_variant_id: assignment.variantId
// - context_hash: hash de user_agent + referer

console.log(`Usuario asignado a: ${assignment.variantId}`);

// Más tarde...
await samplit.recordConversion({
  assignmentId: assignment.id,
  value: 49.99
});

// ✅ La conversión se registra automáticamente:
// - conversion_timestamp: AHORA
// - conversion_value: 49.99
```

---

## 🎓 Conclusión

### Resumen

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  CLIENTE obtiene:                                             │
│  ✅ Transparencia total                                       │
│  ✅ Poder de auditoría                                        │
│  ✅ Prueba de que no hay trampa                               │
│  ✅ Exportación de datos                                      │
│  ✅ API en tiempo real                                        │
│                                                               │
│  SAMPLIT protege:                                             │
│  ✅ Algoritmo (propiedad intelectual)                         │
│  ✅ Parámetros internos (alpha, beta)                         │
│  ✅ Lógica de decisión                                        │
│  ✅ Ventaja competitiva                                       │
│                                                               │
│  RESULTADO: Win-Win                                           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Por Qué Funciona

1. **Separación de Concerns:**
   - Decisión (privada) vs Registro (público)
   - Qué eligió (público) vs Cómo eligió (privado)

2. **Prueba Matemática:**
   - decision_timestamp < conversion_timestamp
   - Hash chain inmutable
   - No se necesita ver el algoritmo

3. **Pragmatismo:**
   - Cliente puede auditar sin entender Optimización Adaptativa
   - Competencia no puede copiar sin ver parámetros
   - Cumple regulaciones sin revelar secretos

### Siguiente Paso

Implementar en tu proyecto:

1. Aplicar migrations de DB
2. Integrar AuditService en tu ExperimentService
3. Agregar endpoints a tu API
4. Actualizar SDK cliente
5. Crear dashboard de auditoría

---

**Documentación adicional:**
- API Reference: `/docs/api-audit.md`
- SDK Integration: `/docs/sdk-audit.md`
- Compliance Guide: `/docs/compliance-audit.md`
