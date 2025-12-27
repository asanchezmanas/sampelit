# 📋 Detalle de Migración V1 → V2

Análisis archivo por archivo: qué hay, qué está mal, qué poner, y sub-tareas.

---

## Leyenda

- ✅ V2 existe y es funcional
- ⚠️ V2 tiene mocks (no conecta API)
- ❌ No hay V2 o V1 debe eliminarse
- 🔄 En progreso

---

## 🏗️ Arquitectura "Hybrid V2" (Implemented)

La migración ha evolucionado hacia una arquitectura híbrida robusta que combina la simplicidad de Alpine.js con una capa de servicios profesional.

### Capas del Sistema:
1.  **Core**: `js/core/api.js` (Cliente HTTP centralizado).
2.  **Services**: Capa de negocio pura (API Calls & Data Formatting).
    *   `js/services/experiment-service.js`
    *   `js/services/metrics-service.js`
    *   `js/services/team-service.js`
    *   `js/services/auth-service.js` (Includes Login/Register/Profile)
    *   `js/services/billing-service.js` (Includes Subscription/Invoice)
3.  **State Management**: `js/alpine-store.js` (Store global reactivo).
    *   `Alpine.store('experiments')`
    *   `Alpine.store('analytics')`
    *   `Alpine.store('team')`
    *   `Alpine.store('auth')`
    *   `Alpine.store('ui')`
4.  **View Controllers**: Controladores Alpine por página (`js/pages/*_v2.js`).

---

## 🚀 Estado de Migración por Módulo

### 1. Dashboard (`index_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: Conectado a `Alpine.store('experiments')`.

### 2. Experiments
- **Listing (`experiments_v2.html`)**: ✅ **COMPLETADO**
- **Detail (`experiment_detail_v2.html`)**: ✅ **COMPLETADO**
- **Create (`experiments_create_v2.html`)**: ✅ **COMPLETADO**

### 3. Analytics (`analytics_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: `MetricService` + `store.analytics`.

### 4. Settings & Team (`settings_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: `TeamService` + `store.team`.

### 5. Profile (`profile_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: `AuthService` + `store.auth`.

### 6. Billing (`billing_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: `BillingService` con inyección directa en controlador.
- **Features**: Suscripción activa, listado de facturas, upgrade modal.
- **Controlador**: `js/pages/billing_v2.js`

### 7. Auth Pages
- **Sign In (`signin_v2.html`)**:
    - **Estado**: ✅ **COMPLETADO**
    - **Architecture**: `AuthService.login()` via `js/pages/auth_v2.js`.
- **Sign Up (`signup_v2.html`)**:
    - **Estado**: ✅ **COMPLETADO**
    - **Architecture**: `AuthService.register()` via `js/pages/auth_v2.js`.

### 8. Tools
- **Simulator (`simulator_v2.html`)**: ✅ **COMPLETADO** (Usa `ExperimentService.forecast`).
- **Help Center (`help_center_v2.html`)**: ⚠️ **Pendiente** (Baja prioridad).

---

## 📅 Próximos Pasos (Limpieza Final)

1.  **Legacy Cleanup**: Eliminar carpetas viejas de JS y HTML v1.
2.  **Visual Editor**: Decidir estrategia (Iframe vs Proxy).
3.  **Help Center**: Refactor simple si es necesario.

---
