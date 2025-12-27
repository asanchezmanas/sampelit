# Frontend Value Map: Exposing the Logic
*Strategic alignment of Backend Intelligence to Frontend UI.*

Instead of copying V1, V2 will expose the sophisticated mathematical engines discovered in the backend audit.

---

## 1. Experiment Details (`experiment_detail_v2.html`)
*Current State: Requests non-existent time-series data.*
*New Strategy: Visualize the Bayesian Engine (`analytics_service.py`).*

| Backend Metric | Visualization Component | Value to User |
| :--- | :--- | :--- |
| **`probability_best`** | **Win Probability Gauge** (Donut Chart) | Instantly know if a variant is winning (e.g., "98% Confidence"). |
| **`expected_loss`** | **Risk Assessment Card** (Red/Green Indicator) | "If you switch to B, your risk is < 0.1% conversion loss." |
| **`credible_interval_95`** | **Error Bar Box Plot** | Shows the range of possible conversion rates (Performance Certainty). |
| **`monte_carlo_samples`** | **"Confidence Computation" Badge** | "Computed with 10k Monte Carlo simulations in 50ms". |

---

## 2. Global Command Center (`index_v2.html`)
*Current State: Generic counters.*
*New Strategy: System Health & Simulator Pulse.*

| Backend Metric | Visualization Component | Value to User |
| :--- | :--- | :--- |
| **`metrics_service.get_health`** | **System Status Pod** | "Auto-Scaling Active: Redis Connected. Health: 100%". |
| **`simulator.stream`** | **Live Traffic Pulse** (Ticker) | Real-time stream of "Decision Events" showing the engine working. |
| **`activity_feed`** | **Intelligence Log** | "Engine pivoted traffic to Variant B (High Confidence)". |

---

## 3. Trust & Verification (`audits_v2.html` - NEW)
*Current State: Hidden in `audit_service.py`.*
*New Strategy: "Glass Box" Transparency Page.*

| Backend Metric | Visualization Component | Value to User |
| :--- | :--- | :--- |
| **`verify_integrity`** | **Cryptographic Chain View** | Visual proof that the algorithm wasn't tampered with. |
| **`truth_matrix_entropy`** | **Matrix Heatmap** | Educational viz showing the "ground truth" distribution. |

---

## 4. Multi-Element Lab (`features_v2.html` - NEW)
*Current State: Hidden in `multi_element_service.py`.*
*New Strategy: Factorial Experiment Canvas.*

| Backend Metric | Visualization Component | Value to User |
| :--- | :--- | :--- |
| **`interaction_effect`** | **Combination Grid** | Shows how "Hero A" + "CTA Red" performs better than sum of parts. |
| **`sample_efficiency`** | **"Time Saved" Counter** | "Factorial design saved you 14 days of testing vs A/B". |

---

## 🚀 Execution Strategy

1.  **Stop** trying to force "Daily Conversions" charts (Time-Series).
2.  **Start** building the **Bayesian Gauge** and **Risk Cards** in `experiment_detail_v2.html`.
3.  **Start** building the **Live Pulse** in `index_v2.html` connecting to `/api/v1/simulate/stream`.
4.  **Create** `audits_v2.html` to expose the cryptographic verification layer.
