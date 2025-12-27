# 🎨 Frontend Architecture Guide

**Versión**: 2.0  
**Última actualización**: Diciembre 2024  
**Nivel**: OBLIGATORIO para cualquier desarrollador 🔴

---

## ⚠️ REGLA FUNDAMENTAL

> **Todas las páginas v2 DEBEN seguir la misma arquitectura que las páginas existentes.**
> No inventes nuevas formas de hacer las cosas. Copia el patrón de `experiments_v2.html`.

---

## 📁 Estructura de Archivos

```
static/
├── partials/                    # 🔴 OBLIGATORIO usar estos
│   ├── header_v2.html          # Header con navegación
│   ├── sidebar_v2.html         # Sidebar con menú
│   ├── modals_v2.html          # Sistema de modales
│   └── toast_v2.html           # Notificaciones toast
├── js/
│   ├── include.js              # Procesa <include> tags
│   └── core/
│       ├── api.js              # Cliente API (APIClient)
│       ├── app.js              # Inicialización global
│       ├── state.js            # Estado global
│       └── utils.js            # Utilidades
├── *_v2.html                   # Páginas de producción v2
└── *.html                      # Páginas v1 (legacy)
```

---

## 🏗️ Anatomía de una Página v2 Correcta

### Estructura Obligatoria

```html
<!DOCTYPE html>
<html lang="en">

<head>
    <!-- 1️⃣ META TAGS OBLIGATORIOS -->
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sampelit | [Nombre de Página]</title>
    
    <!-- 2️⃣ FONTS (copiar exacto) -->
    <link href="https://fonts.googleapis.com" rel="preconnect" />
    <link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&amp;family=Manrope:wght@300;400;500;600;700;800&amp;display=swap" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet" />
    
    <!-- 3️⃣ TAILWIND CDN (copiar exacto) -->
    <script src="https://cdn.tailwindcss.com?plugins=forms,typography,container-queries"></script>
    
    <!-- 4️⃣ TAILWIND CONFIG (copiar exacto) -->
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        background: "#FFFFFF",
                        surface: "#FAFAFA",
                        primary: "#0f172a",
                        accent: "#1e3a8a",
                        "primary-light": "#3b82f6",
                        text: { main: "#1E293B", muted: "#64748B", dim: "#94A3B8" },
                        border: { light: "#E2E8F0", subtle: "#F1F5F9" },
                        brand: { DEFAULT: '#3b82f6', 50: '#eff6ff', 500: '#3b82f6', 600: '#2563eb' },
                        success: { 50: '#ecfdf5', 500: '#10b981', 600: '#059669' },
                        error: { 50: '#fef2f2', 500: '#ef4444', 600: '#dc2626' }
                    },
                    fontFamily: { display: ['"Manrope"', 'sans-serif'], body: ['"Inter"', 'sans-serif'] },
                },
            },
        };
    </script>
    
    <!-- 5️⃣ ALPINE.JS (copiar exacto) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    
    <!-- 6️⃣ INCLUDE.JS (copiar exacto) -->
    <script src="js/include.js"></script>
</head>

<body x-data="{ page: 'nombre-pagina', sidebarToggle: false, darkMode: false }"
    x-init="darkMode = JSON.parse(localStorage.getItem('darkMode')) || false; $watch('darkMode', value => localStorage.setItem('darkMode', JSON.stringify(value)))"
    :class="{ 'dark': darkMode === true }"
    class="bg-[#f8f9fc] dark:bg-gray-900 text-text-main dark:text-gray-300 font-sans antialiased">
    
    <div class="flex h-screen overflow-hidden">
        <!-- 7️⃣ SIDEBAR (obligatorio) -->
        <include src="./partials/sidebar_v2.html"></include>

        <div class="relative flex flex-1 flex-col overflow-y-auto overflow-x-hidden bg-surface dark:bg-gray-900">
            <!-- 8️⃣ HEADER (obligatorio) -->
            <include src="./partials/header_v2.html"></include>

            <main>
                <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
                    <!-- 9️⃣ TU CONTENIDO AQUÍ -->
                </div>
            </main>
        </div>
    </div>

    <!-- 🔟 SCRIPTS AL FINAL -->
    <script src="js/core/api.js"></script>
    
    <!-- Toast y Modals (siempre al final) -->
    <include src="./partials/toast_v2.html"></include>
    <include src="./partials/modals_v2.html"></include>
</body>

</html>
```

---

## 🚨 ERRORES COMUNES (NO HACER)

### ❌ Error 1: No usar partials

```html
<!-- ❌ MAL: Header copiado inline -->
<header class="sticky top-0...">
    <!-- 200 líneas de código repetido -->
</header>

<!-- ✅ BIEN: Usar include -->
<include src="./partials/header_v2.html"></include>
```

### ❌ Error 2: Olvidar include.js

```html
<!-- ❌ MAL: Sin include.js, los <include> no funcionan -->
<head>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs..."></script>
</head>

<!-- ✅ BIEN: Siempre añadir include.js -->
<head>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs..."></script>
    <script src="js/include.js"></script>
</head>
```

### ❌ Error 3: Tailwind config diferente

```html
<!-- ❌ MAL: Colores diferentes -->
<script>
    tailwind.config = {
        theme: {
            extend: {
                colors: {
                    primary: "#ff0000",  // Color inventado
                },
            },
        },
    };
</script>

<!-- ✅ BIEN: Copiar config exacto de experiments_v2.html -->
```

### ❌ Error 4: Estructura body diferente

```html
<!-- ❌ MAL: Sin x-data en body -->
<body class="bg-white">
    <include src="./partials/sidebar_v2.html"></include>
    ...
</body>

<!-- ✅ BIEN: Con x-data para Alpine -->
<body x-data="{ page: 'mi-pagina', sidebarToggle: false, darkMode: false }"
    x-init="darkMode = JSON.parse(localStorage.getItem('darkMode')) || false"
    :class="{ 'dark': darkMode === true }"
    class="bg-[#f8f9fc] dark:bg-gray-900 text-text-main dark:text-gray-300 font-sans antialiased">
```

---

## 🧩 Componentes Alpine.js

### Patrón: Función que retorna objeto

```html
<!-- En el HTML -->
<div x-data="miComponente()">
    <template x-for="item in items">
        <p x-text="item.name"></p>
    </template>
</div>

<!-- Script al final del body -->
<script>
function miComponente() {
    return {
        // Estado
        items: [],
        loading: false,
        
        // Inicialización
        async init() {
            this.client = new APIClient();
            await this.fetchData();
        },
        
        // Métodos
        async fetchData() {
            this.loading = true;
            try {
                const response = await this.client.get('/mi-endpoint');
                this.items = response.data;
            } catch (error) {
                console.error('Error:', error);
            } finally {
                this.loading = false;
            }
        },
        
        // Computed properties (getters)
        get filteredItems() {
            return this.items.filter(i => i.active);
        }
    };
}
</script>
```

---

## 📡 API Client

### Ubicación: `js/core/api.js`

```javascript
// Usar siempre APIClient para requests
const client = new APIClient();

// GET
const response = await client.get('/experiments');

// POST
const created = await client.post('/experiments', {
    name: 'Mi Experimento',
    variants: [...]
});

// PATCH
await client.patch(`/experiments/${id}`, { status: 'active' });

// DELETE
await client.delete(`/experiments/${id}`);
```

---

## 🎨 Clases CSS Estándar

### Cards

```html
<div class="overflow-hidden rounded-[32px] border border-gray-200 bg-white shadow-premium dark:border-white/5 dark:bg-white/[0.03]">
    <!-- Card content -->
</div>
```

### Botones

```html
<!-- Primario -->
<button class="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-5 py-3 text-sm font-bold text-white transition-all hover:bg-black hover:shadow-xl dark:bg-white dark:text-gray-900">
    Acción Principal
</button>

<!-- Secundario -->
<button class="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-5 py-3 text-sm font-bold text-gray-700 transition-all hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-white">
    Acción Secundaria
</button>
```

### Inputs

```html
<input type="text" placeholder="Buscar..."
    class="h-11 w-full rounded-2xl border border-gray-100 bg-gray-50 pl-12 pr-6 text-sm transition-all focus:bg-white focus:ring-4 focus:ring-brand-500/5 focus:border-brand-500/20 dark:border-white/5 dark:bg-white/5 dark:text-white" />
```

### Status Badges

```html
<!-- Running -->
<div class="flex items-center gap-2">
    <div class="h-1.5 w-1.5 rounded-full bg-emerald-500"></div>
    <span class="text-[11px] font-bold uppercase tracking-wider text-emerald-600">Running</span>
</div>

<!-- Paused -->
<div class="flex items-center gap-2">
    <div class="h-1.5 w-1.5 rounded-full bg-amber-500"></div>
    <span class="text-[11px] font-bold uppercase tracking-wider text-amber-600">Paused</span>
</div>
```

---

## ✅ Checklist Antes de Commit

Antes de hacer commit de una página v2, verifica:

- [ ] `<include src="./partials/sidebar_v2.html">` presente
- [ ] `<include src="./partials/header_v2.html">` presente
- [ ] `<include src="./partials/toast_v2.html">` al final
- [ ] `<include src="./partials/modals_v2.html">` al final
- [ ] `<script src="js/include.js">` en `<head>`
- [ ] `x-data` en `<body>` con `sidebarToggle` y `darkMode`
- [ ] Tailwind config copiado exacto
- [ ] Fonts copiados exacto
- [ ] Dark mode funciona (`:class="{ 'dark': darkMode }"`)
- [ ] Responsive funciona (probar en móvil)

---

## 📚 Archivos de Referencia

Cuando tengas dudas, copia de estos archivos:

| Tipo | Archivo de referencia |
|------|----------------------|
| Lista/tabla de datos | `experiments_v2.html` |
| Detalle de item | `experiment_detail_v2.html` |
| Formulario de creación | `experiments_create_v2.html` |
| Dashboard | `index_v2.html` |
| Perfil/settings | `profile_v2.html` |

---

## 🔧 Cómo crear una nueva página v2

1. **Copiar** `experiments_v2.html` como base
2. **Renombrar** a `mi_pagina_v2.html`
3. **Cambiar** el `<title>`
4. **Cambiar** el breadcrumb
5. **Cambiar** `page: 'experiments'` → `page: 'mi-pagina'` en `x-data`
6. **Reemplazar** contenido del `<main>`
7. **Mantener** TODO lo demás igual

---

## ⚡ Quick Reference: Include Tags

```html
<!-- Sidebar con menú principal -->
<include src="./partials/sidebar_v2.html"></include>

<!-- Header con búsqueda y user menu -->
<include src="./partials/header_v2.html"></include>

<!-- Sistema de notificaciones toast -->
<include src="./partials/toast_v2.html"></include>

<!-- Modales globales (confirm, delete, etc) -->
<include src="./partials/modals_v2.html"></include>
```

