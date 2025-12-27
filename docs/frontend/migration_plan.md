# 📋 Detalle de Migración V1 → V2

Análisis archivo por archivo: qué hay, qué está mal, qué poner, y sub-tareas.

---

## Leyenda

- ✅ V2 existe y es funcional
- ⚠️ V2 tiene mocks (no conecta API)
- ❌ No hay V2 o V1 debe eliminarse
- 🔄 En progreso

---

## 🧠 Filosofía Frontend de Sampelit

### Principios Fundamentales

1. **El valor está en el backend** - El motor Bayesiano, algoritmos MAB, y análisis son el diferencial
2. **Frontend mínimo y duradero** - No tocar demasiado, que dure años
3. **Sin frameworks volátiles** - No React/Vue/Angular que cambian cada 6 meses
4. **Sin build process** - Solo HTML estático servido por FastAPI
5. **Prototipado rápido** - Poder hacer cambios sin tooling complejo

### Stack Actual y su Durabilidad

| Tecnología | Volatilidad | Riesgo | Veredicto |
|------------|-------------|--------|-----------|
| **HTML** | ❌ Nula | ✅ 0% | Durará para siempre |
| **CSS/Tailwind CDN** | ⚠️ Baja | ✅ Bajo | CDN sigue funcionando, clases son estables |
| **Alpine.js** | ⚠️ Baja | ⚠️ Medio | Sintaxis simple, pero es dependencia |
| **Material Symbols** | ⚠️ Baja | ✅ Bajo | Google, estable |
| **Vanilla JS** | ❌ Nula | ✅ 0% | Siempre funciona |

### ⚠️ Riesgo: Alpine.js

Alpine.js es lightweight y simple, pero sigue siendo una dependencia:
- Si Alpine desaparece, los `x-data`, `@click`, `:class` dejan de funcionar
- **Alternativa segura**: Vanilla JS con data attributes

```html
<!-- Alpine.js (actual) -->
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open">Content</div>
</div>

<!-- Vanilla JS (más duradero) -->
<div data-component="toggle">
  <button data-action="toggle">Toggle</button>
  <div data-target="content" hidden>Content</div>
</div>
<script>/* 10 líneas de JS puro */</script>
```

### Decisión: ¿Mantener Alpine o Vanilla?

| Opción | Pros | Contras |
|--------|------|---------|
| **Mantener Alpine** | Ya implementado, menos código | Dependencia externa |
| **Migrar a Vanilla** | 0 dependencias, eterno | Más código, trabajo |

**Recomendación:** Mantener Alpine por ahora, pero:
- No añadir más dependencias
- Documentar que Alpine es la ÚNICA librería JS
- Si Alpine muere, migrar a Vanilla (no es urgente)

### ✅ Lo que está bien del stack actual:

1. **Sin Node.js en producción** - Solo FastAPI sirve HTML
2. **Sin bundlers** - No Webpack, Vite, etc.
3. **Sin JSX/TSX** - HTML puro
4. **Sin state management** - No Redux, Zustand, etc.
5. **Tailwind via CDN** - Si CDN muere, las clases siguen en HTML

## 🛡️ Brand Guidelines (Sampelit Premium)

La identidad visual de Sampelit combina la robustez técnica de la arquitectura V2 con la estética refinada encontrada en los prototipos originales (v1).

1.  **Nombre**: Siempre **Sampelit**. Erradicar totalmente "Stitch AI", "Stitch" y errores "Samplit".
2.  **El Logo "Dot"**: El nombre Sampelit debe terminar siempre con un punto en color de acento.
    *   `Sampelit<span class="text-accent">.</span>`
3.  **Iconografía**: Usar el icono de "varita mágica" para representar la IA.
    *   Material Symbol: `auto_fix_high`
4.  **Colores Core**:
    *   `primary`: `#0f172a` (Navy Profundo - Autoridad)
    *   `accent`: `#1e3a8a` (Azul Eléctrico - Interacción/Premium)
    *   `surface`: `#FAFAFA` (Fondo suave - Estilo Europeo)

### Estado de Branding por Directorio

| Ubicación | Branding | Estado |
|-----------|----------|--------|
| `static/` (raíz) | **Sampelit** | ✅ Adaptado |
| `static/new/` | **Stitch AI** | ❌ Templates sin adaptar |


---

## ⚖️ Comparativa Crítica: V1 vs V2

Tras analizar ambos sistemas, este es el veredicto bajo la filosofía de "que dure años":

| Característica | V1 (Monolítico) | V2 (Modular/Partials) | Ganador |
|----------------|-----------------|-----------------------|---------|
| **Mantenibilidad** | ❌ Pésima. Cambiar un link en el menú requiere editar 15 archivos. | ✅ Excelente. Editas 1 partial y cambia en toda la web. | ✅ V2 |
| **Consistencia de Marca** | ❌ Inconsistente. Unas páginas dicen "Labs", otras "Stitch", otras "Sampelit". | ✅ Total. La marca se define en el Snippet Estándar y Partials. | ✅ V2 |
| **Código Duplicado** | ❌ Alto. 50 líneas de CSS y Config Tailwind repetidas en cada HTML. | ✅ Mínimo. Solo el snippet de config y el resto en `sampelit-v2.css`. | ✅ V2 |
| **Riesgo de Errores** | ❌ Alto. Es fácil olvidar actualizar una página y dejar links rotos. | ✅ Bajo. La lógica es centralizada. | ✅ V2 |
| **Longevidad** | ⚠️ Media. El desorden acaba haciendo que el proyecto sea inmanejable. | ✅ Alta. Es HTML puro pero con arquitectura profesional. | ✅ V2 |

### ❌ Por qué V1 NO es mejor:
V1 parece "más simple" porque no tiene partials, pero es una **trampa de mantenimiento**. A los 6 meses, tendrás menús diferentes en cada página y archivos CSS basura por todos lados.

### ✅ Por qué V2 ES el camino:
V2 te permite tener la **potencia de un framework moderno** (componentes, configuración centralizada) pero con la **simplicidad del HTML de toda la vida**.

**Conclusión:** 
V2 es la arquitectura que realmente te permitirá "no tocar el frontend demasiado". Una vez configurado el Sidebar y el Header en sus partials, te olvidas de ellos para siempre.

---

## 🧩 Sistema de Partials

### Inventario de Partials

| Partial | Versión | Líneas | Estado |
|---------|---------|--------|--------|
| `sidebar.html` | v1 | 181 | ❌ Deprecated |
| `sidebar_v2.html` | v2 | 180 | ✅ Producción |
| `header.html` | v1 | 205 | ❌ Deprecated |
| `header_v2.html` | v2 | 201 | ✅ Producción |
| `header_landing.html` | v1 | 88 | ⚠️ Funcional pero sin Alpine |
| `header_landing_v2.html` | v2 | 81 | ✅ Producción |
| `footer_landing.html` | - | 75 | ✅ Usa esto |
| `footer_landing_v2.html` | - | 75 | ⚠️ Duplicado exacto |
| `modals_v2.html` | v2 | 228 | ✅ Solo v2 |
| `toast_v2.html` | v2 | 98 | ✅ Solo v2 |
| `overlay.html` | - | 3 | Minimal |
| `preloader.html` | - | 10 | Minimal |

### Comparativa V1 vs V2

#### Sidebar

| Aspecto | v1 (`sidebar.html`) | v2 (`sidebar_v2.html`) |
|---------|---------------------|------------------------|
| Branding | "Samplit." (typo!) | "Sampelit." ✅ |
| Iconos | SVG inline | Material Symbols ✅ |
| Items | Dashboard, Experiments, Funnels | Dashboard, Experiments, Analytics, Pricing, Integrations, Audits, Simulator |
| Admin | Email Leads | Team & Access |
| Settings | Billing, Site Setup, Profile, Logout | En header |
| Upgrade card | ❌ No | ✅ "Unlock Insights" CTA |
| Styling | CSS classes básicas | TailAdmin premium ✅ |

#### Header (App)

| Aspecto | v1 (`header.html`) | v2 (`header_v2.html`) |
|---------|---------------------|------------------------|
| Branding | "Samplit." (typo!) | "Sampelit." ✅ |
| Search | Basic | Premium con CMD+K ✅ |
| Notifications | Empty state | 4 tipos con animación ✅ |
| User menu | Basic dropdown | Premium con avatar ✅ |
| Dark mode | Toggle básico | Alpine.js reactivo ✅ |

#### Header Landing

| Aspecto | v1 (`header_landing.html`) | v2 (`header_landing_v2.html`) |
|---------|----------------------------|-------------------------------|
| Págalo | Home, Blog, About, FAQ, Pricing, Contact, **Help** | Home, Blog, About, FAQ, Pricing, Contact |
| Mobile | ❌ No tiene | ✅ `x-data` mobile menu |
| Dark mode | Script vanilla | Alpine.js parent `darkMode` ✅ |
| CTA | Log In + Start Free | Log In + Start Free |

### Problemas Encontrados

1. **Typo en v1**: "Sampl**i**t" en lugar de "Sampl**e**lit" en sidebar.html y header.html
2. **Links rotos v2**: `header_landing_v2.html` apunta a `pricing.html` (sin _v2)
3. **Duplicado**: `footer_landing.html` = `footer_landing_v2.html` (idénticos)
4. **v1 tiene "Help"**: `header_landing.html` incluye link a Help Center, v2 no

### Acciones de Partials

- [ ] Verificar qué páginas aún usan `sidebar.html` y `header.html` (v1)
- [ ] Eliminar partials v1 tras confirmar que no se usan
- [ ] Añadir link a Help Center en `header_landing_v2.html`
- [ ] Corregir links en `header_landing_v2.html`: `pricing.html` → `pricing_v2.html`
- [ ] Eliminar `footer_landing_v2.html` (duplicado)

### 💡 Partials bajo la Filosofía de Longevidad

Tras analizar el código interno de ambos, esta es la comparativa de robustez a largo plazo:

| Característica | V1 (`sidebar.html`) | V2 (`sidebar_v2.html`) | ¿Por qué V2 es más duradero? |
|----------------|---------------------|------------------------|------------------------------|
| **Branding** | "Samplit" (Error) | "Sampelit" (Correcto) | Evita tener que renombrar todo el UI después. |
| **Persistencia** | Usa `$persist` (Plugin) | Usa `localStorage` (Nativo) | **V2 es más robusto** al depender de APIs Web estándar en lugar de plugins de Alpine. |
| **Iconografía** | SVG Inline manual | Material Symbols (CDN) | V2 centraliza el estilo. Si Google cambia, se cambia un link. V1 requiere editar 180 líneas. |
| **Arquitectura** | Monolítica | Modular (Modals/Toasts) | V2 permite mejorar el backend sin tocar cada página HTML. Solo se edita el partial. |

**Veredicto de Longevidad:**
Irónicamente, **V2 es técnicamente "más vanilla"** en su lógica de persistencia que V1. V1 depende de un plugin específico de Alpine (`$persist`), mientras que V2 lo hace a mano con `localStorage`, lo que cumple mejor la filosofía de "que dure años sin tocarlo".

### ✅ Decisión Final sobre Partials

1. **Adoptar V2 para TODO.** Es el sistema que mejor corrige errores pasados y usa APIs más estándar.
2. **Eliminar V1**: Mantener `sidebar.html` y `header.html` es una deuda técnica con nombres de marca incorrectos.
3. **Fix Urgente V2**: Portar el link de "Help Center" de la landing V1 a la landing V2.
4. **Simplificar Toasts**: El sistema de `toast_v2.html` es auto-contenido y duradero. No requiere mantenimiento.

### Acciones de Partials (Ordenadas por prioridad)

- [ ] **[Bajo Riesgo]** Añadir link a Help Center en `header_landing_v2.html`.
- [ ] **[Bajo Riesgo]** Corregir link a `pricing.html` → `pricing_v2.html` en headers.
- [ ] **[Limpieza]** Eliminar `header.html` y `sidebar.html` una vez verificado que todas las páginas usan `*_v2.html`.
- [ ] **[Limpieza]** Unificar `footer_landing.html` y `footer_landing_v2.html`.


---

## 🎨 Sistema CSS y Tailwind

### Inventario de Archivos CSS

| Archivo | Líneas | Propósito | Usado por |
|---------|--------|-----------|-----------|
| `input.css` | 260 | **Tailwind v4** entry point + TailAdmin theme | V2 build |
| `sampelit.css` | 323 | Design tokens CSS variables v1 | V1 pages |
| `sampelit-v2.css` | 317 | Design tokens + utilities v2 | V2 pages |
| `main.css` | ~360 | Output compilado de Tailwind | Producción |
| `style.css` | ~590 | CSS legacy monolítico | ❌ Deprecated |
| `styles.css` | ~610 | Otro CSS legacy | ❌ Deprecated |
| `components.css` | ~95 | Componentes adicionales | Algunos |
| `prism.css` | ~60 | Syntax highlighting | Code blocks |

### Comparativa: Enfoque CSS

| Aspecto | V1 | V2 (Estrategia Definitiva) |
|---------|----|----|
| **Metodología** | Manual + Tailwind CDN | **Híbrido CDN + static CSS** |
| **Configuración** | Inline `tailwind.config` disperso | **Snippet Estándar Consolidado** |
| **Dark mode** | Variables CSS manuales | **Nativo Tailwind `class`** |
| **Build Process** | Nulo | **Nulo (Prohibido)** |
| **Mantenimiento** | Alto (CSS disperso) | **Bajo (Centralizado en `sampelit-v2.css`)** |

---

## 🛠️ El Snippet "No Preocupaciones" (Estándar V2)

Para garantizar la longevidad y el diseño premium sin usar Node.js o compiladores, cada página V2 debe incluir exactamente este bloque en el `<head>`:

```html
<!-- Sampelit Standard Snippet v2 -->
<!-- Google Fonts & Material Symbols -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1" />

<!-- Tailwind 3.x CDN + Plugins -->
<script src="https://cdn.tailwindcss.com?plugins=forms,typography,container-queries"></script>

<!-- Estilos Compartidos (Premium Components) -->
<link rel="stylesheet" href="css/sampelit-v2.css" />

<!-- Configuración Centralizada -->
<script>
    tailwind.config = {
        darkMode: 'class',
        theme: {
            extend: {
                colors: {
                    primary: "#0f172a",   // Navy Sampelit
                    accent: "#1e3a8a",    // Blue Accent Premium
                    sampelit: "#0f172a"   // Alias primary
                },
                fontFamily: {
                    display: ['Manrope', 'sans-serif'],
                    body: ['Inter', 'sans-serif'],
                },
                boxShadow: {
                    'premium': '0 10px 30px -5px rgba(15, 23, 42, 0.08)',
                    'soft': '0 2px 10px rgba(0, 0, 0, 0.03)'
                }
            }
        }
    }
</script>

<!-- Alpine.js (Longevidad JS) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

### sampelit.css (V1) - CSS Variables

```css
:root {
  --color-primary: #0f172a;
  --color-accent: #1e3a8a;
  // ... tokens
}

.btn { ... }      // Componentes como clases
.card { ... }
.input { ... }
```

### sampelit-v2.css - Híbrido

```css
:root {
  --sampelit-primary: #1E3A8A;
  // ... tokens alineados
}

.btn-premium { @apply ... }   // Usa @apply de Tailwind
.input-premium { @apply ... }
```

### 💡 Reflexión: ¿Por qué CDN es correcto para Sampelit?

**Realidad:** 100% de páginas usan **Tailwind CDN**, `input.css`/`main.css` NO se usan.

**CDN tiene sentido porque:**
1. **El valor está en el backend** (motor Bayesiano, algoritmos)
2. **No hay equipo frontend dedicado**
3. **Prototipado rápido > optimización bundle**
4. **Sin Node.js en servidor**

| Aspecto | CDN (actual ✅) | npm build |
|---------|-----------------|-----------|
| Requiere Node.js | ❌ No | ✅ Sí |
| Deploy | Solo copiar HTML | Build + deploy |
| Prototipado | ✅ Inmediato | ⚠️ Rebuild |

### Problema: Inconsistencia de Config

- ⚠️ `tailwind.config` duplicado en cada HTML
- ⚠️ 3 valores de "primary" diferentes
- ⚠️ Diferentes plugins en diferentes páginas

| Variable | Valor 1 | Valor 2 | Valor 3 |
|----------|---------|---------|---------|
| Primary | `#0f172a` | `#1754cf` | `#1E3A8A` |

### Acciones de Consolidación (V2 Prioridad)

- [x] **[Branding]** Unificar estética Premium Sampelit en Partials V2
- [x] **[Partials]** Añadir link a Help Center en `header_landing_v2.html`
- [x] **[Partials]** Corregir link a `pricing.html` -> `pricing_v2.html` en headers V2
- [x] **[Partials]** Actualizar `footer_landing_v2.html` con branding premium y links V2
- [ ] **[Standard]** Aplicar Snippet "No Preocupaciones" a todas las páginas `*_v2.html`
- [ ] **[Verificación]** Validar navegación completa entre páginas V2

### 🧹 Limpieza Pos-Migración (SOLO tras validación final)
> [!IMPORTANT]
> No eliminar archivos hasta que la versión V2 esté 100% operativa y probada.

- [ ] Eliminar `header.html` y `sidebar.html` (V1)
- [ ] Eliminar `footer_landing.html` (V1)
- [ ] Eliminar páginas V1 redundantes
- [x] Eliminar `input.css` y `main.css` (No se usan)

---

## 💎 Estándar de Diseño Sampelit (CDN)

Para cumplir la filosofía de "que dure años sin tocarlo", usaremos este snippet estándar en el `<head>` de todas las páginas V2. Esto elimina la necesidad de archivos CSS externos pesados.

### El Snippet "No Preocupaciones"

```html
<!-- Core Design System: Tailwind CDN + Brand Config -->
<script src="https://cdn.tailwindcss.com?plugins=forms,typography,container-queries"></script>
<script>
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          primary: "#0f172a",    /* Navy Profundo (Sampeit Principal) */
          accent: "#1e3a8a",     /* Azul Interactivo */
          surface: "#FAFAFA",    /* Fondo suave estilo europeo */
          border: { light: "#E2E8F0" }
        },
        fontFamily: {
          display: ['Manrope', 'sans-serif'],
          body: ['Inter', 'sans-serif'],
        }
      }
    }
  }
</script>

<!-- Iconografía Estándar -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1" />
```

### Ventajas de este Estándar:
1. **Consistencia total**: Si cambias el hexadecimal del `primary` aquí, cambia en toda la página.
2. **0 Mantenimiento**: Google sirve las fuentes e iconos; Tailwind sirve el CSS.
3. **Independencia**: No necesitas `npm`, no necesitas `sampelit.css`. Todo lo que la página necesita para verse bien está en su propio HTML.
4. **Respeto a V1**: Mantenemos los colores que hacían que V1 se viera premium, pero con el nombre **Sampelit**.


### Arquitectura de Partials v2

```
App Pages (dashboard, experiments, etc.):
├── <include src="./partials/sidebar_v2.html">
├── <include src="./partials/header_v2.html">
├── <include src="./partials/modals_v2.html">
└── <include src="./partials/toast_v2.html">

Landing Pages (index, about, pricing, etc.):
├── <include src="./partials/header_landing_v2.html">
└── <include src="./partials/footer_landing_v2.html">
```

### Características de Partials v2

| Partial | Alpine.js | Dark Mode | Branding |
|---------|-----------|-----------|----------|
| sidebar_v2 | ✅ `x-data`, localStorage | ✅ | ✅ Sampelit |
| header_v2 | ✅ dropdowns, search | ✅ | ✅ Sampelit |
| header_landing_v2 | ✅ mobile menu | ✅ | ✅ Sampelit |
| footer_landing_v2 | - | ✅ | ✅ Sampelit |
| modals_v2 | ✅ `modalSystem()` | ✅ | ✅ |
| toast_v2 | ✅ `toastSystem()` | ✅ | - |

### Cómo usar Modales

```html
<!-- Abrir modal -->
<button @click="$dispatch('open-modal', 'create-experiment')">Create</button>

<!-- Modales disponibles -->
- 'create-experiment' → Formulario nuevo experimento
- 'confirm-delete' → Confirmación eliminar
```

### Cómo usar Toasts

```html
<!-- Disparar toast -->
<button @click="$dispatch('show-toast', { 
  type: 'success', 
  message: 'Experiment saved!' 
})">Save</button>

<!-- Tipos disponibles -->
- success (verde)
- error (rojo)
- warning (amarillo)
- info (azul)
```

### Acciones de Partials

- [ ] Eliminar `header.html` (v1) tras validar que no se usa
- [ ] Eliminar `sidebar.html` (v1) tras validar que no se usa
- [ ] Unificar `footer_landing.html` y `footer_landing_v2.html` (son idénticos)

## 1. Dashboard

### V1: `dashboard.html` (466 líneas)

**Problemas:**
- ❌ No usa partials (`<include>`)
- ❌ Todo inline: CSS config, sidebar, header
- ❌ Datos hardcoded, no conecta API
- ❌ Sin darkMode reactivo

### V2: `index_v2.html` ✅

**Estado:** Funcional
- ✅ Usa `<include>` para sidebar/header
- ✅ Tiene `include.js`
- ✅ x-data con darkMode
- ⚠️ Conecta a API pero podría mejorar

### Sub-tareas:
- [ ] Verificar que conecta a `/analytics/global`
- [ ] Extraer JS a `js/pages/dashboard_v2.js`
- [ ] Eliminar `dashboard.html` tras validación

---

## 2. Experiments List

### V1: No existe (era parte de dashboard)

### V2: `experiments_v2.html` ✅

**Estado:** Funcional
- ✅ Arquitectura v2 correcta
- ✅ Conecta a `GET /experiments`
- ✅ Sorting, filtering, pagination

### Sub-tareas:
- [ ] Añadir estado empty/error
- [ ] Bulk actions (opcional)
- [ ] Extraer JS a archivo separado

---

## 3. Experiment Detail

### V1: `experiment-detail.html` + `experiment-results.html`

**Problemas:**
- ❌ Dos archivos para misma función
- ❌ Layout sin partials
- ❌ Datos mock

### V2: `experiment_detail_v2.html` ✅

**Estado:** Funcional
- ✅ Conecta a `/analytics/experiment/{id}`
- ✅ Muestra variantes, confianza
- ✅ JS extraído a `js/pages/experiment_detail_v2.js`

### Sub-tareas:
- [x] Spec completo ✅
- [x] JS separado ✅
- [ ] Eliminar v1 tras validación

---

## 4. Create Experiment

### V1: No existe como página separada

### V2: `experiments_create_v2.html` ✅

**Estado:** Funcional
- ✅ Wizard de 3 pasos
- ✅ Conecta a `POST /experiments`

### Sub-tareas:
- [ ] Validación de formularios más robusta
- [ ] Preview de variantes

---

## 5. Visual Editor

### V1: `visual-editor.html` (279 líneas)

**Problemas:**
- ❌ **Sin sidebar/header** - Layout totalmente diferente
- ❌ No usa includes
- ✅ Pero tiene Alpine.js y conecta a API
- ⚠️ Diseño intencionalmente diferente (fullscreen editor)

### V2: `visual_editor_v2.html`

**Estado:** Parcial
- ✅ Usa arquitectura v2
- ⚠️ Verificar funcionalidad del iframe proxy

### Decisión: ¿Migrar o mantener layout especial?
El visual editor necesita layout fullscreen. Opciones:
1. Mantener layout especial sin sidebar
2. Añadir sidebar colapsable

### Sub-tareas:
- [ ] Decidir layout final
- [ ] Crear spec `visual_editor.md`
- [ ] Verificar endpoint `/visual-editor/proxy`
- [ ] Verificar endpoint `/visual-editor/save-elements`

---

## 6. Funnel Builder

### V1: `funnel-builder.html`

**Problemas:**
- ❌ Sin includes (usaba fetch manual - ya corregido en v2)
- ❌ Layout diferente al resto

### V2: `funnel_builder_v2.html` ✅ (corregido)

**Estado:** Arquitectura corregida
- ✅ Ahora usa `<include>` (corregido esta sesión)
- ⚠️ Lógica interna sin verificar

### Sub-tareas:
- [ ] Crear spec `funnel_builder.md`
- [ ] Verificar endpoints de funnels
- [ ] Probar funcionalidad de drag & drop

---

## 7. Calendar

### V1: `calendar.html`

**Problemas:**
- ❌ Layout antiguo

### V2: `calendar_v2.html` ✅ (corregido)

**Estado:** Arquitectura corregida
- ✅ Ahora usa `<include>` (corregido esta sesión)
- ⚠️ Datos mock

### Sub-tareas:
- [ ] Conectar a endpoint de experimentos programados
- [ ] Integrar librería de calendario (FullCalendar?)

---

## 8. Profile / Settings

### V1: `profile.html`

**Problemas:**
- ❌ Layout antiguo
- ❌ Sin conexión a API

### V2: `profile_v2.html` ✅

**Estado:** Parcial
- ✅ Arquitectura v2 correcta
- ⚠️ Datos mock hardcoded

### Sub-tareas:
- [ ] Conectar a `GET /users/me`
- [ ] Implementar `PATCH /users/me`
- [ ] Implementar cambio de password
- [x] Spec creado ✅

---

## 9. Integrations

### V1: No existe

### V2: `integrations_v2.html` ✅

**Estado:** Parcial
- ✅ Arquitectura v2 correcta
- ⚠️ Datos mock, toggles no funcionales

### Sub-tareas:
- [ ] Crear endpoint `/integrations`
- [ ] Implementar OAuth flows
- [x] Spec creado ✅

---

## 10. Simulator

### V1: `simulator-landing.html` (landing page)

### V2: `simulator_v2.html` ✅

**Estado:** Funcional
- ✅ Arquitectura v2
- ✅ Conecta a `/simulator/forecast`
- ✅ JS en `js/pages/simulator_v2.js`
- ✅ Spec completo con CSV upload

### Sub-tareas:
- [x] Spec completo ✅
- [x] JS separado ✅
- [ ] Implementar upload de CSV real

---

## 11. Analytics

### V1: No existe como página separada

### V2: `analytics_v2.html` ✅

**Estado:** Funcional
- ✅ Arquitectura v2
- ✅ Conecta a `/analytics/global`

### Sub-tareas:
- [x] Spec creado ✅
- [ ] Añadir gráficos con ApexCharts
- [ ] Extraer JS a archivo

---

## 12. Audits

### V1: No existe

### V2: `audits_v2.html` ✅

**Estado:** Funcional
- ✅ Arquitectura v2
- ✅ Conecta a `/audit/experiments/{id}/trail`

### Sub-tareas:
- [x] Spec completo ✅
- [ ] Implementar descarga PDF
- [ ] Extraer JS a archivo

---

## 13. Auth Pages (signin, signup, reset_password)

### V1: `signin.html`, `signup.html`, `reset_password.html`

### V2: `signin_v2.html`, `signup_v2.html`, `reset_password_v2.html` ✅

**Estado:** Funcional
- ✅ Arquitectura v2
- ✅ Conectan a endpoints de auth

### Sub-tareas:
- [ ] Verificar flujo completo de auth
- [ ] Añadir validación de formularios

---

## 14. Marketing/Landing Pages

### Páginas estáticas (no requieren API):
- `about_v2.html` ✅
- `contact_v2.html` ⚠️ (formulario sin envío)
- `faq_v2.html` ✅
- `pricing_v2.html` ✅
- `blog_v2.html`, `blog_post_v2.html` ⚠️ (mock)

### Sub-tareas:
- [ ] Conectar formulario de contacto
- [ ] Blog: decidir si CMS o estático

---

## 15. Error Pages

- `404_v2.html` ✅
- `500_v2.html` ✅
- `503.html` ❌ (no hay v2)

### Sub-tareas:
- [ ] Crear `503_v2.html`

---

## 16. Páginas en `static/new/` (51 archivos)

> ⚠️ **IMPORTANTE**: Estas páginas están EN PRODUCCIÓN si no tienen v2 en `static/`.
> Sufijos: `_br` = bordeless/rounded, `_d` = dark theme variant

### 16.1 Billing (❌ Sin V2 - EN PRODUCCIÓN)

| Archivo | Estado | Acción |
|---------|--------|--------|
| `billing.html` | ❌ V1 en prod | Crear `billing_v2.html` |
| `billing_br.html` | variante | Fusionar en v2 |

**Endpoint necesario:** `GET /billing`, `GET /invoices`

### 16.2 Account Settings (❌ Sin V2)

| Archivo | Estado |
|---------|--------|
| `account_settings.html` | ❌ V1 en prod |
| `role_settings.html` | ❌ V1 en prod |

**Acción:** Fusionar con `profile_v2.html` o crear `settings_v2.html`

### 16.3 CRM Dashboard (❌ Sin V2)

| Archivo | Estado |
|---------|--------|
| `crm_dasboard_br.html` | ❌ V1 en prod |
| `crm_dashboard_br_contactos.html` | ❌ V1 en prod |
| `crm_dashboard_d.html` | variante dark |
| `crm_dashboard_d_contactos.html` | variante dark |

**Decisión:** ¿CRM es feature core o separar?

### 16.4 Help Center (❌ Sin V2 - EN PRODUCCIÓN)

| Archivo | Líneas | Estado |
|---------|--------|--------|
| `help_center.html` | 354 | ❌ V1 en prod |
| `help_center_d.html` | - | variante dark |
| `help_center_post_br.html` | - | Artículos|
| `help_center_post_d.html` | - | variante dark |

**Análisis de `help_center.html`:**

```
Estructura:
├── Header con navegación fija
├── Hero con búsqueda (⌘K shortcut)
├── Grid de 6 categorías:
│   ├── 🚀 Primeros Pasos
│   ├── 🔌 Integraciones
│   ├── 📊 Análisis de Datos
│   ├── 💳 Facturación
│   ├── 🔧 Solución de Problemas
│   └── 🔌 API & Desarrolladores
├── Artículos Populares (lista)
├── Banner de soporte (Chat + Email)
└── Footer
```

**Qué tiene:**
- ✅ Diseño moderno dark mode
- ✅ Búsqueda con ⌘K
- ✅ Grid de categorías con iconos
- ✅ Artículos populares
- ❌ NO usa arquitectura v2 (sin includes)
- ❌ Sin Alpine.js para interactividad
- ❌ Contenido estático (no CMS)

**Acción:** Crear `help_center_v2.html` con:
- Arquitectura v2 (sidebar, header)
- Conectar a CMS/Markdown para artículos
- Búsqueda funcional

---

### 16.5 Create Experiment Wizard (⚠️ Conflicto con V2)

| Archivo | Paso | Contenido |
|---------|------|-----------|
| `create_exp_step_1.html` | 1. Define Hypothesis | Nombre, URL, métrica, hipótesis |
| `create_exp_step_2.html` | 2. Audience | Targeting, allocation |
| `create_exp_step_3.html` | 3. Variations | Diseño cambios |
| `create_exp_step_4.html` | 4. Review & Launch | Confirmación |

**Análisis de `create_exp_step_1.html` (357 líneas):**

```
Estructura:
├── Header con logo Sampelit
├── Sidebar izquierdo FIJO con timeline:
│   ├── 1. Define Hypothesis ← ACTIVO
│   ├── 2. Audience (gris)
│   ├── 3. Variations (gris)
│   └── 4. Review & Launch (gris)
├── Main content:
│   ├── Formulario: nombre, URL, métrica
│   ├── Hipótesis con botón "Generate with AI"
│   └── Traffic Allocation preview
├── Sidebar derecho: Tips contextuales
└── Footer sticky: Save Draft + Next
```

**Qué tiene de bueno:**
- ✅ Wizard de 4 pasos (v2 tiene 3)
- ✅ Sidebar con timeline visual
- ✅ Tips contextuales
- ✅ "Generate with AI" para hipótesis
- ✅ Auto-save indicator

**Problema:**
- ❌ NO coincide con `experiments_create_v2.html` (que es 3 pasos)
- ❌ Son 4 páginas separadas vs 1 página con steps
- ❌ Diseño diferente

**Decisión necesaria:**
1. ¿Mantener wizard de 4 pasos (new/) o 3 pasos (v2)?
2. ¿Migrar features de new/ a v2 o al revés?

---

### 16.8 Landing Pages (Marketing - EN PRODUCCIÓN)

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `home.html` | 673 | **Landing principal** |
| `home_d.html` | - | variante dark |
| `landing_ad.html` | - | Ads landing |
| `landing_adbr.html` | - | variante |
| `landing_b.html` | - | Variante B test |
| `landing_d.html` | - | variante dark |

**Análisis de `home.html` (673 líneas):**

```
Estructura:
├── Nav fija con blur
├── Hero:
│   ├── Badge "Neural Engine V3.2"
│   ├── H1: "La ciencia de la experimentación digital"
│   ├── CTA: "Comenzar ahora" + "Ver funcionamiento"
│   └── Dashboard mock con gráfico
├── Logos de clientes
├── Features (3 cards):
│   ├── Smart Allocation
│   ├── Inferencia Bayesiana
│   └── Editor Visual Puro
├── How it works (3 pasos)
├── Blog/Journal (3 artículos)
└── Footer completo
```

**Qué tiene:**
- ✅ Diseño premium europeo (light mode)
- ✅ Glassmorphism, gradientes sutiles
- ✅ Dashboard mock animado
- ✅ Responsive
- ❌ Marca "Stitch.ai" (¡no Sampelit!)
- ❌ Sin Alpine.js
- ❌ Links rotos (#)

**Problema crítico:**
- Esta landing tiene branding "Stitch.ai" pero el producto es "Sampelit"
- ¿Es un template o la landing real?

**Acción:**
1. Decidir qué landing usar: `home.html` o `pricing_v2.html`
2. Actualizar branding a Sampelit
3. Conectar links reales

### 16.6 Traffic Filter (❌ Sin V2)

| Archivo | Estado |
|---------|--------|
| `traffic_filter_br.html` | ❌ V1 en prod |
| `traffic_filter_d.html` | variante dark |

**Acción:** Crear `traffic_filter_v2.html` o integrar en experimento

### 16.7 User Demo Simulator (⚠️ Relacionado)

| Archivo | V2 equivalente |
|---------|----------------|
| `user_demo_simulator_br.html` | → `simulator_v2.html` |
| `user_demo_simulator_d.html` | variante dark |

**Estado:** Verificar si `simulator_v2.html` cubre funcionalidad

### 16.8 Landing Pages (Marketing)

| Archivo | Estado |
|---------|--------|
| `home.html` | ❌ Landing principal |
| `home_d.html` | variante dark |
| `landing_ad.html` | Ads landing |
| `landing_adbr.html` | variante |
| `landing_b.html` | Variante B test |
| `landing_d.html` | variante dark |

**Acción:** Decidir cuál es la landing oficial

### 16.9 Experiment Detail Variants

| Archivo | V2 equivalente |
|---------|----------------|
| `experiment detail.html` | → `experiment_detail_v2.html` ✅ |
| `experiment_detail_br.html` | Variante bordeless |

**Estado:** V2 existe, eliminar v1

### 16.10 Visual Editor

| Archivo | V2 equivalente |
|---------|----------------|
| `visual_editor.html` | → `visual_editor_v2.html` ⚠️ |

**Estado:** Verificar cuál es más completo

### 16.11 Otros

| Archivo | Estado | Acción |
|---------|--------|--------|
| `about.html` | ✅ Hay v2 | Eliminar |
| `about_faq-html` | Typo en ext | Eliminar |
| `blog.html`, `blog_v3.html` | Varias versiones | Consolidar |
| `contact.html`, `contact_br.html` | ✅ Hay v2 | Eliminar |
| `faq.html` | ✅ Hay v2 | Eliminar |
| `profile.html`, `profile_edit_*.html` | ⚠️ v2 parcial | Fusionar |
| `register.html` | → `signup_v2.html` | Eliminar |
| `signin.html`, `reset_password.html` | ✅ Hay v2 | Eliminar |
| `integrations.html` | ✅ Hay v2 | Eliminar |
| `404_*.html`, `500_*.html`, `503_*.html` | Variantes | Consolidar |

---

## 📋 CHECKLIST DE ACCIONES

### ✅ NO REQUIERE ACCIÓN (Ya existe en producción adaptado)

| Template en new/ | Ya existe como | Estado |
|------------------|----------------|--------|
| `home.html` | `static/index.html` | ✅ Branding Sampelit |
| `help_center*.html` | `static/help-center/` (10 artículos) | ✅ Completo |
| `signin.html` | `signin_v2.html` | ✅ |
| `register.html` | `signup_v2.html` | ✅ |
| `reset_password.html` | `reset_password_v2.html` | ✅ |
| `about.html` | `about_v2.html` | ✅ |
| `contact*.html` | `contact_v2.html` | ✅ |
| `faq.html` | `faq_v2.html` | ✅ |
| `blog*.html` | `blog_v2.html` | ✅ |
| `profile*.html` | `profile_v2.html` | ✅ |
| `integrations.html` | `integrations_v2.html` | ✅ |
| `visual_editor.html` | `visual_editor_v2.html` | ✅ |
| `experiment*.html` | `experiment_detail_v2.html` | ✅ |
| `user_demo_simulator*.html` | `simulator_v2.html` | ✅ |
| `landing*.html` | `index.html` / `pricing_v2.html` | ✅ |
| `404/500/503*.html` | Error pages v2 | ✅ |

---

### ❌ CREAR (No existe en producción)

- [ ] **`billing_v2.html`** - Adaptar desde `new/billing.html`
  - Rebranding: Stitch → Sampelit
  - Conectar a endpoint `/billing`
  - Añadir arquitectura v2 (includes, Alpine)

- [ ] **`settings_v2.html`** - Fusionar:
  - `new/account_settings.html`
  - `new/role_settings.html`
  - O integrar en `profile_v2.html`

---

### ⚠️ DECIDIR

- [ ] **CRM Dashboard** (`new/crm_dashboard_*.html`)
  - ¿Es feature core del producto?
  - Si SÍ → Crear `crm_v2.html`
  - Si NO → Ignorar

- [ ] **Traffic Filter** (`new/traffic_filter_*.html`)
  - ¿Página separada o integrar en experimento?

- [ ] **Wizard Create Experiment**
  - new/ = 4 pasos separados con timeline visual
  - v2 = 3 pasos en 1 página
  - ¿Adoptar diseño de new/ o mantener v2?

---

### 🗑️ ELIMINAR de static/new/ (ya migrados)

```
static/new/
├── home.html, home_d.html         → duplicado de index.html
├── help_center*.html              → duplicado de help-center/
├── signin.html, register.html     → duplicado de *_v2.html
├── about.html, contact*.html      → duplicado de *_v2.html
├── faq.html, blog*.html           → duplicado de *_v2.html
├── profile*.html                  → duplicado de profile_v2.html
├── integrations.html              → duplicado
├── visual_editor.html             → duplicado
├── experiment*.html               → duplicado
├── landing*.html                  → duplicado
├── 404/500/503*.html              → duplicado
└── about_faq-html                 → archivo con typo, eliminar
```

**Total: ~40 archivos a eliminar** tras confirmar que v2 funciona.

---

### 🔧 MEJORAS EN V2 EXISTENTES

| Página | Acción |
|--------|--------|
| `profile_v2.html` | Conectar a `/users/me` |
| `integrations_v2.html` | Crear endpoint `/integrations` |
| `calendar_v2.html` | Conectar a datos reales |
| `experiments_create_v2.html` | Considerar añadir timeline de new/ |

---

## Inventario Final

| Ubicación | Archivos | Acción |
|-----------|----------|--------|
| `static/*.html` v1 | ~20 | Eliminar tras validar v2 |
| `static/*_v2.html` | ~25 | ✅ Producción |
| `static/help-center/` | 10 | ✅ Completo |
| `static/new/*.html` | 51 | ~40 eliminar, ~6 decidir, ~5 crear |
