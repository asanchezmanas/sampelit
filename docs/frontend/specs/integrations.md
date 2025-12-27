# UI Specs - Integrations

**Archivo**: `integrations_v2.html`  
**Endpoint**: `GET /api/v1/integrations` (pendiente)

---

## Job del Usuario

> "Quiero conectar mis herramientas existentes sin complicaciones"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Command Center → Integrations                                     │
│                                                                     │
│  Integrations                                                       │
│  Connect your favorite tools and services.                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [All] [E-commerce] [Marketing] [CMS]                              │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ 📊 Google       │  │ 🛒 Shopify      │  │ 📧 Mailchimp    │     │
│  │    Analytics    │  │                 │  │                 │     │
│  │                 │  │                 │  │                 │     │
│  │ Sync your GA    │  │ E-commerce      │  │ Sync email      │     │
│  │ metrics         │  │ events          │  │ campaigns       │     │
│  │                 │  │                 │  │                 │     │
│  │ ⚙️ Settings     │  │ 🟢 Connected    │  │ ⚫ Not setup    │     │
│  │ [Toggle: ON]    │  │ [Toggle: ON]    │  │ [Connect]       │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ 📝 WordPress    │  │ 🔍 GTM          │  │ 💬 Slack        │     │
│  │                 │  │                 │  │                 │     │
│  │ CMS sync        │  │ Tag manager     │  │ Notifications   │     │
│  │                 │  │ integration     │  │                 │     │
│  │ [Connect]       │  │ [Connect]       │  │ [Connect]       │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Integraciones Disponibles

| Integración | Categoría | Estado | Endpoint |
|-------------|-----------|--------|----------|
| Google Analytics | Analytics | ✅ Implementado | OAuth flow |
| Shopify | E-commerce | ✅ Implementado | `/integrations/shopify` |
| WooCommerce | E-commerce | ⚠️ Pendiente | - |
| WordPress | CMS | ✅ Implementado | OAuth flow |
| Mailchimp | Marketing | ⚠️ Pendiente | - |
| GTM | Analytics | ⚠️ Pendiente | - |
| Slack | Notifications | ⚠️ Pendiente | - |

---

## API (Propuesta)

### `GET /api/v1/integrations`

```json
{
  "integrations": [
    {
      "id": "google_analytics",
      "name": "Google Analytics",
      "category": "analytics",
      "is_connected": true,
      "connected_at": "2024-12-20T10:00:00Z",
      "config": { "tracking_id": "UA-XXXXX" }
    }
  ]
}
```

### `POST /api/v1/integrations/{id}/connect`

Inicia OAuth flow o guarda API keys.

### `DELETE /api/v1/integrations/{id}/disconnect`

Desconecta integración.

---

## Estado Actual

⚠️ **Página estática con datos mock**. Requiere:

1. Crear endpoint `/integrations`
2. Implementar flujo OAuth para cada servicio
3. Almacenar tokens en DB

---

## Prioridad

**Media** - Importante para retención pero no bloquea core functionality.
