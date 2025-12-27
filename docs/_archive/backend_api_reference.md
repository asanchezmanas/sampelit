# Backend API Reference

This document outlines the existing API endpoints available in the `public_api` module. Use this reference to integrate the V2 Frontend with the backend.

**Base URL**: `/api/v1`

---

## 🚨 Gap Analysis (Missing Features)
*The following features are present in the V2 Frontend but lack corresponding Backend Endpoints:*

| Feature | Frontend Component | Missing Backend Need |
| :--- | :--- | :--- |
| **Time-Series Charts** | `experiment_detail_v2.html` | Endpoint returning daily conversions/visitors (e.g., `/experiments/{id}/stats/timeline`) |
| **Advanced Filtering** | `analytics_v2.html` | Endpoints for filtering by browser, device, or country. |
| **Email/Push Experiments** | `experiments_v2.html` | Backend currently throws `NotImplementedError` for these types. |

---

## 1. Dashboard (`/dashboard`)
*High-level system overview.*

### Get Dashboard Data
`GET /dashboard/`
Returns aggregated stats for the user (total visitors, conversions, active experiments).
- **Response**: `DashboardData`
    - `stats`: `{ total_experiments, active_experiments, total_visitors, total_conversions, avg_conversion_rate }`
    - `recent_experiments`: List of top 5 recent experiments.
    - `quick_actions`: List of recommended next steps.

### Get Activity Feed
`GET /dashboard/activity`
- **Params**: `limit` (int, default=10)
- **Response**: List of recent system activities (experiment created, started, etc.).

---

## 2. Experiments (`/experiments`)
*Core A/B testing logic.*

### List Experiments
`GET /experiments/`
- **Params**: `status_filter` (draft, active, paused, archived), `page`, `per_page`
- **Response**: Paginated list of experiments.

### Create Experiment
`POST /experiments/`
- **Body**: `{ name, description, url, elements: [...] }`
- **Response**: `{ id, elements: [...] }`

### Get Experiment Details
`GET /experiments/{experiment_id}`
- **Response**: Full details including hierarchical performance analysis.
    - **Note**: Returns `total_visitors` and `conversion_rate`, but **NO** historical time-series data.

### Update Status
`PATCH /experiments/{experiment_id}/status`
- **Params**: `new_status` (active, paused, completed)

---

## 3. Funnels (`/funnels`)
*Multi-step conversion paths with visual node editor.*

### List Funnels
`GET /funnels/`
- **Response**: Paginated list of funnels with conversion rates.

### Get Funnel (Canvas Data)
`GET /funnels/{funnel_id}`
- **Response**: detailed object containing `nodes` and `edges` for the visual canvas.

### Node Management
- `POST /funnels/{id}/nodes`: Create a new step/node.
- `DELETE /funnels/{id}/nodes/{node_id}`: Remove a step.

### Edge Management
- `POST /funnels/{id}/edges`: Connect two nodes.
- `DELETE /funnels/{id}/edges/{edge_id}`: Disconnect nodes.

---

## 4. Visual Editor (`/visual-editor`)
*Proxy and saving for the drag-and-drop editor.*

### Proxy Page
`GET /visual-editor/proxy`
- **Params**: `url` (Target website URL)
- **Response**: HTML content of the target URL with the Editor Client script injected.
- **Frontend Usage**: Used by the iframe in `visual_editor_v2.html`.

### Save Elements
`POST /visual-editor/save-elements`
- **Body**: `{ experiment_name, page_url, elements: [...] }`
- **Response**: Creates a new experiment draft from the visual selection.

---

## 5. Public Dashboard (`/public-dashboard`)
*Shareable, read-only stats.*

### View Public Page
`GET /public-dashboard/{experiment_id}`
- **Response**: HTML page (certificate style) showing experiment results.

### Get Public Metrics
`GET /public-dashboard/api/{experiment_id}`
- **Response**: JSON data of the public metrics (sanitized).

---

## 6. Tracker (`/tracker`)
*Public-facing endpoints used by the JavaScript SDK (`tracker.js`).*

- `POST /tracker/assign`: Bucketing logic. Returns which variant a user should see.
- `POST /tracker/convert`: Records a conversion event.
- `POST /tracker/experiments/active`: Returns list of experiments running on a specific `installation_token`.
