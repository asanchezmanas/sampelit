# Metrics Dashboard — Solo Founder

Qué medir, cuándo mirarlo, y cuándo preocuparse.

**Última actualización:** Diciembre 2024

---

## 🎯 Filosofía de Métricas

### Principios

1. **Menos es más.** 10 métricas bien trackadas > 50 ignoradas.
2. **Actionable > Vanity.** Si no puedes actuar sobre ella, no la midas.
3. **Leading > Lagging.** Trials predicen MRR futuro mejor que MRR actual.
4. **Thresholds, no trends.** Define cuándo actuar ANTES de que pase.

### Anti-patrones

- ❌ Revisar métricas cada hora (ansiedad, no insight)
- ❌ Celebrar vanity metrics (visitors sin conversión)
- ❌ Ignorar métricas por semanas
- ❌ Cambiar definiciones constantemente

---

## 📊 Métricas Tier 1: Críticas

Revisar **semanalmente**. Acción inmediata si cruzan threshold.

### 1. MRR (Monthly Recurring Revenue)

```
MRR = Suma de todas las suscripciones activas
```

| Threshold | Significado | Acción |
|-----------|-------------|--------|
| ↑ 10%+ MoM | Crecimiento sano | Mantener estrategia |
| ↔ 0-5% MoM | Estancamiento | Revisar acquisition o churn |
| ↓ 5%+ MoM | Problema serio | Pausar gasto, investigar |
| ↓ 20%+ MoM | Emergencia | Modo crisis (ver contingency) |

**Dónde verlo:** Stripe Dashboard → Billing → MRR

### 2. Churn Rate

```
Churn = Clientes perdidos este mes / Clientes al inicio del mes × 100
```

| Threshold | Significado | Acción |
|-----------|-------------|--------|
| < 5% | Excelente | Mantener |
| 5-8% | Aceptable para early stage | Monitorear |
| 8-12% | Problema | Investigar razones, pausar acquisition |
| > 12% | Crisis | Stop todo, focus 100% en retención |

**Benchmark:** SaaS B2B típico: 3-7% mensual. Startups early stage: hasta 10%.

### 3. Trial → Paid Conversion

```
Conversion = Trials que pagaron / Total trials × 100
```

| Threshold | Significado | Acción |
|-----------|-------------|--------|
| > 30% | Excelente | Escalar acquisition |
| 20-30% | Bueno | Optimizar onboarding |
| 10-20% | Problema | Revisar producto o pricing |
| < 10% | Crisis | Parar ads, fix fundamental |

**Cómo mejorar:**
- Revisar dónde abandonan (email open rates, login frequency)
- Hablar con trials que no convirtieron
- Mejorar onboarding emails

### 4. ARPU (Average Revenue Per User)

```
ARPU = MRR / Clientes activos
```

| Threshold | Significado | Acción |
|-----------|-------------|--------|
| > €300 | Excelente mix hacia Pro/Scale | Mantener |
| €250-300 | Buen equilibrio | Optimizar upgrades |
| €200-250 | Demasiado Starter | Push upgrade path |
| < €200 | Problema de mix | Revisar pricing o targeting |

**Target:** €275+

---

## 📈 Métricas Tier 2: Importantes

Revisar **mensualmente**. Informan estrategia.

### 5. CAC (Customer Acquisition Cost)

```
CAC = Gasto total marketing / Nuevos clientes pagando
```

| Threshold | Significado | Acción |
|-----------|-------------|--------|
| < €150 | Muy eficiente | Escalar ese canal |
| €150-300 | Sostenible | Mantener |
| €300-500 | Caro pero ok si LTV alto | Optimizar |
| > €500 | Insostenible | Parar o pivotar canal |

**Por canal:** Trackear CAC por fuente (organic, ads, referral)

### 6. LTV (Lifetime Value)

```
LTV = ARPU × (1 / Churn rate mensual)
```

**Ejemplo:** €275 ARPU × (1/0.06) = €4,583 LTV

| LTV:CAC Ratio | Significado |
|---------------|-------------|
| > 5:1 | Excelente, escalar agresivo |
| 3-5:1 | Bueno, crecimiento sostenible |
| 1-3:1 | Ajustado, optimizar |
| < 1:1 | Perdiendo dinero, parar |

### 7. Runway

```
Runway (meses) = Cash en banco / Burn rate mensual
```

| Threshold | Significado | Acción |
|-----------|-------------|--------|
| > 18 meses | Cómodo | Invertir en growth |
| 12-18 meses | Ok | Mantener disciplina |
| 6-12 meses | Alerta | Reducir gasto, acelerar revenue |
| < 6 meses | Crisis | Modo supervivencia |

### 8. Net Revenue Retention (NRR)

```
NRR = (MRR inicio + Upgrades - Downgrades - Churn) / MRR inicio × 100
```

| Threshold | Significado |
|-----------|-------------|
| > 100% | Creciendo solo con clientes existentes |
| 90-100% | Sano, pero necesitas nuevos clientes |
| < 90% | Problema de retención serio |

---

## 🔍 Métricas Tier 3: Diagnóstico

Revisar cuando algo Tier 1/2 falla. Para entender el "por qué".

### Acquisition

| Métrica | Qué indica | Dónde verlo |
|---------|------------|-------------|
| Website visitors | Top of funnel | PostHog/Analytics |
| Visitor → Trial | Landing page effectiveness | PostHog |
| Traffic by source | Qué canal funciona | UTM tracking |
| Blog traffic | SEO progress | Analytics |

### Activation

| Métrica | Qué indica | Dónde verlo |
|---------|------------|-------------|
| Trial signup → First experiment | Onboarding friction | DB query |
| Time to first experiment | Product complexity | DB query |
| Email open rates (onboarding) | Email quality | Resend |
| Day 1/3/7 retention | Early engagement | PostHog |

### Revenue

| Métrica | Qué indica | Dónde verlo |
|---------|------------|-------------|
| Upgrade rate | Expansion revenue | Stripe |
| Downgrade rate | Price sensitivity | Stripe |
| Failed payments | Technical/card issues | Stripe |
| Annual vs monthly mix | Revenue predictability | Stripe |

### Retention

| Métrica | Qué indica | Dónde verlo |
|---------|------------|-------------|
| DAU/MAU | Product stickiness | PostHog |
| Feature usage | What matters to users | PostHog |
| Support ticket volume | Product issues | Crisp |
| NPS score | Overall satisfaction | Survey |

---

## 📅 Calendario de Revisión

### Daily (2 min)

Solo si hay campaña de ads activa o lanzamiento reciente:

- [ ] MRR (quick glance en Stripe)
- [ ] Cualquier alerta configurada

### Weekly (15 min) — Viernes

```
[ ] MRR actual: €______
[ ] MRR cambio vs semana pasada: ____%
[ ] Nuevos trials esta semana: ____
[ ] Trials → Paid esta semana: ____
[ ] Churn esta semana: ____
[ ] ARPU actual: €____
[ ] Runway (meses): ____

Notas:
_________________________________
_________________________________
```

### Monthly (1 hora) — Primer lunes del mes

```
[ ] MRR cierre mes anterior: €______
[ ] MRR growth MoM: ____%
[ ] Churn rate: ____%
[ ] CAC promedio: €____
[ ] LTV estimado: €____
[ ] LTV:CAC ratio: ____
[ ] NRR: ____%

[ ] Top 3 churns - razones:
    1. ______________________
    2. ______________________
    3. ______________________

[ ] Top 3 upgrades - qué los motivó:
    1. ______________________
    2. ______________________
    3. ______________________

Acciones para próximo mes:
_________________________________
_________________________________
```

### Quarterly (2 horas)

- Revisar todas las métricas vs objetivos
- Actualizar projections para siguiente quarter
- Ajustar OKRs
- Benchmark vs competencia si hay data pública

---

## 🚨 Sistema de Alertas

### Configurar en Stripe/PostHog:

| Alerta | Trigger | Acción inmediata |
|--------|---------|------------------|
| Churn spike | > 3 churns en 1 semana | Contactar cada uno, investigar |
| Payment failed | Cualquier fallo | Revisar dunning, contactar |
| No trials | 0 trials en 7 días | Revisar acquisition |
| Trial sin actividad | Trial no crea experimento en 5 días | Email manual personal |

### Herramientas para alertas

- **Stripe:** Webhooks → Slack/Email
- **PostHog:** Alertas en dashboards
- **UptimeRobot:** Site down alerts
- **Sentry:** Error rate spikes

---

## 📊 Dashboard Setup

### Stripe (ya viene built-in)

Usar Stripe Dashboard para:
- MRR
- Churn
- ARPU
- Failed payments
- Subscription distribution

### PostHog (gratis)

Crear dashboard con:
1. **Visitors por día** (trend)
2. **Signups por día** (trend)
3. **Conversion funnel:** Visit → Signup → First experiment → Paid
4. **Retention:** Day 1, 7, 30
5. **Feature usage:** Qué features usan los que convierten

### Google Sheets (weekly tracker)

Simple spreadsheet:

| Semana | MRR | Trials | Conversions | Churn | ARPU | Notas |
|--------|-----|--------|-------------|-------|------|-------|
| W1 Jan | €5,200 | 12 | 3 | 1 | €260 | Lanzamos blog |
| W2 Jan | €5,450 | 15 | 4 | 0 | €268 | Ads started |
| ... | | | | | | |

---

## 🎯 Benchmarks por Fase

### Fase 1: 0-20 clientes

| Métrica | Target | "Bien" |
|---------|--------|--------|
| Trial → Paid | > 20% | > 25% |
| Churn | < 10% | < 8% |
| ARPU | > €200 | > €250 |
| CAC | < €300 | < €200 |

### Fase 2: 20-50 clientes

| Métrica | Target | "Bien" |
|---------|--------|--------|
| Trial → Paid | > 25% | > 30% |
| Churn | < 8% | < 6% |
| ARPU | > €250 | > €275 |
| CAC | < €250 | < €175 |
| NRR | > 95% | > 100% |

### Fase 3: 50-100 clientes

| Métrica | Target | "Bien" |
|---------|--------|--------|
| Trial → Paid | > 25% | > 30% |
| Churn | < 6% | < 5% |
| ARPU | > €275 | > €300 |
| CAC | < €200 | < €150 |
| NRR | > 100% | > 105% |

---

## ❌ Métricas a Ignorar

| Métrica vanity | Por qué ignorar |
|----------------|-----------------|
| Total visitors | Sin contexto de conversión = ruido |
| Social followers | No paga facturas |
| Email list size | Open rates y conversiones importan más |
| "Usuarios registrados" | Trials que no pagan = 0 value |
| Competitors' funding | No afecta tu negocio |
| Feature requests count | Prioriza por quién paga, no cuántos piden |

---

## 🔧 Queries Útiles (SQL/DB)

### Trials sin actividad (últimos 7 días)

```sql
SELECT email, created_at 
FROM users 
WHERE subscription_status = 'trial'
  AND created_at > NOW() - INTERVAL '7 days'
  AND id NOT IN (SELECT user_id FROM experiments);
```

### Clientes por tier

```sql
SELECT 
  plan_name,
  COUNT(*) as customers,
  SUM(price) as mrr
FROM subscriptions 
WHERE status = 'active'
GROUP BY plan_name;
```

### Churn del mes

```sql
SELECT 
  COUNT(*) as churned,
  (SELECT COUNT(*) FROM subscriptions 
   WHERE status = 'active' 
   AND created_at < DATE_TRUNC('month', NOW())) as start_of_month
FROM subscriptions
WHERE status = 'cancelled'
  AND cancelled_at >= DATE_TRUNC('month', NOW());
```

---

## 📝 Template: Weekly Review

```markdown
## Week of [DATE]

### Numbers
- MRR: €____
- New trials: ____
- Conversions: ____
- Churn: ____
- ARPU: €____

### Wins
1. 
2. 

### Problems
1. 
2. 

### Actions next week
1. 
2. 

### Notes
```

Guarda en Notion/Doc cada semana. Invaluable para ver patrones después.
