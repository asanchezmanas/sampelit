# Backend Architecture & Data Documentation

**Version:** 1.0 (Release)
**Date:** December 25, 2025

---

## 🏗 System Overview

Samplit is a high-performance **Adaptive Experimentation Platform** built on **FastAPI** (Python) and **Supabase** (PostgreSQL). It moves beyond traditional A/B testing by using **Multi-Armed Bandit algorithms** (Thompson Sampling) to automatically route traffic to winning variants in real-time.

### Technology Stack
- **API Framework**: FastAPI (Async Python 3.12+)
- **Database**: PostgreSQL 15+ (via Supabase) with `asyncpg`
- **Authentication**: JWT (Stateless)
- **Optimization Engine**: Bayesian logic (Beta Distributions) for adaptive traffic allocation.

---

## 🧩 Core Data Models

The system is designed around a hierarchical structure that supports both simple A/B tests and complex Multi-Element experiments.

### 1. Experiments (`experiments` table)
The top-level container.
- **Type**: 
  - `ab_test`: Simple split URL or single-element test.
  - `multi_element`: Multivariate/Factorial tests (e.g., changing Button Color AND Headline simultaneously).
- **Status**: `draft`, `running`, `paused`, `completed`.
- **Traffic Allocation**: `adaptive` (Thompson Sampling) or `fixed` (e.g., 50/50).

### 2. Elements (`elements` table)
Examples: "Main CTA Button", "Hero Image", "Headline".
- For `ab_test`, there is typically 1 implied element.
- For `multi_element`, there are multiple explicit elements.

### 3. Variants (`variants` / `element_variants`)
The specific options for each element.
- Example for "Hero Headline":
  - Variant A: "Boost your sales"
  - Variant B: "Get more customers"
- **Properties**: `id`, `name`, `weight` (current traffic allocation probability).

### 4. Combinations (Factorial Logic)
In Multi-Element experiments (as seen in `scripts/data/generate_demo_multielement.py`), the system treats every unique combination of variants as a "Super-Variant".
- **Interaction Effects**: The system learns that "Blue Button" + "Sales Headline" works better than "Red Button" + "Sales Headline".
- **Optimization**: Traffic is allocated to *Combinations*, not just individual elements.

---

## 🔄 Data Flow & Lifecycle

### 1. Configuration (Design Phase)
User creates an experiment via the Dashboard or API.
- **Input**: Definition of Elements and their Variants.
- **Action**: Backend creates records in `experiments`, `elements`, `element_variants`.
- **Reference Script**: `generate_demo_multielement.py` simulates this by defining dictionaries of `elements` and `combination_conversion_rates`.

### 2. Assignment (Runtime)
A user visits the client website.
- **Request**: Client SDK sends `POST /api/v1/tracker/assign` with `browser_id`.
- **Logic**:
  1. **Eligibility**: Check targeting rules.
  2. **Allocation**: 
     - If `fixed`: Random weighted choice.
     - If `adaptive`: Sample from Beta Distribution (Thompson Sampling) for each variation/combination.
  3. **Stickiness**: If user was already assigned, return the *same* variant (consistent UX).
- **Output**: JSON with the specific variants to render.

### 3. Tracking (User Action)
User clicks a button or converts.
- **Request**: Client SDK sends `POST /api/v1/tracker/convert`.
- **Action**: 
  1. Backend records conversion event.
  2. Updates `successful_conversions` count for the assigned variant/combination.
  3. **Feedback Loop**: Next assignment call will have updated probabilities.

### 4. Analysis & Reporting
- **Real-time Stats**: Dashboard queries `experiments` and `variants` tables.
- **Bayesian Stats**:
  - **Alpha/Beta**: Parameters of the probability distribution (Alpha = Successes + Prior, Beta = Failures + Prior).
  - **Win Probability**: Calculated on the fly (or periodically) to determine the leader.
- **Demo Data**: The `generate_demo_data.py` scripts simulate thousands of visitors to generate CSVs that demonstrate how the "Winner" emerges from the noise using these probabilities.

---

## 🧪 Demo Data Scripts Explained

The scripts in `scripts/data/` serve as **logic verification** and **demo generators**.

### `generate_demo_multielement.py`
This script proves the **Factorial** capability of the backend logic.
- **Scenario**: 2 Elements (CTA Button, Hero Copy), 3 Variants each = 9 Combinations.
- **Simulation**: It defines "True Conversion Rates" (hidden from the system) where specific combinations have interaction effects (e.g., CTA-B works best ONLY with Copy-Y).
- **Execution**:
  1. Simulates 10,000 visitors.
  2. Randomly converts them based on the "True CR".
  3. Outputs a Matrix (CSV) and Metadata (JSON).
- **Purpose**: Validates that the backend's analytics engine can ingest this data and correctly identify the "Winner" purely from the binary conversion data.

---

## 📂 API Structure (Key Endpoints)

| Module | Endpoint | Method | Description |
|--------|----------|--------|-------------|
| **Auth** | `/auth/register` | POST | Create account |
| | `/auth/token` | POST | Login (Get JWT) |
| **Exp** | `/experiments` | POST | Create Experiment |
| | `/experiments/{id}` | GET | Get details & stats |
| **Tracker**| `/tracker/assign` | POST | Get assignments for user |
| | `/tracker/convert` | POST | Record conversion |
| **Visual** | `/visual-editor/proxy`| GET | Proxy target site for editor |

---

## 🔒 Security & Data Integrity

- **Row Level Security (RLS)**: Users can only access their own experiments (`user_id` check).
- **Obfuscation**: In Production (`IS_DEVELOPMENT=False`), internal error codes (`EXP_CREATE_001`) are hidden from API responses to prevent information leakage.
- **Input Validation**: Strict **Pydantic V2** models ensure all incoming data (URLs, Configs) is valid before processing.
