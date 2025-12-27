# 🌐 API Reference (REST Endpoints)

**Versión**: 1.0  
**Última actualización**: Diciembre 2024  
**Nivel**: Beginner-friendly 🟢

---

## 🎯 Introducción

Esta documentación describe todos los endpoints REST del backend de Samplit. La API sigue principios RESTful y usa JSON para request/response.

**Base URL**: `/api/v1`

**Autenticación**: JWT Bearer Token (excepto endpoints públicos)

```bash
# Ejemplo de request autenticada
curl -X GET "http://localhost:8000/api/v1/experiments" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiI..."
```

---

## 📁 Estructura de Routers

```
public_api/routers/
├── analytics.py          # Análisis de experimentos
├── audit.py              # Trail de auditoría
├── auth.py               # Autenticación (login, registro)
├── blog.py               # Blog público
├── dashboard.py          # Dashboard de usuario
├── demo.py               # Demo pública
├── downloads.py          # Exportación de datos
├── experiments.py        # CRUD de experimentos
├── experiments_multi_element.py  # Experimentos multi-elemento
├── funnels.py            # Embudos de conversión
├── installations.py      # Instalación de snippets
├── integrations.py       # OAuth (Shopify, WordPress)
├── leads.py              # Captura de leads
├── onboarding.py         # Onboarding de usuarios
├── proxy.py              # Proxy para Visual Editor
├── public_dashboard.py   # Dashboard público (share)
├── simulator.py          # Simulador de experimentos
├── subscriptions.py      # Planes y pagos
├── system.py             # Health checks
├── tracker.py            # SDK tracking (assign/convert)
├── traffic_filters.py    # Reglas de exclusión
└── visual_editor.py      # Editor visual
```

---

## 🔐 Auth (`/api/v1/auth`)

### POST `/auth/register`

Registra un nuevo usuario.

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "usuario@ejemplo.com",
  "password": "contraseña_segura_123",
  "full_name": "Juan García"
}
```

**Response 201 Created:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@ejemplo.com",
  "full_name": "Juan García",
  "role": "client",
  "created_at": "2024-12-27T10:00:00Z"
}
```

**Errores:**
- `400 Bad Request`: Email ya registrado
- `422 Unprocessable Entity`: Validación fallida

---

### POST `/auth/login`

Inicia sesión y obtiene JWT token.

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=usuario@ejemplo.com&password=contraseña_segura_123
```

🎓 **NOTA**: El endpoint usa `username` (no `email`) por compatibilidad con OAuth2.

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errores:**
- `401 Unauthorized`: Credenciales incorrectas

---

### GET `/auth/me`

Obtiene información del usuario autenticado.

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Response 200 OK:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@ejemplo.com",
  "full_name": "Juan García",
  "company": "Mi Empresa S.L.",
  "role": "client",
  "created_at": "2024-12-27T10:00:00Z"
}
```

---

## 📊 Experiments (`/api/v1/experiments`)

### GET `/experiments`

Lista todos los experimentos del usuario.

```http
GET /api/v1/experiments?status=active&page=1&per_page=20
Authorization: Bearer <token>
```

**Query Parameters:**
| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `status` | string | - | Filtrar: draft, active, paused, completed, archived |
| `page` | int | 1 | Página actual |
| `per_page` | int | 20 | Items por página (max 100) |

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "exp-123",
      "name": "Test CTA Homepage",
      "status": "active",
      "created_at": "2024-12-20T08:00:00Z",
      "started_at": "2024-12-21T10:00:00Z",
      "traffic_allocation": 1.0,
      "stats": {
        "total_visitors": 1500,
        "total_conversions": 120,
        "conversion_rate": 0.08
      }
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### POST `/experiments`

Crea un nuevo experimento.

```http
POST /api/v1/experiments
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Test Botón Comprar",
  "description": "A/B test del CTA principal",
  "target_url": "https://mitienda.com/producto",
  "traffic_allocation": 1.0,
  "variants": [
    {
      "name": "Control",
      "content": {"text": "Comprar ahora"},
      "is_control": true
    },
    {
      "name": "Variante B",
      "content": {"text": "¡Añadir al carrito!"}
    }
  ]
}
```

**Response 201 Created:**
```json
{
  "id": "exp-456",
  "name": "Test Botón Comprar",
  "status": "draft",
  "created_at": "2024-12-27T10:00:00Z",
  "elements": [
    {
      "id": "elem-789",
      "name": "Element: Test Botón Comprar",
      "variants": [
        {"id": "var-001", "name": "Control", "is_control": true},
        {"id": "var-002", "name": "Variante B", "is_control": false}
      ]
    }
  ]
}
```

---

### GET `/experiments/{experiment_id}`

Obtiene detalles de un experimento.

```http
GET /api/v1/experiments/exp-456
Authorization: Bearer <token>
```

**Response 200 OK:**
```json
{
  "id": "exp-456",
  "name": "Test Botón Comprar",
  "description": "A/B test del CTA principal",
  "status": "active",
  "target_url": "https://mitienda.com/producto",
  "traffic_allocation": 1.0,
  "created_at": "2024-12-27T10:00:00Z",
  "started_at": "2024-12-27T11:00:00Z",
  "elements": [...],
  "stats": {
    "total_visitors": 500,
    "total_conversions": 45,
    "conversion_rate": 0.09
  }
}
```

---

### PATCH `/experiments/{experiment_id}/status`

Cambia el estado de un experimento.

```http
PATCH /api/v1/experiments/exp-456/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "active"
}
```

**Estados válidos:**
| Estado actual | Estados permitidos |
|---------------|-------------------|
| `draft` | `active` |
| `active` | `paused`, `completed` |
| `paused` | `active`, `completed` |
| `completed` | `archived` |

**Response 200 OK:**
```json
{
  "id": "exp-456",
  "status": "active",
  "started_at": "2024-12-27T11:00:00Z"
}
```

---

### DELETE `/experiments/{experiment_id}`

Archiva un experimento (soft delete).

```http
DELETE /api/v1/experiments/exp-456
Authorization: Bearer <token>
```

**Response 204 No Content**

---

## 📈 Analytics (`/api/v1/analytics`)

### GET `/analytics/experiment/{experiment_id}`

Obtiene análisis estadístico completo.

```http
GET /api/v1/analytics/experiment/exp-456
Authorization: Bearer <token>
```

**Response 200 OK:**
```json
{
  "experiment_id": "exp-456",
  "analyzed_at": "2024-12-27T12:00:00Z",
  "total_allocations": 3000,
  "total_conversions": 270,
  "overall_conversion_rate": 0.09,
  "variants": [
    {
      "id": "var-001",
      "name": "Control",
      "allocations": 1500,
      "conversions": 120,
      "conversion_rate": 0.08,
      "confidence_interval": {
        "lower": 0.067,
        "upper": 0.095
      },
      "uplift_percent": 0,
      "is_statistically_significant": false
    },
    {
      "id": "var-002",
      "name": "Variante B",
      "allocations": 1500,
      "conversions": 150,
      "conversion_rate": 0.10,
      "confidence_interval": {
        "lower": 0.085,
        "upper": 0.117
      },
      "uplift_percent": 25.0,
      "is_statistically_significant": true
    }
  ],
  "bayesian_analysis": {
    "method": "bayesian_monte_carlo",
    "variants": [
      {"variant_id": "var-002", "win_probability": 0.92},
      {"variant_id": "var-001", "win_probability": 0.08}
    ],
    "leader": {
      "variant_id": "var-002",
      "variant_name": "Variante B",
      "confidence": 0.92
    },
    "is_conclusive": false
  },
  "recommendations": {
    "action": "CONSIDERAR_IMPLEMENTAR",
    "reason": "Variante B lidera con 92% de confianza...",
    "urgency": "low"
  }
}
```

---

## 🎯 Tracker (`/api/v1/tracker`)

Endpoints usados por el SDK JavaScript (tracker.js).

### POST `/tracker/assign`

Asigna un visitante a una variante.

```http
POST /api/v1/tracker/assign
Content-Type: application/json

{
  "experiment_id": "exp-456",
  "visitor_id": "browser_abc123",
  "session_id": "session_xyz",
  "context": {
    "url": "https://mitienda.com/producto",
    "device": "mobile",
    "browser": "Chrome"
  }
}
```

**Response 200 OK:**
```json
{
  "experiment_id": "exp-456",
  "variant_id": "var-002",
  "variant_name": "Variante B",
  "content": {
    "text": "¡Añadir al carrito!"
  },
  "is_new_assignment": true,
  "assignment_id": "assign-789"
}
```

🎓 **Sticky Bucketing**: Si el visitante ya fue asignado, siempre recibe la misma variante.

---

### POST `/tracker/convert`

Registra una conversión.

```http
POST /api/v1/tracker/convert
Content-Type: application/json

{
  "experiment_id": "exp-456",
  "visitor_id": "browser_abc123",
  "conversion_value": 1.0,
  "metadata": {
    "product_id": "SKU-123",
    "action": "add_to_cart"
  }
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "conversion_id": "conv-456",
  "message": "Conversion recorded"
}
```

---

### GET `/tracker/experiments/active`

Obtiene experimentos activos para un dominio.

```http
GET /api/v1/tracker/experiments/active?domain=mitienda.com
```

**Response 200 OK:**
```json
{
  "experiments": [
    {
      "id": "exp-456",
      "name": "Test Botón Comprar",
      "target_url": "https://mitienda.com/producto",
      "elements": [...]
    }
  ]
}
```

---

## 🔧 Visual Editor (`/api/v1/visual-editor`)

### GET `/visual-editor/proxy`

Proxy para cargar sitios en el editor visual.

```http
GET /api/v1/visual-editor/proxy?url=https://mitienda.com
Authorization: Bearer <token>
```

**Response 200 OK:**
```html
<!DOCTYPE html>
<html>
<!-- Contenido del sitio con script del editor inyectado -->
<script src="/static/js/editor-client.js"></script>
</html>
```

---

### POST `/visual-editor/save-elements`

Guarda elementos seleccionados como experimento.

```http
POST /api/v1/visual-editor/save-elements
Authorization: Bearer <token>
Content-Type: application/json

{
  "experiment_name": "Test Visual Homepage",
  "page_url": "https://mitienda.com",
  "elements": [
    {
      "selector": "#cta-button",
      "selector_type": "css",
      "element_type": "button",
      "original_content": {"text": "Comprar"},
      "variants": [
        {"name": "Control", "content": {"text": "Comprar"}},
        {"name": "Variante B", "content": {"text": "¡Comprar ahora!"}}
      ]
    }
  ]
}
```

---

## 📥 Downloads (`/api/v1/downloads`)

### GET `/downloads/experiment/{experiment_id}/csv`

Descarga datos del experimento en CSV.

```http
GET /api/v1/downloads/experiment/exp-456/csv
Authorization: Bearer <token>
```

**Response 200 OK:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="experiment_exp-456_2024-12-27.csv"

variant_name,allocations,conversions,conversion_rate
Control,1500,120,0.08
Variante B,1500,150,0.10
```

---

### GET `/downloads/experiment/{experiment_id}/excel`

Descarga datos del experimento en Excel.

```http
GET /api/v1/downloads/experiment/exp-456/excel
Authorization: Bearer <token>
```

**Response 200 OK:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="experiment_exp-456_2024-12-27.xlsx"
```

---

## 📋 Audit (`/api/v1/audit`)

### GET `/audit/experiments/{experiment_id}`

Obtiene el trail de auditoría de un experimento.

```http
GET /api/v1/audit/experiments/exp-456?limit=50
Authorization: Bearer <token>
```

**Response 200 OK:**
```json
{
  "experiment_id": "exp-456",
  "entries": [
    {
      "sequence_number": 1,
      "decision_type": "experiment_created",
      "decision_data": {...},
      "timestamp": "2024-12-27T10:00:00Z",
      "hash": "sha256:abc123..."
    },
    {
      "sequence_number": 2,
      "decision_type": "assignment",
      "decision_data": {...},
      "timestamp": "2024-12-27T10:05:00Z",
      "previous_hash": "sha256:abc123...",
      "hash": "sha256:def456..."
    }
  ],
  "chain_valid": true
}
```

🎓 **Hash Chain**: Cada entrada contiene el hash de la anterior, formando una cadena inmutable (como blockchain simplificado).

---

### GET `/audit/experiments/{experiment_id}/verify`

Verifica la integridad de la cadena de auditoría.

```http
GET /api/v1/audit/experiments/exp-456/verify
Authorization: Bearer <token>
```

**Response 200 OK:**
```json
{
  "experiment_id": "exp-456",
  "total_entries": 1253,
  "chain_valid": true,
  "first_entry_hash": "sha256:abc...",
  "last_entry_hash": "sha256:xyz...",
  "verified_at": "2024-12-27T12:00:00Z"
}
```

---

## ❤️ System (`/api/v1/system`)

### GET `/system/health`

Health check del sistema.

```http
GET /api/v1/system/health
```

**Response 200 OK:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "uptime_seconds": 86400
}
```

---

## ⚠️ Códigos de Error

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| `400` | Bad Request | Parámetros inválidos |
| `401` | Unauthorized | Token missing/expirado |
| `403` | Forbidden | Sin permisos |
| `404` | Not Found | Recurso no existe |
| `422` | Unprocessable Entity | Validación fallida |
| `429` | Too Many Requests | Rate limit |
| `500` | Internal Server Error | Error del servidor |

**Formato de error estándar:**
```json
{
  "detail": "Experiment not found",
  "error_code": "EXP_NOT_FOUND",
  "request_id": "req-abc123"
}
```

---

## 🔒 Rate Limiting

| Endpoint | Límite |
|----------|--------|
| `/auth/*` | 10 req/min |
| `/tracker/*` | 1000 req/min |
| Otros | 100 req/min |

Headers de rate limit:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703678400
```

