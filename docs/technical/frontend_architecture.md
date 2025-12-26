# Sampelit Frontend Architecture & Interaction Guide

> [!IMPORTANT]
> This guide defines the "State of the Art" frontend patterns for Sampelit. It leverages **Alpine.js** for reactivity and **Tailwind CSS** for styling, orchestrated by a custom Vanilla JS core.

## 1. High-Level Architecture

The frontend is a **Multi-Page Application (MPA)** enhanced with JavaScript for a Single-Page-App (SPA) feel.

- **Framework**: `Alpine.js` (Reactivity & DOM manipulation).
- **Styling**: `Tailwind CSS` (Utility-first).
- **Core Logic**: Vanilla ES6 Modules in `static/js/core/`.
- **Composition**: Custom `<include>` system for components.

```mermaid
graph TD
    HTML[Page (e.g., experiment.html)] -->|Includes| Partials[Partials (Sidebar, Header)]
    HTML -->|Initializes| App[MABApp (app.js)]
    App -->|Manages| State[StateManager (state.js)]
    App -->|Requests| API[APIClient (api.js)]
    App -->|Controls| UI[UIManager]
    HTML -->|Binds| Alpine[Alpine.js Data]
```

---

## 2. Core Systems

### A. The `<include>` System (`include.js`)
We use a custom client-side inclusion system to keep HTML DRY without a build step.
```html
<include src="../partials/sidebar.html"></include>
```
*   Recursively fetches and replaces content.
*   **Note**: Scripts in included files may need manual re-initialization if they depend on DOM load events.

### B. The Orchestrator (`app.js`)
The `MABApp` class initializes all subsystems. It is available globally as `window.MABApp`.
- **Usage**: `MABApp.api.get(...)` or `MABApp.state.set(...)`.

### C. State Management (`state.js`)
A robust Pub/Sub state manager that supports history and local storage persistence.
- **Reactive**: Alpine components can subscribe to changes.
- **Persistent**: Critical data (like `user`) is saved to `localStorage`.

---

## 3. "State of the Art" UI Patterns

To ensure a premium feel, we follow these interaction patterns:

### A. Reactivity with Alpine.js
Do not write jQuery-style DOM manipulation. Use Alpine's declarative directives.

**Bad:**
```javascript
document.getElementById('btn').addEventListener('click', () => { ... });
```

**Good (State of the Art):**
```html
<div x-data="{ isLoading: false }">
    <button @click="isLoading = true; await fetchResults(); isLoading = false"
            :class="isLoading ? 'opacity-50 cursor-wait' : ''">
        <span x-show="!isLoading">Run Experiment</span>
        <span x-show="isLoading">Running...</span>
    </button>
</div>
```

### B. Visual Editor Proxy (`visual-editor.html`)
The crown jewel of the platform. It allows users to edit their websites via an iframe.
- **Mechanism**:
    1.  User enters URL.
    2.  Backend `/proxy` fetches HTML and injects `editor-client.js`.
    3.  Frontend displays pure HTML in iframe (sandbox).
    4.  `postMessage` API synchronizes clicks/edits between Parent (Sampelit) and Child (Iframe).

### C. Advanced Visualization (Planned)
For the [Results UI], we will use **Chart.js**.
- **Container**: `<div class="chart-container relative h-[400px]">...</div>`
- **Initialization**: Wrapper component in `js/components/results-chart.js`.
- **Data**: Fed directly from `MABApp.api.get('/experiments/{id}/analytics')`.

---

## 4. Development Workflow

When creating a new page (e.g., `experiment-results.html`):

1.  **Scaffold**: Copy `static/_template_starter.html`.
2.  **Includes**: Add `<include src="../partials/sidebar.html">`.
3.  **State**: Define `x-data="{ ... }"` on the `<body>` or main wrapper.
4.  **Logic**:
    *   Simple logic? Keep in `x-data`.
    *   Complex logic? Add method to `MABApp` or create a module in `js/components/`.
5.  **Style**: Use Tailwind classes. Use `dark:` variants for Dark Mode support.

### Example: Results Tab
```html
<div x-data="{ activeTab: 'overview', results: null }" x-init="results = await MABApp.api.get(...)">
    <!-- Tabs -->
    <div class="flex border-b">
        <button @click="activeTab = 'overview'" :class="...">Overview</button>
        <button @click="activeTab = 'audit'" :class="...">Audit Log</button>
    </div>

    <!-- Content -->
    <div x-show="activeTab === 'overview'">
        <!-- Chart Canvas -->
        <canvas id="conversionChart"></canvas>
    </div>
</div>
```

## 5. Directory Structure
```
static/
├── css/             # Custom vanilla CSS (if Tailwind isn't enough)
├── js/
│   ├── core/        # Singleton Classes (API, State, App)
│   ├── components/  # Page-specific logic (VisualEditor, Charts)
│   └── include.js   # The include system loader
├── partials/        # Reusable HTML snippets
└── [pages].html     # Entry points
```
