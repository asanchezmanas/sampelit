# 📦 Partials Reference

**Versión**: 2.0  
**Nivel**: Referencia rápida

---

## 📁 Archivos Disponibles

```
partials/
├── header_v2.html          # ✅ Usar en todas las páginas v2
├── sidebar_v2.html         # ✅ Usar en todas las páginas v2
├── modals_v2.html          # ✅ Usar al final del body
├── toast_v2.html           # ✅ Usar al final del body
├── header_landing_v2.html  # Para páginas públicas (sin login)
├── footer_landing_v2.html  # Para páginas públicas
├── header.html             # ⚠️ Legacy v1 - no usar en v2
├── sidebar.html            # ⚠️ Legacy v1 - no usar en v2
└── header_landing.html     # ⚠️ Legacy v1
```

---

## 🔷 sidebar_v2.html

**Uso**: Menú lateral de navegación

**Variables Alpine requeridas en `<body>`**:
- `sidebarToggle` - controla expandir/colapsar
- `page` - página actual para highlight

```html
<body x-data="{ page: 'experiments', sidebarToggle: false, darkMode: false }">
    <div class="flex h-screen overflow-hidden">
        <include src="./partials/sidebar_v2.html"></include>
        ...
    </div>
</body>
```

**Menú items definidos dentro del partial**. Para añadir nuevos items, editar `sidebar_v2.html`.

---

## 🔷 header_v2.html

**Uso**: Barra superior con búsqueda, notificaciones, user menu

**Variables Alpine requeridas**:
- `sidebarToggle` - para el botón hamburger
- `darkMode` - para el toggle de tema

**Contiene**:
- Botón hamburger (toggle sidebar)
- Input de búsqueda (desktop)
- Dropdown de notificaciones
- Toggle dark/light mode
- Dropdown de usuario con logout

---

## 🔷 modals_v2.html

**Uso**: Sistema de modales reutilizables

**Cómo abrir un modal**:
```html
<button @click="$dispatch('open-modal', 'confirm-delete')">
    Eliminar
</button>
```

**Modales disponibles**:
- `confirm-delete` - Confirmación de eliminación
- `success` - Mensaje de éxito
- Puedes añadir más editando el archivo

---

## 🔷 toast_v2.html

**Uso**: Notificaciones toast

**Cómo mostrar un toast**:
```javascript
// Desde Alpine.js
$dispatch('show-toast', { 
    type: 'success', // success, error, warning, info
    message: 'Operación completada' 
});
```

---

## 🔷 header_landing_v2.html + footer_landing_v2.html

**Uso**: Solo para páginas públicas (landing, pricing, about)

```html
<!-- Para páginas de marketing/públicas -->
<body>
    <include src="./partials/header_landing_v2.html"></include>
    
    <main>
        <!-- Contenido -->
    </main>
    
    <include src="./partials/footer_landing_v2.html"></include>
</body>
```

---

## ⚠️ Reglas

1. **Páginas de app** (dashboard, experiments, settings):
   - Usar `sidebar_v2.html` + `header_v2.html`
   
2. **Páginas públicas** (landing, pricing):
   - Usar `header_landing_v2.html` + `footer_landing_v2.html`

3. **Siempre incluir al final**:
   - `toast_v2.html`
   - `modals_v2.html`

