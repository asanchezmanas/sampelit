# 🔍 Verificación Optimización Adaptativa + Auditoría

## 📄 Script Actualizado: `verify_flow.py`

Este script ahora incluye **verificación completa del sistema de auditoría** además de la verificación de la Optimización Adaptativa.

---

## ✨ Qué Hay de Nuevo

### Verificaciones Adicionales

1. **✅ Audit Trail Integrado**
   - Registra cada decisión del algoritmo
   - Verifica hash chain criptográfico
   - Comprueba orden temporal de eventos

2. **✅ Demostración de Transparencia**
   - Muestra exactamente qué se registra
   - Muestra exactamente qué NO se registra
   - Prueba que no se revela propiedad intelectual

3. **✅ Verificación de Integridad**
   - Chain integrity (hash links)
   - Timestamp order (decision < conversion)
   - Sequence continuity (no gaps)

4. **✅ Comparación Backend vs Audit**
   - Verifica que los números coinciden
   - PostgreSQL vs Audit Trail
   - Conversiones en ambos sistemas

---

## 🎯 Lo Que Verifica

### Optimización Adaptativa (Original)

```
✅ Estado inicial (priors 1,1)
✅ Encriptación/desencriptación
✅ Allocator usa estado de BD
✅ Algoritmo aprende de conversiones
✅ Tráfico se optimiza automáticamente
```

### Sistema de Auditoría (NUEVO)

```
✅ Decisiones se registran ANTES de resultados
✅ Hash chain inmutable
✅ Timestamps correctos (decision < conversion)
✅ Sequence numbers continuos
✅ NO se registra alpha/beta/probabilidades
✅ Comparación backend vs audit coincide
```

---

## 🚀 Cómo Ejecutar

### Pre-requisitos

```bash
# 1. PostgreSQL corriendo
systemctl status postgresql

# 2. Base de datos creada
createdb samplit

# 3. Migrations aplicadas
psql -U postgres -d samplit -f migrations/001_initial_schema.sql
```

### Ejecutar Script

```bash
# Desde raíz del proyecto
python scripts/verify_flow.py

# O desde outputs
python /mnt/user-data/outputs/verify_flow.py
```

---

## 📊 Output Esperado

### Paso 1-5: Setup y Estado Inicial
```
[1/12] Conectando a base de datos...
     ✅ Conexión establecada
     
[2/12] Creando usuario de prueba...
     ✅ Usuario creado: a1b2c3d4...
     
[3/12] Creando experimento con 3 variantes...
     ✅ Experimento creado: e5f6g7h8...
     ✅ Variantes creadas: 3
     
[4/12] Activando experimento...
     ✅ Status: active
     
[5/12] Verificando estado inicial de optimización adaptativa...
     Estado inicial (priors):
       • Variant A: alpha=1.0, beta=1.0
       • Variant B: alpha=1.0, beta=1.0
       • Variant C: alpha=1.0, beta=1.0
     ✅ Todos tienen priors (1,1) - Correcto!
```

### Paso 6-7: Auditoría Inicial
```
[6/12] Simulando 30 visitantes con AUDITORÍA...
     → ExperimentService.allocate_user_to_variant()
     → El motor adaptativo decide (PRIVADO)
     ✨ AuditService.log_decision() registra (PÚBLICO)
     → Solo registra: visitor_id, variant_id, timestamp
     → NO registra: alpha, beta, probabilidades
     ✅ 30 visitantes asignados
     ✅ 30 decisiones registradas en audit trail
     
[7/12] Verificando audit trail inicial...
     Verificación de integridad:
       ✅ chain_integrity: PASSED
       ✅ timestamp_order: PASSED
       ✅ sequence_continuity: PASSED
     ✅ Audit trail VÁLIDO (30 registros)
     
     Ejemplo de registro en audit trail:
       ✅ visitor_id: visitor_0
       ✅ variant_id: abc12345...
       ✅ decision_timestamp: 2025-12-19T09:30:00.123Z
       ✅ decision_hash: a4f2b9c1e8d7f6a5...
       ✅ sequence_number: 0
       ❌ (NO hay alpha, beta, ni probabilidades)
```

### Paso 8-9: Aprendizaje
```
[8/12] Simulando 15 conversiones en Variant B...
     → ExperimentService.record_conversion()
     → Actualiza motor adaptativo (PRIVADO)
     ✨ AuditService.log_conversion() registra (PÚBLICO)
     → Solo registra: conversion_timestamp
     → Verifica: decision_timestamp < conversion_timestamp
     ✅ 15 conversiones en Variant B
     ✅ 15 conversiones en audit trail
     
[9/12] Verificando que la optimización adaptativa aprendió...
     Estado adaptativo DESPUÉS de conversiones:
       • Variant A: alpha=  1.0, beta= 15.0, score=0.062
       • Variant B: alpha= 16.0, beta=  5.0, score=0.762  👈
       • Variant C: alpha=  1.0, beta= 12.0, score=0.077
     ✅ Variant B tiene score alto (0.762) - Correcto!
```

### Paso 10-11: Verificación Completa
```
[10/12] Verificando audit trail completo...
     Total de registros: 45
     Conversiones registradas: 15
     Conversion rate: 33.33%
     
     Verificación de integridad:
       ✅ chain_integrity
       ✅ timestamp_order
       ✅ sequence_continuity
     ✅ Audit trail mantiene integridad criptográfica
     
[11/12] Simulando 50 visitantes adicionales...
     El motor adaptativo debería enviar MÁS tráfico a Variant B
     → Cada decisión se registra en audit trail
     ✅ 50 visitantes asignados + registrados
     
     Distribución DESPUÉS de aprendizaje:
          Variant A:  5/50 (10.0%) ███
          Variant B: 38/50 (76.0%) ███████████████████  👈
          Variant C:  7/50 (14.0%) ████
```

### Paso 12: Resultado Final
```
[12/12] Evaluando resultado final...
     Variant B recibió: 38/50 visitas (76.0%)
     
     Audit Trail Final:
       Total registros: 95
       Conversiones: 15
       Integridad: ✅ VÁLIDA

╔══════════════════════════════════════════════════════════════╗
║                ✅ VERIFICACIÓN EXITOSA                       ║
╚══════════════════════════════════════════════════════════════╝

  Optimización Adaptativa + Auditoría funcionan CORRECTAMENTE:
    • Variant B recibió 38/50 visitas (76.0%)
    • El algoritmo aprendió de las conversiones
    • El estado se guarda/carga correctamente
    • ✨ Audit trail con 95 registros
    • ✨ Integridad criptográfica verificada
    • ✨ Sin revelar alpha/beta/probabilidades

  🎉 Todo el flujo funciona correctamente!
```

### Estadísticas Finales
```
────────────────────────────────────────────────────────────────
📊 ESTADÍSTICAS FINALES
────────────────────────────────────────────────────────────────

Backend (PostgreSQL):
  Total visitantes: 95
  Total conversiones: 15
  CR global: 15.79%

Por variante:
  Variant B      :  63 visits (66.3%) | 15 conv | CR: 23.81%  👈
  Control (A)    :  18 visits (18.9%) |  0 conv | CR: 0.00%
  Variant C      :  14 visits (14.7%) |  0 conv | CR: 0.00%

Audit Trail (En Memoria):
  Total registros: 95
  Conversiones auditadas: 15
  CR auditado: 15.79%
  Integridad: ✅ VÁLIDA

✅ Backend y Audit Trail coinciden exactamente
```

### Demostración de Transparencia
```
────────────────────────────────────────────────────────────────
📋 QUÉ CONTIENE EL AUDIT TRAIL
────────────────────────────────────────────────────────────────

✅ LO QUE SÍ ESTÁ EN AUDIT TRAIL:
  • visitor_id: final_visitor_49
  • variant_id: abc12345...
  • variant_name: Variant B
  • decision_timestamp: 2025-12-19T09:31:45.678Z
  • decision_hash: a4f2b9c1e8d7...
  • sequence_number: 94

❌ LO QUE NO ESTÁ EN AUDIT TRAIL:
  • alpha, beta (parámetros internos)
  • probabilidades calculadas
  • samples de distribuciones Beta
  • razón de por qué se eligió esta variante
  • estado completo del experimento

💡 Esto permite:
  ✅ Cliente puede auditar TODAS las decisiones
  ✅ Cliente puede verificar que no hay trampa
  ✅ Samplit protege su propiedad intelectual
  ✅ Competencia NO puede copiar el algoritmo
```

---

## 🔍 Qué Verifica Cada Paso

| Paso | Verificación | Qué Comprueba |
|------|--------------|---------------|
| 1-2  | Setup | Conexión BD + Usuario |
| 3-4  | Experimento | Creación + Activación |
| 5    | Estado Inicial | Priors Adaptive (1,1) |
| **6** | **Asignación + Audit** | **Decisiones registradas** |
| **7** | **Integridad Audit** | **Hash chain, timestamps** |
| 8    | Conversiones | Backend + Audit |
| 9    | Aprendizaje | Estado adaptativo actualizado |
| **10** | **Audit Completo** | **Integridad mantenida** |
| 11   | Optimización | Tráfico a ganador |
| **12** | **Resultado** | **Adaptive + Audit OK** |

---

## ✅ Criterios de Éxito

### Optimización Adaptativa
```python
✅ b_traffic >= 20  # >40% del tráfico a B
```

### Sistema de Auditoría
```python
✅ integrity['is_valid'] == True

# Donde:
- chain_integrity: True     # Hash chain correcto
- timestamp_order: True     # decision < conversion
- sequence_continuity: True # No gaps en secuencia
```

### Comparación
```python
✅ backend_conversions == audit_conversions
```

---

## 🆚 Diferencias con Versión Anterior

### Antes (solo Optimización Adaptativa)
```
✅ 10 pasos
✅ Verificaba algoritmo
❌ No verificaba auditoría
❌ No demostraba transparencia
```

### Ahora (Adaptativa + Auditoría)
```
✅ 12 pasos
✅ Verifica algoritmo
✅ Verifica auditoría
✅ Demuestra transparencia
✅ Compara backend vs audit
✅ Muestra qué se registra vs qué NO
```

---

## 📋 Estructura del Código

### AuditService (Nuevo)
```python
class AuditService:
    """Sistema de auditoría"""
    
    def log_decision(...)
        # Registra decisión con hash
        # ✅ visitor_id, variant_id, timestamp
        # ❌ NO alpha, beta, probabilidades
    
    def log_conversion(...)
        # Registra conversión
        # Verifica: decision < conversion
    
    def verify_integrity(...)
        # Verifica hash chain
        # Verifica timestamps
        # Verifica secuencia
```

### Integración con Optimización Adaptativa
```python
# 1. ALGORITMO DECIDE (privado)
assignment = await service.allocate_user_to_variant(...)
# El motor adaptativo calcula parámetros, muestrea, etc.

# 2. AUDITORÍA REGISTRA (público)
audit.log_decision(
    visitor_id=visitor_id,
    variant_id=assignment['variant_id'],
    ...
)
# Solo registra ID, timestamp, hash
```

---

## 🐛 Troubleshooting

### Error: ModuleNotFoundError
```bash
# Instalar dependencias
pip install asyncpg --break-system-packages
```

### Error: could not connect to server
```bash
# Verificar PostgreSQL
systemctl status postgresql

# O iniciar
systemctl start postgresql
```

### Error: relation does not exist
```bash
# Aplicar migrations
psql -U postgres -d samplit -f migrations/001_initial_schema.sql
```

### Audit integrity fails
```python
# Revisar:
- Hash chain (previous_hash correcto?)
- Timestamps (decision < conversion?)
- Sequence (no gaps?)
```

---

## 🎓 Resumen

### Lo Que Este Script Demuestra

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  OPTIMIZACIÓN ADAPTATIVA                                 │
│  ✅ Funciona correctamente                            │
│  ✅ Aprende de conversiones                           │
│  ✅ Optimiza tráfico automáticamente                  │
│                                                        │
│  SISTEMA DE AUDITORÍA                                 │
│  ✅ Registra todas las decisiones                     │
│  ✅ Mantiene integridad criptográfica                 │
│  ✅ NO revela propiedad intelectual                   │
│  ✅ Permite auditoría completa al cliente             │
│                                                        │
│  RESULTADO                                             │
│  🎉 Sistema completo verificado                       │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 📚 Documentación Relacionada

- **Arquitectura completa:** `AUDIT_REAL_TIME_MULTIELEMENT.md`
- **FAQ clientes:** `AUDIT_FAQ_CLIENT.md`
- **Demo educativo:** `demo_audit_realtime.py`
- **Demo backend real:** `demo_multielement_with_audit.py`
- **Scripts README:** `DEMO_SCRIPTS_README.md`

---

## 💡 Próximos Pasos

1. **Ejecutar el script**
   ```bash
   python scripts/verify_flow.py
   ```

2. **Verificar output**
   - Todos los checks ✅
   - Variant B recibe >40% tráfico
   - Audit integrity válida

3. **Usar en producción**
   - Integrar AuditService en backend
   - Crear tabla `algorithm_audit_trail`
   - Exponer endpoints de auditoría

4. **Demostrar a clientes**
   - "Nuestro sistema tiene auditoría completa"
   - "Pueden verificar integridad criptográfica"
   - "Sin revelar nuestro algoritmo"
