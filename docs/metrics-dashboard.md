# Metrics Dashboard

Qué medir, cuándo, y qué hacer cuando algo está mal.

**Actualizado:** Diciembre 2024

---

## 🎯 Métricas Tier 1 (Revisar Semanalmente)

Estas son las métricas que determinan si el negocio está sano.

### Revenue

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **MRR** | Suma de revenue mensual recurrente | Creciendo | Cae 2 semanas seguidas |
| **MRR Growth %** | (MRR actual - MRR mes anterior) / MRR mes anterior | > 10%/mes | < 5%/mes |
| **ARPU** | MRR / Clientes activos | > €275 | < €200 |

### Clientes

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **Clientes activos** | Clientes con suscripción activa | Creciendo | Decrece |
| **New MRR** | MRR de nuevos clientes este mes | > Churned MRR | < Churned MRR |
| **Churned MRR** | MRR perdido por churn | < 5% del MRR | > 8% del MRR |

### Conversión

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **Trial starts** | Nuevos trials / semana | > 10/semana | < 5/semana |
| **Trial → Paid** | Trials convertidos / Trials expirados | > 20% | < 12% |

---

## 📊 Métricas Tier 2 (Revisar Mensualmente)

### Unit Economics

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **CAC** | Gasto marketing / Nuevos clientes | < €250 | > €400 |
| **LTV** | ARPU × Meses promedio de vida | > €2,500 | < €1,500 |
| **LTV:CAC** | LTV / CAC | > 10:1 | < 5:1 |
| **Payback** | CAC / ARPU | < 2 meses | > 4 meses |

### Retención

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **Gross Churn** | Clientes perdidos / Clientes inicio mes | < 5% | > 8% |
| **Net Revenue Retention** | (MRR inicio + Expansion - Churn) / MRR inicio | > 100% | < 90% |
| **Logo Retention** | Clientes retenidos / Clientes inicio mes | > 95% | < 92% |

### Engagement

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **DAU/MAU** | Daily active / Monthly active | > 30% | < 15% |
| **Experiments created** | Experimentos nuevos / mes / cliente | > 1 | < 0.3 |
| **Time to first experiment** | Tiempo desde signup hasta primer experimento | < 2 días | > 7 días |

---

## 🔴 Métricas Tier 3 (Revisar Trimestralmente)

### Financieras

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **Runway** | Cash / Burn mensual | > 18 meses | < 12 meses |
| **Gross Margin** | (Revenue - COGS) / Revenue | > 80% | < 70% |
| **Net Margin** | (Revenue - Todos los gastos) / Revenue | > 50% | < 30% |

### Growth Efficiency

| Métrica | Cálculo | Target | Alarma |
|---------|---------|--------|--------|
| **Burn Multiple** | Net Burn / Net New ARR | < 1 | > 2 |
| **Magic Number** | New ARR / Sales & Marketing spend (Q anterior) | > 0.75 | < 0.5 |
| **Rule of 40** | Growth rate % + Profit margin % | > 40 | < 25 |

---

## 📈 Dashboard por Canal

### SEO / Organic

| Métrica | Target | Frecuencia |
|---------|--------|------------|
| Organic sessions | Creciendo 10%/mes | Semanal |
| Keyword rankings (top 10) | +5/mes | Mensual |
| Organic trials | > 30% de total trials | Semanal |
| Blog → Trial conversion | > 2% | Mensual |

### Paid (cuando activo)

| Métrica | Instagram | LinkedIn |
|---------|-----------|----------|
| CTR | > 1% | > 0.5% |
| CPC | < €2 | < €5 |
| CPL (lead) | < €30 | < €50 |
| CPA (trial) | < €100 | < €150 |
| CPA (paid) | < €200 | < €300 |
| ROAS | > 3x | > 2.5x |

### Email

| Métrica | Target | Alarma |
|---------|--------|--------|
| Open rate | > 40% | < 25% |
| Click rate | > 5% | < 2% |
| Unsubscribe rate | < 0.5% | > 1% |
| Reply rate (nurture) | > 2% | < 0.5% |

### Referrals

| Métrica | Target | Alarma |
|---------|--------|--------|
| % clientes que refieren | > 10% | < 5% |
| Referrals por referidor | > 1.5 | < 1 |
| Referral → Paid conversion | > 40% | < 25% |
| % revenue de referrals | > 15% | < 5% |

---

## 🚨 Sistema de Alertas

### Alertas Críticas (Actuar HOY)

| Alerta | Trigger | Acción |
|--------|---------|--------|
| 🔴 **MRR Drop** | MRR cae > 10% semana | Investigar churn, contactar clientes |
| 🔴 **Churn Spike** | > 3 cancellations / día | Llamar (sí, llamar) a churned users |
| 🔴 **Trial Crash** | Trials caen > 50% semana | Check site, ads, tracking |
| 🔴 **Payment Failed** | > 20% failed payments | Revisar Stripe, contactar clientes |

### Alertas Importantes (Actuar esta semana)

| Alerta | Trigger | Acción |
|--------|---------|--------|
| 🟡 **Conversion Drop** | Trial→Paid < 15% (2 semanas) | Revisar onboarding, talk to trials |
| 🟡 **CAC Rising** | CAC > €300 | Revisar spend, pausar underperformers |
| 🟡 **Engagement Drop** | DAU/MAU < 20% | Revisar producto, enviar re-engagement |
| 🟡 **Support Spike** | Tickets > 2x normal | Identificar issue común |

### Alertas de Monitoreo (Revisar en weekly)

| Alerta | Trigger | Acción |
|--------|---------|--------|
| 🟢 **Growth Slowing** | MRR growth < 8% | Evaluar nuevos canales |
| 🟢 **ARPU Dropping** | ARPU < €250 | Revisar upgrade paths |
| 🟢 **Organic Stall** | Organic flat 4 semanas | Aumentar content velocity |

---

## 📋 Reporting Templates

### Weekly Snapshot (Lunes, 15 min)

```markdown
## Week of [DATE]

### Headlines
- MRR: €X,XXX (↑/↓ X% vs last week)
- New trials: XX
- New customers: X
- Churned: X

### Health Check
- [✅/⚠️/❌] Trial→Paid: XX%
- [✅/⚠️/❌] Churn: X%
- [✅/⚠️/❌] Support tickets: XX

### Wins
- 

### Issues
- 

### Focus this week
1. 
2. 
3. 
```

### Monthly Report (1er día del mes, 1h)

```markdown
## [MONTH] Report

### Revenue
| Metric | This Month | Last Month | Change |
|--------|------------|------------|--------|
| MRR | | | |
| New MRR | | | |
| Churned MRR | | | |
| Net New MRR | | | |
| ARPU | | | |

### Customers
| Metric | This Month | Last Month | Change |
|--------|------------|------------|--------|
| Active customers | | | |
| New customers | | | |
| Churned customers | | | |
| Trials started | | | |
| Trial→Paid % | | | |

### Unit Economics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| CAC | | <€250 | |
| LTV | | >€2,500 | |
| LTV:CAC | | >10:1 | |
| Payback | | <2 mo | |

### Channels
| Channel | Trials | Customers | CAC |
|---------|--------|-----------|-----|
| Organic | | | |
| Paid | | | |
| Referral | | | |
| Direct | | | |

### Learnings
1. 
2. 
3. 

### Next Month Focus
1. 
2. 
3. 
```

---

## 🛠️ Herramientas de Tracking

### Stack Recomendado (Bootstrap)

| Función | Herramienta | Coste |
|---------|-------------|-------|
| Product analytics | Plausible | €9/mes |
| Revenue metrics | Stripe Dashboard | €0 |
| Spreadsheet | Google Sheets | €0 |
| Visualization | Notion | €10/mes |

### Stack Avanzado (€15k+ MRR)

| Función | Herramienta | Coste |
|---------|-------------|-------|
| Product analytics | PostHog o Amplitude | €0-100/mes |
| Revenue metrics | ChartMogul o Baremetrics | €50-150/mes |
| BI | Metabase | €85/mes |
| Data warehouse | Supabase (ya tienes) | €0 |

---

## 📊 Benchmarks por Fase

### Early Stage (€0-10k MRR)

| Métrica | Poor | OK | Good | Great |
|---------|------|----|----- |-------|
| MRR Growth | <10% | 15% | 20% | >30% |
| Churn | >10% | 7% | 5% | <3% |
| Trial→Paid | <15% | 20% | 25% | >35% |
| CAC | >€400 | €300 | €200 | <€150 |

### Growth Stage (€10k-50k MRR)

| Métrica | Poor | OK | Good | Great |
|---------|------|----|----- |-------|
| MRR Growth | <8% | 12% | 15% | >20% |
| Churn | >8% | 6% | 4% | <3% |
| NRR | <90% | 95% | 100% | >110% |
| LTV:CAC | <4 | 6 | 10 | >15 |

### Scale Stage (€50k+ MRR)

| Métrica | Poor | OK | Good | Great |
|---------|------|----|----- |-------|
| MRR Growth | <5% | 8% | 12% | >15% |
| Churn | >6% | 4% | 3% | <2% |
| Rule of 40 | <25 | 35 | 45 | >60 |
| Magic Number | <0.5 | 0.75 | 1 | >1.5 |

---

## 🔄 Proceso de Review

### Weekly (Lunes, 15 min)

1. Open Stripe → Check MRR, new, churn
2. Open Database → Check trials this week
3. Open Crisp → Check ticket volume
4. Fill weekly snapshot
5. Identify any 🔴 alerts → Act today

### Monthly (1st of month, 1h)

1. Export all data to spreadsheet
2. Calculate unit economics
3. Compare vs targets
4. Fill monthly report
5. Adjust next month's focus

### Quarterly (2h)

1. Deep dive on trends
2. Calculate burn multiple, magic number
3. Cohort analysis (retention by signup month)
4. Channel attribution analysis
5. Update annual projections

---

## 📈 North Star Metrics por Fase

| Fase | North Star | Por qué |
|------|------------|---------|
| Pre-PMF | Trial → Paid % | Valida que el producto resuelve problema |
| Early (€0-10k) | MRR | Prueba que puedes vender |
| Growth (€10k-50k) | Net Revenue Retention | Prueba que puedes retener y expandir |
| Scale (€50k+) | Rule of 40 | Prueba que puedes crecer eficientemente |

---

## 🎯 Quick Reference

### "¿Estoy OK?"

```
IF MRR growing AND churn < 8% AND runway > 12mo
  → You're fine, keep going
  
IF MRR flat AND churn < 8%
  → Focus on acquisition
  
IF MRR growing AND churn > 8%
  → STOP acquisition, fix retention
  
IF MRR declining
  → EMERGENCY: talk to every churned user this week
```

### "¿Dónde poner foco?"

```
IF Trial→Paid < 15%
  → Fix onboarding/activation
  
IF CAC > €400
  → Fix channels/messaging
  
IF Churn > 8%
  → Fix product/support
  
IF All good but growth slow
  → Add new channel or increase spend
```
