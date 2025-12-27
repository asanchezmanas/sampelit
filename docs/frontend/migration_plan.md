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
1.  **Core**: `js/core/api.js` (Cliente HTTP centralizado con manejo de errores y auth headers).
2.  **Services**: Capa de negocio pura (API Calls & Data Formatting).
    *   `js/services/experiment-service.js`
    *   `js/services/metrics-service.js`
    *   `js/services/team-service.js`
    *   `js/services/auth-service.js`
3.  **State Management**: `js/alpine-store.js` (Store global reactivo).
    *   `Alpine.store('experiments')`: Lista, activo actual, CRUD.
    *   `Alpine.store('analytics')`: Métricas globales, tráfico, dispositivos.
    *   `Alpine.store('team')`: Miembros, roles, organización.
    *   `Alpine.store('auth')`: Usuario actual, login/logout, perfil.
    *   `Alpine.store('ui')`: Sidebar, Dark Mode, Toasts.
4.  **View Controllers**: Controladores Alpine por página (`js/pages/*_v2.js`) que consumen los Stores.

---

## 🚀 Estado de Migración por Módulo

### 1. Dashboard (`index_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: Conectado a `Alpine.store('experiments')`.
- **Características**:
    *   Timeline de actividad premium cronológica.
    *   KPI cards con tendencias.
    *   Gráfico de rendimiento v2 (TailAdmin style).
    *   Filtros de estado (Active/Paused).
- **Controlador**: `js/pages/dashboard_v2.js`

### 2. Experiments
- **Listing (`experiments_v2.html`)**:
    - **Estado**: ✅ **COMPLETADO**
    - **Architecture**: Usa `store.experiments.fetchAll()`.
    - **Features**: Búsqueda, filtrado por estado, paginación, acciones (Delete, Pause).
    - **Controlador**: `js/pages/experiments_v2.js`
- **Detail (`experiment_detail_v2.html`)**:
    - **Estado**: ✅ **COMPLETADO**
    - **Architecture**: `store.experiments.fetchOne(id)`.
    - **Features**: Insights de negocio, Gráfico Bayesiano, Uplift Calc, Tabla de variantes.
    - **Controlador**: `js/pages/experiment_detail_v2.js`
- **Create (`experiments_create_v2.html`)**:
    - **Estado**: ✅ **COMPLETADO**
    - **Architecture**: `store.experiments.create(payload)`.
    - **Features**: Wizard de 3 pasos, validación básica.
    - **Controlador**: `js/pages/experiments_create_v2.js`

### 3. Analytics (`analytics_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: `MetricService` + `store.analytics`.
- **Features**:
    *   Dashboard de tráfico con Sparklines.
    *   Desglose por dispositivo (Donut chart).
    *   Rendimiento por página.
    *   Mapa de calor geográfico (Lista).
- **Controlador**: `js/pages/analytics_v2.js`

### 4. Settings & Team (`settings_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: `TeamService` + `store.team`.
- **Features**:
    *   Gestión de miembros (Invite, Remove, Role Change).
    *   Paginación de miembros.
    *   Información de organización.
    *   Roles Policy visual.
- **Controlador**: `js/pages/settings_v2.js`

### 5. Profile (`profile_v2.html`)
- **Estado**: ✅ **COMPLETADO**
- **Architecture**: `AuthService` + `store.auth`.
- **Features**:
    *   Edición de perfil (Nombre, Empresa).
    *   Cambio de contraseña.
    *   Avatar con iniciales autogeneradas.
- **Controlador**: `js/pages/profile_v2.js`

### 6. Billing (`billing_v2.html`)
- **Estado**: ⚠️ **Parcial / Standalone**
- **Architecture**: Tiene su propio controlador (`billing_v2.js`) pero falta integrarlo formalmente en `alpine-store.js` o usar un `BillingService`. Funciona visualmente con mocks.
- **Acción**: Integrar en fase de limpieza.

---

## 📅 Próximos Pasos (Prioridad)

1.  **Integration**: Revisar `simulator_v2.js` y `help_center_v2.js` para asegurar que sigan el patrón de arquitectura (Service/Store).
2.  **Auth Pages**: Verificar `signin_v2.html` y `signup_v2.html`. Deben usar `AuthService`.
3.  **Visual Editor**: Decidir estrategia final para el editor (Iframe vs Proxy) - *Complejidad Alta*.
4.  **Legacy Cleanup**: Mover archivos v1 (`dashboard.html`, `profile.html`, etc.) a carpeta `_legacy`.

---

## 🛡️ Brand Guidelines (Sampelit Premium)
*(Se mantiene igual que la versión anterior)*

## ⚖️ Comparativa Crítica: V1 vs V2
*(Se mantiene igual que la versión anterior)*

## 🧩 Sistema de Partials
*(Se mantiene igual que la versión anterior)*
- [x] Unificar `footer_landing.html` y `footer_landing_v2.html`.

## ⚙️ Estado de Conexión Técnica (API Integration Check)

| Módulo | Endpoint Base | Servicio JS | Store JS | Estado |
|--------|---------------|-------------|----------|--------|
| **Dashboard** | `/analytics/global` | `ExperimentService` | `experiments` | ✅ |
| **Exp. List** | `/experiments` | `ExperimentService` | `experiments` | ✅ |
| **Exp. Detail**| `/experiments/{id}` | `ExperimentService` | `experiments` | ✅ |
| **Analytics** | `/analytics/global` | `MetricsService` | `analytics` | ✅ |
| **Profile** | `/users/me` | `AuthService` | `auth` | ✅ |
| **Settings** | `/team` | `TeamService` | `team` | ✅ |
| **Billing** | `/billing` | *Pending* | *Pending* | ⚠️ (Mock UI) |
| **Simulator** | `/simulator` | *Pending* | *Pending* | ⚠️ (Mock UI) |
| **Help** | `/help` | *Pending* | *Pending* | ⚠️ (Mock UI) |

---
