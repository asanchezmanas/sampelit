# UI Specs - Analytics

**Archivo**: `analytics_v2.html`  
**Endpoint**: `GET /analytics/experiment/{id}/insights`

---

## Job del Usuario

> "Quiero ver el impacto real en mi negocio, no solo gráficos bonitos"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Analytics                                      [Últimos 30 días ▼] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐    │
│  │ CONVERSIONES     │ │ IMPACTO TOTAL    │ │ EXPERIMENTOS     │    │
│  │ EXTRA            │ │                  │ │ COMPLETADOS      │    │
│  │ +1,234           │ │ €37,020          │ │ 12               │    │
│  │ este mes         │ │ valor generado   │ │ con ganador      │    │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘    │
│                                                                     │
│  📈 IMPACTO EN EL TIEMPO                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Conversiones extra por semana:                             │   │
│  │                                                             │   │
│  │  400│                                            ╭───       │   │
│  │     │                                     ╭─────╯           │   │
│  │  300│                              ╭─────╯                  │   │
│  │     │                       ╭─────╯                         │   │
│  │  200│                ╭─────╯                                │   │
│  │     │         ╭─────╯                                       │   │
│  │  100│  ╭─────╯                                              │   │
│  │     │──╯                                                    │   │
│  │    0└────────────────────────────────────────────────────   │   │
│  │      Sem 1   Sem 2   Sem 3   Sem 4                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  🏆 MEJORES RESULTADOS                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Checkout Flow     +45% conversión     €12,500 impacto   │   │
│  │  2. CTA Homepage      +30% conversión     €8,200 impacto    │   │
│  │  3. Pricing Page      +18% conversión     €5,400 impacto    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Mapeo API → UI

### Endpoint: `GET /analytics/global?period=30d`

```json
{
  "total_visitors": 45000,
  "total_conversions": 2340,
  "conversion_rate": 0.052,
  "period": "30d"
}
```

### Endpoint: `GET /experiments?status=completed`

```json
{
  "experiments": [
    {
      "id": "...",
      "name": "Checkout Flow",
      "bayesian": {
        "leader": { "name": "Variante B", "uplift_percent": 45 }
      },
      "estimated_revenue_impact": 12500
    }
  ]
}
```

| Dato | Fuente | Cálculo |
|------|--------|---------|
| Conversiones extra | `experiments.sum(uplift × conversions)` | Calculado |
| Impacto total | `experiments.sum(estimated_revenue_impact)` | API |
| Experimentos completados | `experiments.filter(status=completed).length` | API |

---

## Componente Alpine.js

```javascript
function analyticsView() {
  return {
    loading: true,
    period: '30d',
    globalMetrics: null,
    topExperiments: [],
    chartData: [],
    
    async init() {
      await this.loadData();
    },
    
    async loadData() {
      this.loading = true;
      
      const [global, exps] = await Promise.all([
        APIClient.get(`/analytics/global?period=${this.period}`),
        APIClient.get('/experiments?status=completed&limit=10')
      ]);
      
      this.globalMetrics = global.data;
      this.topExperiments = exps.data.experiments
        .sort((a, b) => b.estimated_revenue_impact - a.estimated_revenue_impact)
        .slice(0, 5);
      
      this.loading = false;
    },
    
    get totalImpact() {
      return this.topExperiments.reduce(
        (sum, e) => sum + (e.estimated_revenue_impact || 0), 0
      );
    },
    
    get extraConversions() {
      return this.topExperiments.reduce((sum, e) => {
        const uplift = e.bayesian?.leader?.uplift_percent || 0;
        const conversions = e.total_conversions || 0;
        return sum + Math.round(conversions * uplift / 100);
      }, 0);
    },
    
    formatCurrency(n) {
      return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'EUR'
      }).format(n);
    }
  }
}
```

---

## Selector de Período

```html
<select x-model="period" @change="loadData()">
  <option value="7d">Últimos 7 días</option>
  <option value="30d">Últimos 30 días</option>
  <option value="90d">Últimos 90 días</option>
  <option value="12m">Último año</option>
</select>
```

---

## Gráfico con ApexCharts

```javascript
const chartOptions = {
  chart: { type: 'area', height: 300 },
  series: [{
    name: 'Conversiones extra',
    data: this.chartData
  }],
  xaxis: {
    categories: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
  },
  colors: ['#10b981'],
  fill: {
    type: 'gradient',
    gradient: { opacityFrom: 0.4, opacityTo: 0 }
  }
};
```

---

## Métricas que SÍ Importan

| Métrica | Por qué | Cómo mostrar |
|---------|---------|--------------|
| Revenue adicional | € ganados | "+€12,500 este mes" |
| Conversiones extra | Ventas extra | "+1,234 ventas" |
| % mejora promedio | Cuánto mejor | "+28% promedio" |
| Experimentos con ganador | Decisiones tomadas | "12 completados" |

---

## Métricas a NO Mostrar

| Métrica | Por qué ocultar |
|---------|-----------------|
| p-value | Nadie lo entiende |
| Alpha/Beta parameters | Técnico |
| Confidence intervals (raw) | Confuso |
| Chi-square statistics | Académico |
