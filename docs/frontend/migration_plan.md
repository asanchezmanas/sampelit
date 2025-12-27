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

## 🔌 Matriz de Cobertura de Endpoints (Gap Analysis)

Esta sección detalla qué partes del Backend (FastAPI) están realmente conectadas en el Frontend V2.

### ✅ Core Critical Path (Conectado 100%)
Estos módulos utilizan controladores JS reales (`js/services/*`) y hablan con la API.

| Backend Router | Frontend Service | Rutas Verificadas |
| :--- | :--- | :--- |
| `routers/auth.py` | `auth-service.js` | `/auth/login`, `/auth/register`, `/auth/me` |
| `routers/experiments.py` | `experiment-service.js` | `GET /`, `POST /`, `GET /{id}`, `PATCH /{id}/status` |
| `routers/analytics.py` | `metrics-service.js` | `GET /global`, `GET /experiment/{id}` |
| `routers/subscriptions.py` | `billing-service.js` | `GET /subscription` |
| `routers/simulator.py` | `experiment-service.js` | `/simulate/forecast` (con fallback) |

### ❌ Periferia (Maquetas Visuales)
Estos módulos tienen backend, pero el frontend es solo HTML estático sin controlador JS ("No-Code" por ahora).

| Módulo | Estado Backend | Estado Frontend | Acción Requerida |
| :--- | :--- | :--- | :--- |
| **Integrations** | `/integrations/*` existe | `integrations_v2.html` es maqueta (tarjetas estáticas). | Crear `IntegrationsService` |
| **Audits** | `/audit/*` existe | `audits_v2.html` (si existe) es maqueta. | Crear `AuditService` |
| **Visual Editor** | `/canvas/*` existe | `visual_editor_v2.html` es maqueta. | Implementar Editor JS |
| **Funnels** | `/funnels/*` (deshabilitado) | `funnel_builder_v2.html` es maqueta. | Habilitar backend y conectar |
| **Installations** | `/installations/*` existe | No hay UI para validar snippet. | Agregar UI de "Verify Install" |

---

## 📅 Próximos Pasos (Fase 5 - Post-Migration)

1.  **Visual Editor Implementation**: El mayor gap técnico restante. Requiere proxy o iframe.
2.  **Integrations Wiring**: Convertir la vista estática en dinámica.
3.  **Legacy Wipe**: Borrar `static/_legacy_v1_backup` después de QA.

---

# 6. 💎 Roadmap SOTA (State of the Art UX/UI)

Este documento define el estándar de excelencia "State of the Art" que Sampelit V2 debe alcanzar. No es una lista de deseos, es la especificación funcional para un SaaS de Tier-1.

## 🅰️ Cross-Cutting Concerns (Global)

Mejoras que afectan a toda la aplicación.

| Dimensión | Requisito SOTA | Detalles de Implementación |
| :--- | :--- | :--- |
| **Data Safety** | **No Data Loss Policy** | Implementar `localStorage` auto-save en TODOS los formularios. Detectar cierre de pestaña (`onbeforeunload`) si hay datos sucios (`isDirty`). |
| **Navigation** | **Instant Transitions** | SPA real. El sidebar y header no deben parpadear. Prefetch de datos al hacer hover en enlaces del sidebar. |
| **Accessibility** | **Keyboard First** | Todo debe ser operable sin mouse. Focus indicators visibles. Soporte real para Screen Readers (ARIA labels). |
| **Power User** | **Command Palette (Cmd+K)** | Menú modal global para navegar ("Ir a Billing"), crear ("Nuevo Experimento") y buscar ("Buscar usuario X"). |
| **Feedback** | **Optimistic UI** | La interfaz miente. Si borras un item, desaparece instantáneamente. Si la API falla 1s después, reaparece con un Toast de error. |

---

## 🅱️ Análisis por Módulo

### 1. Autenticación (`auth_v2.js`)
*   **Shake-on-Error**: Si el login falla, el modal vibra (feedback visceral).
*   **Password Strength**: Medidor de fuerza de contraseña en tiempo real.
*   **Social Login**: Botones de Google/GitHub nativos (sin popup si es posible).
*   **Session recovery**: Si el token expira mientras escribo un email, guardar el borrador, pedir re-login en modal, y restaurar el borrador.

### 2. Dashboard (`dashboard_v2.js`)
*   **Greeting Dinámico**: "Buenos días, Artur" basado en hora local.
*   **Skeleton Loading**: Cero spinners. Mostrar estructura de cajas grises pulsantes (shimmer) mientras carga.
*   **Drag & Drop**: Permitir reorganizar widgets (KPIs arriba, Gráficas abajo). Persistir preferencia.
*   **Real-time**: Si un experimento tiene una conversión AHORA, actualizar el contador vía WebSockets (o polling inteligente).

### 3. Gestión de Experimentos (`experiments_v2.js`)
*   **Virtual Scrolling**: Si hay 10,000 experimentos, el DOM solo renderiza 20. Scroll infinito fluido.
*   **Saved Views**: Permitir guardar filtros complejos (ej: "Mis tests activos en Mobile") como pestañas rápidas.
*   **Bulk Actions**: Seleccionar 50 experimentos -> "Archivar". Barra flotante de acciones.
*   **Deep Linking**: La URL debe contener el estado de la UI. `sampelit.com/experiments?status=active&sort=date_desc&q=landing`.

### 4. Creation Wizard (`experiments_create_v2.js`)
*   **Persistencia Total**: Si cierro el navegador en el Paso 3, al volver mañana sigo en el Paso 3.
*   **Validación Inline**: El campo se pone rojo en cuanto dejo de escribir (blur), no al enviar. Mensajes de error contextuales.
*   **Preview Realista**: Al poner la URL, mostrar un iframe (o screenshot) del sitio objetivo, no solo texto.
*   **Smart Defaults**: Si el 90% de mis tests son "A/B", no preseleccionar "Multivariante". Aprender del usuario.

### 5. Analytics & Reports (`analytics_v2.js`)
*   **Interactive Charts**: Tooltips detallados al pasar el mouse. Zoom (seleccionar área para ampliar).
*   **Export nativo**: "Download as PNG" y "Export CSV" generados en cliente (JS), sin esperar al servidor.
*   **Comparison Mode**: Superponer gráficas de dos experimentos para ver correlaciones.
*   **Annotated Timeline**: Marcar hitos en la gráfica (ej: "Black Friday", "Cambio de diseño") para explicar picos.

### 6. Billing & Subscription (`billing_v2.js`)
*   **Pro-rata Calculator**: Al cambiar de plan a mitad de mes, mostrar exactamente cuánto se cobrará/abonará antes de confirmar.
*   **Invoice PDF**: Generación de PDF en cliente para descarga inmediata.
*   **Usage Alerts**: Barra de progreso que cambia de color (verde -> amarillo -> rojo) al acercarse al límite de MAUs.

### 7. Settings & Team (`settings_v2.js`)
*   **Avatar Crop**: Subir imagen, recortar en cliente (círculo), optimizar a WebP antes de subir.
*   **Dark Mode Sync**: Opción "System Default" que reacciona si cambia el OS de día a noche.
*   **Undo Changes**: Botón "Reset" global si he tocado muchas configuraciones y quiero volver al estado guardado.

### 8. Visual Editor (Integración Futura)
*   **Undo/Redo Stack**: Ctrl+Z y Ctrl+Y infinitos.
*   **Element Selector**: Al pasar el mouse por el sitio web, resaltar elementos del DOM inteligentemente.
*   **Responsive Preview**: Botones para ver cómo queda el cambio en Mobile/Tablet/Desktop al instante.

---

## 📝 Lista de Verificación de Implementación (Prioridad)

1.  [x] **Auto-Save Wizard**: Implementar persistencia en `experiments_create_v2.js` (Baja esfuerzo / Alto impacto).
2.  [x] **Optimistic UI en Tablas**: Eliminar filas visualmente antes de la llamada API `delete`.
3.  [ ] **Skeletons Globales**: Reemplazar todos los `loading = true` con componentes Skeleton.
4.  [ ] **Command Palette**: Inyectar componente global de búsqueda.

