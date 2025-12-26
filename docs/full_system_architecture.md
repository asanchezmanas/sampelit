# Full System Architecture & API Integration Map

This document serves as the "Source of Truth" for connecting the Sampelit Frontend (V2) with the FastAPI Backend. It maps every user-facing page to its underlying API logic.

---

## 🏗️ System Overview

- **Frontend**: HTML5 + Tailwind CSS + Alpine.js (served via `static/` or Jinja2 templates).
- **Backend Service**: FastAPI (`public_api` module).
- **Database**: PostgreSQL (via `data_access` layer).
- **Auth**: JWT (Bearer Token).

---

## 1. Authentication & Identity
*Logic*: `public_api/routers/auth.py`

| Page (V2) | Page (V1) | Action | Endpoint | Method | Payload |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `signin_v2.html` | `signin.html` | **Login** | `/api/v1/auth/login` | `POST` | `{email, password}` |
| `signup_v2.html` | `signup.html` | **Register** | `/api/v1/auth/register` | `POST` | `{email, password, name, role}` |
| Global | Global | **Verify Session** | `/api/v1/auth/me` | `GET` | Header: `Authorization: Bearer <token>` |

---

## 2. Onboarding Flow
*Logic*: `public_api/routers/onboarding.py`

| Page (V2) | Page (V1) | Action | Endpoint | Method | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `onboarding/*.html` | `onboarding/*.html` | **Get Status** | `/api/v1/onboarding/status` | `GET` | Returns current step & completion status |
| `onboarding/install.html`| `onboarding/install.html` | **Update Step** | `/api/v1/onboarding/update-step` | `POST` | `{step: "install"}` |
| `onboarding/verify.html`| `onboarding/verify.html` | **Verify Install**| `/api/v1/onboarding/verify-installation` | `POST` | Triggers remote crawler to check snippet |
| `onboarding/complete.html`| `onboarding/complete.html`| **Complete** | `/api/v1/onboarding/complete` | `POST` | Unlocks dashboard |

---

## 3. Core Dashboard & Analytics
*Logic*: `public_api/routers/dashboard.py`

| Page (V2) | Page (V1) | Action | Endpoint | Method | Integration Gap |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `index_v2.html` | `dashboard.html` | **Get Overview** | `/api/v1/dashboard/` | `GET` | ✅ Fully Supported |
| `index_v2.html` | `dashboard.html` | **Activity Feed**| `/api/v1/dashboard/activity` | `GET` | ✅ Fully Supported |

---

## 4. Experimentation Engine
*Logic*: `public_api/routers/experiments.py`

| Page (V2) | Page (V1) | Action | Endpoint | Method | Integration Gap |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `experiments_v2.html`| `experiments.html`| **List All** | `/api/v1/experiments/` | `GET` | ✅ Supported |
| `modals_v2.html` | *Inline* | **Create New** | `/api/v1/experiments/` | `POST` | ✅ Supported |
| `experiment_detail_v2.html`| `experiment-detail.html`| **Get Details** | `/api/v1/experiments/{id}` | `GET` | ✅ Supported (Hierarchical Data) |
| `experiment_detail_v2.html`| *N/A* | **Get Charts** | **MISSING** | `GET` | 🔴 **CRITICAL GAP**: No endpoint for time-series data (daily conversions) |
| `experiment_detail_v2.html`| *N/A* | **Pause/Resume**| `/api/v1/experiments/{id}/status` | `PATCH`| ✅ Supported |

---

## 5. Visual Editor & Builder
*Logic*: `public_api/routers/visual_editor.py` & `public_api/routers/funnels.py`

| Page (V2) | Page (V1) | Action | Endpoint | Method | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `visual_editor_v2.html`| `visual-editor.html`| **Proxy Site** | `/api/v1/visual-editor/proxy` | `GET` | Creates iframe tunnel |
| `visual_editor_v2.html`| `visual-editor.html`| **Save Draft** | `/api/v1/visual-editor/save-elements`| `POST`| Converts DOM selection to experiment variables |
| `funnel_builder_v2.html`| `funnel-builder.html`| **Save Funnel**| `/api/v1/funnels/` | `POST` | Saves canvas node graph |

---

## 6. Simulation & Demos
*Logic*: `public_api/routers/simulator.py` & `public_api/routers/demo.py`

| Page (V1 - No V2 yet) | Action | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- | :--- |
| `simulator-landing.html` | **Live Stream** | `/api/v1/simulator/stream` | `GET` | Returns 20 real-time events for visualization |
| `simulator-landing.html` | **History** | `/api/v1/simulator/summary` | `GET` | Returns 10k aggregated events for ROI comparison |
| `demo.html` | **Verify Audit**| `/api/v1/demo/verify-integrity` | `POST` | Upload truth matrix & session logs |

---

## 7. Subscriptions & Billing
*Logic*: `public_api/routers/subscriptions.py`

| Page (V2) | Page (V1) | Action | Endpoint | Method | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pricing_v2.html` | `pricing.html` | **Get Plans** | `/api/v1/subscriptions/plans` | `GET` | Returns Free, Starter, Pro, Scale config |
| `pricing_v2.html` | `pricing.html` | **Checkout** | `/api/v1/subscriptions/checkout` | `POST` | Returns Stripe Checkout URL (mock/real) |
| `profile_v2.html` | `profile.html` | **Cancel Sub**| `/api/v1/subscriptions/cancel` | `POST` | Cancels at period end |

---

## 8. Installations & Integrations
*Logic*: `public_api/routers/installations.py` & `public_api/routers/integrations.py`

| Page (V2) | Page (V1) | Action | Endpoint | Method | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `integrations_v2.html`| `integrations.html`| **Connect WordPress**| `/api/v1/integrations/connect/wordpress` | `POST` | OAuth Handshake |
| `integrations_v2.html`| `integrations.html`| **Connect Shopify** | `/api/v1/integrations/connect/shopify` | `POST` | OAuth Handshake |
| `onboarding/install.html`| *N/A* | **Get Simple Snippet**| `/api/v1/installations/simple` | `POST` | Generates 1-line JS snippet |

---

## 9. Backend Services Layer (Orchestration)
*Hidden Logic*: `orchestration/services/`

| Service | File | Function |
| :--- | :--- | :--- |
| **Analytics** | `analytics_service.py` | Bayesian Monte Carlo simulation (Adaoptive Sampling). |
| **Metrics** | `metrics_service.py` | Auto-scaling (Postgres <-> Redis) & health monitoring. |
| **Experiment**| `experiment_service.py`| Core CRUD and caching strategies. |
| **Multi-Var** | `multi_element_service.py`| Factorial experiment handling. |

---

## 10. Frontend Structure
*Client Logic*: `static/js/`

- **Core** (`static/js/core/`): Central application logic (`app.js`) and router.
- **Managers** (`static/js/managers/`): Feature-specific handlers.
- **Components** (`static/js/components/`): Reusable UI bits (modals, toasts).
- **TailAdmin** (`static/js/tailadmin/`): Legacy dashboard scripts (to be migrated).

---

## 🚨 Critical Development Tasks (Next Steps)

1.  **Metric Charts Endpoint**: Implement `/api/v1/analytics/experiment/{id}/timeline` to support the V2 "Daily Conversions" chart.
2.  **Visual Editor Wiring**: `visual_editor_v2.html` is currently mocking the proxy. Point it to `/api/v1/visual-editor/proxy`.
3.  **Safe V2 Integration**: Add `/v2/*` routes to `main.py` for side-by-side testing.
4.  **Auth Integration**: Ensure `signin_v2.html` calls `/api/v1/auth/login`.
