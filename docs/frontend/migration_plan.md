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
- **Help Center (`help_center_v2.html`)**: ✅ **COMPLETADO** (Controller `helpCenter()` con búsqueda dinámica).

### 9. Advanced Tools
- **Visual Editor (`visual_editor_v2.html`)**: ✅ **COMPLETADO** (Controller `visual-editor.js` con preview iframe).
- **Funnel Builder (`funnel_builder_v2.html`)**: ✅ **COMPLETADO** (Controller `funnelBuilder()` con drag-drop canvas).
- **Audits (`audits_v2.html`)**: ✅ **COMPLETADO** (Controller `auditDashboard()` con hash chain UI).

### 10. Integrations
- **Integrations (`integrations_v2.html`)**: ⚠️ **UI Lista, Falta API Connection**
    - UI completa con tabs por categoría
    - Falta: Crear `integration-service.js` y controlador Alpine

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

### ⚠️ Pendiente Conexión API
| Módulo | Estado Backend | Estado Frontend | Acción Requerida |
| :--- | :--- | :--- | :--- |
| **Integrations** | `/integrations/*` existe | UI lista, sin controlador | Crear `IntegrationsService` |

### ✅ Módulos Ya Funcionales (UI + Mock/Local Data)
| Módulo | Controlador | Notas |
| :--- | :--- | :--- |
| Visual Editor | `visual-editor.js` | Preview con iframe |
| Funnel Builder | `funnel-builder.js` | Canvas drag-drop |
| Audits | `auditDashboard()` | Hash chain visual |
| Help Center | `helpCenter()` | Búsqueda local |

---

## 📅 Próximos Pasos (Fase Final)

1.  ✅ **Integrations API Wiring**: `integration-service.js` + controlador Alpine conectados.
2.  ✅ **Install Verification UI**: Sección añadida a `settings_v2.html` con controller.
3.  ⏸️ **Legacy Wipe**: **MANTENIDO COMO BACKUP** por decisión del usuario.
    - `static/_legacy_v1_backup` - Conservado
    - `static/_template_archive` - Conservado
    - `static/js/_legacy_v1_backup` - Conservado

> **🏁 MIGRACIÓN V2 COMPLETADA**

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
*   **Shake-on-Error**: ✅ Implementado.
*   **Password Strength**: ✅ Implementado (medidor visual 4 barras).
*   **Social Login**: ⏸️ UI lista (Google/GitHub buttons), backend pending.
*   **Session recovery**: ⏸️ Future.

### 2. Dashboard (`dashboard_v2.js`)
*   **Greeting Dinámico**: ✅ Implementado ("Good morning/afternoon, [Name]").
*   **Skeleton Loading**: ✅ Implementado.
*   **Drag \u0026 Drop**: ⏸️ Future.
*   **Real-time**: ⏸️ WebSockets future.

### 3. Gestión de Experimentos (`experiments_v2.js`)
*   **Virtual Scrolling**: ⏸️ Future (para 10k+ items).
*   **Saved Views**: ⏸️ Future.
*   **Bulk Actions**: ✅ Implementado (Archive/Delete floating bar).
*   **Deep Linking**: ✅ Implementado (URL sync con filtros/paginación).
*   **Status Filter Tabs**: ✅ Implementado (All/Active/Draft/Completed).

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
*   **Undo/Redo Stack**: ✅ Implementado (50 items max, Ctrl+Z/Y).
*   **Element Selector**: ✅ Implementado (highlight on hover, CSS selector generation).
*   **Responsive Preview**: ✅ Implementado (Desktop/Tablet/Mobile buttons + shortcuts 1/2/3).
*   **Keyboard Shortcuts**: ✅ Ctrl+Z, Ctrl+Y, Escape, 1/2/3 viewports.

---

### 💎 The "Senior Touch" (Secret Sauce)
*Estos detalles separan un producto funcional de uno Premium.*

1.  **Transiciones "Mantequilla"**: [x] Todos los módulos.
2.  **Empty States Ilustrados**: [x] Experiment List, Billing, Analytics.
3.  **Micro-Interacciones Táctiles**: [x] Todos los botones.
4.  **Toast Notifications Stacking**: [x] `partials/toast_stack.html` global.
5.  **Focus Rings Premium**: [x] CSS en Auth.
6.  **Skeleton Shimmer**: [x] Dashboard, Lists, Analytics, Billing.

## 🌟 Matriz de Excelencia UX (The "Senior Standard")

*Esta matriz define los requisitos obligatorios para considerar una vista como "Premium/Final". ✅ = Implementado.*

| Vista / Módulo | Loading State (Skeletons) | Empty States (Ilustrados) | Transiciones (x-transition) | Micro-Interacciones (Feedback) | Estado Actual |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dashboard** | ✅ Skeleton Grid + Chart | N/A | ✅ Fade-in charts | ✅ Botones táctiles | **GOLD STANDARD** 🏆 |
| **Auth (Login/Reg)** | ✅ Spinner en botón | N/A | ✅ Focus Rings Premium | ✅ Shake on Error | **GOLD STANDARD** 🏆 |
| **Experiment List** | ✅ Table Skeleton | ✅ "No Experiments" + CTA | ✅ Row leave transition | ✅ Hover row animations | **GOLD STANDARD** 🏆 |
| **Wizard (Create)** | ✅ Step ready | ✅ Auto-Save Badge | ✅ Slide-left/right | ✅ Save micro-indicator | **GOLD STANDARD** 🏆 |
| **Analytics Detail** | ✅ Chart Skeleton | ✅ "Listening..." Waiting | ✅ Chart load anim | ✅ Smooth transitions | **GOLD STANDARD** 🏆 |
| **Billing & Plan** | ✅ Invoice Skeleton | ✅ "No Transactions" | ✅ Progress bar animated | ✅ Download hover | **GOLD STANDARD** 🏆 |
| **Shared/Global** | ✅ Sidebar ready | ✅ Toast Stack | ✅ Toast Stacking, Modal fade | ✅ Cmd+K Command Palette | **GOLD STANDARD** 🏆 |

### Detalle de Implementación por Vista

#### 1. Authentication (`auth_v2.html`)
*   **Requisito Senior**: El formulario no debe "saltar" al cambiar entre Login y Register. Debe usar `x-transition` para deslizarse suavemente o hacer un flip.
*   **Error Handling**: Si falla el login, el card debe vibrar (animación CSS `shake`).

#### 2. Experiment List (`experiments_v2.html`)
*   **Optimistic UI**: Ya implementamos lógica de borrado. Falta visual: La fila debe colapsar su `height` y opacidad suavemente (`x-transition:leave`) antes de desaparecer del DOM.
*   **Empty State**: Si el array está vacío, mostrar bloque centrado con Ilustración SVG 3D/Flat y botón primario "Launch First Experiment".

#### 3. Wizard (`experiments_create_v2.js`)
*   **Step Transition**: Al dar "Next", el contenido actual debe salir por la izquierda (`-translate-x`) y el nuevo entrar por la derecha.
*   **Feedback**: Mostrar un pequeño indicador "Saved" en la esquina cada vez que el Auto-Save (`localStorage`) se dispara.

#### 4. Analytics (`analytics_v2.html`)
*   **Chart Loading**: Replicar el patrón del Dashboard (Skeletons exactos del tamaño del gráfico).
*   **Waiting State**: Si el experimento es nuevo, mostrar un estado "Listening for events..." con una animación de radar/ping, no un gráfico vacío a cero.

## 📝 Lista de Verificación de Implementación (Prioridad)

1.  [x] **Auto-Save Wizard**: Implementar persistencia en `experiments_create_v2.js`.
2.  [x] **Optimistic UI en Tablas**: Eliminar filas visualmente antes de la llamada API `delete`.
3.  [x] **Skeletons Globales**: Dashboard, Analytics, Billing, Experiment List - 100% migrado.
4.  [x] **Command Palette**: `partials/command_palette.html` inyectado globalmente.
5.  [x] **Toast Stack Premium**: `partials/toast_stack.html` con progress bar y tipos.
6.  [x] **Empty States**: Todas las tablas y gráficos tienen estados vacíos ilustrados.
7.  [x] **Micro-Interacciones**: Shake on error, botones táctiles, focus rings premium.

