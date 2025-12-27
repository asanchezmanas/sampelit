# 📚 Frontend Documentation

Documentación del frontend de Sampelit V2.

---

## 📖 Documentos

| Documento | Descripción |
|-----------|-------------|
| **[🎯 UI Specifications](./ui_specifications.md)** | **CRÍTICO** - Principios de diseño business-first |
| **[📋 Specs por Vista](./specs/)** | Wireframes y mapeo API por cada vista |
| **[🚀 Migration Plan](./migration_plan.md)** | Estado V1 vs V2, plan archivo por archivo + **SOTA Matrix** |
| [Architecture](./architecture.md) | Estructura obligatoria para páginas v2 |
| [Valor del Backend](../backend/valor_del_backend.md) | Potencial del backend para frontend |

---

## 💎 SOTA UX Features (State of the Art)

El frontend implementa características de nivel **Senior Top-Tier**:

| Feature | Descripción | Ubicación |
|---------|-------------|-----------|
| **Skeleton Loaders** | Zero Layout Shift - bloques grises pulsantes | Dashboard, Lists, Analytics, Billing |
| **Empty States** | Ilustraciones + CTA cuando no hay datos | Experiment List, Billing, Analytics |
| **Shake on Error** | Feedback visceral en login fallido | `auth_v2.js` |
| **Step Transitions** | Slide animado entre pasos | Wizard |
| **Toast Stack** | Notificaciones premium con progress bar | `partials/toast_stack.html` |
| **Command Palette** | Cmd+K para navegación rápida | `partials/command_palette.html` |

---

## ⚡ Quick Start

1. **Leer** [UI Specifications](./ui_specifications.md) - wireframes de cada vista
2. **Leer** [Valor del Backend](../backend/valor_del_backend.md) - qué hace especial Sampelit
3. **Seguir** [Architecture](./architecture.md) - cómo estructurar código

---

## 📁 Ubicación de Archivos

Los archivos frontend están en `static/`:

```
static/
├── *_v2.html           # Páginas de producción
├── partials/           # Componentes reutilizables
│   ├── sidebar_v2.html
│   ├── header_v2.html
│   ├── toast_stack.html     # SOTA: Notificaciones premium
│   └── command_palette.html # SOTA: Cmd+K navigation
├── js/
│   ├── core/api.js          # HTTP Client
│   ├── services/            # Capa de negocio
│   ├── alpine-store.js      # Estado global
│   └── pages/*_v2.js        # Controladores por página
└── css/                     # Estilos
```

Ver READMEs en cada carpeta para más detalles.
