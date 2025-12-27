# UI Specs - Profile / Settings

**Archivo**: `profile_v2.html`  
**Endpoint**: `GET/PATCH /api/v1/users/me`

---

## Job del Usuario

> "Quiero gestionar mi cuenta y seguridad en un solo lugar"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Command Center → Profile                                          │
│                                                                     │
│  Profile Settings                                                   │
│  Manage your account details and security preferences.             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  [Avatar]  John Doe                                          │  │
│  │            john@example.com                                  │  │
│  │            ✓ Pro Plan                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────┐  ┌───────────────────────┐              │
│  │ Personal Information  │  │ Security              │              │
│  │                       │  │                       │              │
│  │ First Name: [John___] │  │ Current: [••••••••]  │              │
│  │ Last Name:  [Doe____] │  │ New:     [••••••••]  │              │
│  │ Email:      [j@ex...] │  │ Confirm: [••••••••]  │              │
│  │                       │  │                       │              │
│  │ [Save Changes]        │  │ [Update Password]    │              │
│  └───────────────────────┘  └───────────────────────┘              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Danger Zone                                                  │  │
│  │                                                              │  │
│  │ [Delete Account]  This action cannot be undone               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Secciones

### 1. Personal Information
- First Name
- Last Name  
- Email (verificado)

### 2. Security
- Change Password
- Two-Factor Auth (futuro)

### 3. Billing (futuro)
- Plan actual
- Historial de pagos
- Cambiar plan

### 4. Danger Zone
- Delete Account

---

## API

### `GET /api/v1/users/me`

```json
{
  "id": "user_001",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "plan": "pro",
  "email_verified": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### `PATCH /api/v1/users/me`

```json
{
  "first_name": "John",
  "last_name": "Smith"
}
```

### `POST /api/v1/users/me/change-password`

```json
{
  "current_password": "...",
  "new_password": "..."
}
```

---

## Estado Actual

⚠️ **Página con datos mock hardcoded**. Requiere:

1. Conectar a endpoint `/users/me`
2. Implementar save con PATCH
3. Implementar cambio de password
4. Validación de formularios

---

## Prioridad

**Baja** - Nice to have, no bloquea funcionalidad core.
