# 🎨 Frontend Architecture Guide

**Guía completa para desarrolladores de frontend**  
**Última actualización**: Diciembre 2024

---

## ⚠️ REGLA FUNDAMENTAL

> **Todas las páginas v2 DEBEN seguir la misma arquitectura.**
> Copiar el patrón de `experiments_v2.html`, no inventar nuevas formas.

---

## 📁 Estructura

```
static/
├── partials/                    # 🔴 OBLIGATORIO usar
│   ├── header_v2.html          
│   ├── sidebar_v2.html         
│   ├── modals_v2.html          
│   ├── toast_stack.html        # SOTA: Notificaciones premium
│   └── command_palette.html    # SOTA: Cmd+K navigation
├── js/
│   ├── include.js              # Procesa <include> tags
│   ├── alpine-store.js         # Estado global reactivo
│   ├── core/
│   │   └── api.js              # Cliente HTTP
│   ├── services/               # Capa de negocio (API calls)
│   │   ├── auth-service.js
│   │   ├── experiment-service.js
│   │   ├── billing-service.js
│   │   └── ...
│   └── pages/                  # Controladores por página
│       ├── dashboard_v2.js
│       ├── auth_v2.js
│       └── ...
├── *_v2.html                   # Páginas producción
└── *.html                      # Legacy v1 (deprecated)
```

---

## 🏗️ Estructura Obligatoria de Página v2

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sampelit | [Página]</title>
    
    <!-- Fonts (copiar exacto) -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
    
    <!-- Tailwind + Config (copiar exacto) -->
    <script src="https://cdn.tailwindcss.com?plugins=forms,typography,container-queries"></script>
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
                        text: { main: "#1E293B", muted: "#64748B" },
                        border: { light: "#E2E8F0" },
                        brand: { DEFAULT: '#3b82f6', 50: '#eff6ff', 500: '#3b82f6' }
                    },
                    fontFamily: { display: ['"Manrope"', 'sans-serif'] },
                },
            },
        };
    </script>
    
    <!-- Alpine + Include.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="js/include.js"></script>
</head>

<body x-data="{ page: 'nombre', sidebarToggle: false, darkMode: false }"
    x-init="darkMode = JSON.parse(localStorage.getItem('darkMode')) || false"
    :class="{ 'dark': darkMode }"
    class="bg-[#f8f9fc] dark:bg-gray-900 font-sans antialiased">
    
    <div class="flex h-screen overflow-hidden">
        <include src="./partials/sidebar_v2.html"></include>
        
        <div class="relative flex flex-1 flex-col overflow-y-auto bg-surface dark:bg-gray-900">
            <include src="./partials/header_v2.html"></include>
            
            <main>
                <div class="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
                    <!-- CONTENIDO AQUÍ -->
                </div>
            </main>
        </div>
    </div>

    <script src="js/core/api.js"></script>
    <include src="./partials/toast_v2.html"></include>
    <include src="./partials/modals_v2.html"></include>
</body>
</html>
```

---

## ✅ Checklist Antes de Commit

### Estructura Base
- [ ] `sidebar_v2.html` incluido
- [ ] `header_v2.html` incluido
- [ ] `toast_stack.html` al final (antes de `</body>`)
- [ ] `command_palette.html` al final (antes de `</body>`)
- [ ] `include.js` en `<head>`
- [ ] `x-data` en body con `sidebarToggle` y `darkMode`
- [ ] Dark mode funciona
- [ ] Responsive funciona

### SOTA UX (Obligatorio para GOLD STANDARD)
- [ ] Skeleton Loader mientras carga datos (`x-show="loading"`)
- [ ] Empty State si no hay datos (`x-if="data.length === 0"`)
- [ ] Transiciones suaves (`x-transition:enter`)
- [ ] Micro-interacciones en botones (`active:scale-95`)

---

## 📚 Archivos de Referencia

| Tipo de página | Copiar de |
|----------------|-----------|
| Lista/tabla | `experiments_v2.html` |
| Detalle | `experiment_detail_v2.html` |
| Formulario | `experiments_create_v2.html` |
| Dashboard | `index_v2.html` ← **GOLD STANDARD** |

---

## 🔗 Documentación Relacionada

- [Valor del Backend](../backend/valor_del_backend.md) - **LEER PRIMERO**
- [API Reference](../backend/api_reference.md)
- [Partials README](../../static/partials/README.md)
- [JS Modules README](../../static/js/README.md)

