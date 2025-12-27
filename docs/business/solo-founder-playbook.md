# Solo Founder Playbook

Guía táctica para operar Sampelit como fundador solo, sin llamadas, maximizando automatización.

**Última actualización:** Diciembre 2024
**Precios vigentes:** €149 / €399 / €999 / €2,499

---

## 🎯 Principios Fundamentales

1. **Nunca hagas llamadas de ventas.** El tiempo de llamada no escala.
2. **El producto vende.** Si necesitas explicar, el producto falla.
3. **Async > Sync.** Email y chat tienen registro y escalan.
4. **Automatiza o elimina.** Si no puedes automatizar, no lo hagas.
5. **Menos clientes, más valiosos.** Precio premium = menos soporte = más margen.

---

## 📊 Modelo de Negocio

### Revenue Target (Year 1)

| Métrica | Target Conservador | Target Optimista |
|---------|-------------------|------------------|
| MRR Target | €10,000 | €20,000 |
| ARPU esperado | €275/mes | €300/mes |
| Clientes necesarios | ~37 | ~67 |
| Churn máximo | 6%/mes | 5%/mes |

### Mix de Tiers Esperado

| Tier | % clientes | Clientes (37 total) | MRR |
|------|------------|---------------------|-----|
| Starter €149 | 50% | 19 | €2,831 |
| Professional €399 | 40% | 15 | €5,985 |
| Scale €999 | 10% | 3 | €2,997 |
| **Total** | 100% | 37 | **€11,813** |

### Unit Economics

| Métrica | Target | Cálculo |
|---------|--------|---------|
| ARPU | €275+ | MRR / Clientes activos |
| CAC | < €300 | Gasto marketing / Nuevos clientes |
| LTV | > €2,500 | ARPU × (1/Churn rate) |
| LTV:CAC | > 8:1 | LTV / CAC |
| Payback | < 2 meses | CAC / ARPU |

---

## 🚀 Fases de Crecimiento

### Fase 1: Validación (0-20 clientes)
**Objetivo:** Confirmar product-market fit

| Actividad | Acción | Tiempo/semana |
|-----------|--------|---------------|
| Outreach | LinkedIn DMs a SaaS founders de tu red | 2h |
| Content | 1 blog post SEO | 3h |
| Product | Iterar basado en feedback | 5h |
| Support | Responder personalmente | 2h |
| **Total** | | **12h** |

**Métricas clave:**
- Trial → Paid > 20%
- NPS > 40
- Al menos 3 testimonials escritos
- 0 churns por problemas de producto

### Fase 2: Tracción (20-50 clientes)
**Objetivo:** Escalar canales que funcionan

| Actividad | Inversión/mes |
|-----------|---------------|
| SEO | 4 posts/mes (tu tiempo o €500 writer) |
| Ads | €500-750 (Meta + Google) |
| Referrals | ~€75-150/referral (1 mes gratis) |

**Automatizaciones críticas:**
- [x] Onboarding email sequence (6 emails)
- [x] Lifecycle emails (10 emails + dunning)
- [x] Billing automático (Stripe)
- [ ] FAQ chatbot / knowledge base
- [ ] In-app help tooltips

### Fase 3: Escala (50-100 clientes)
**Objetivo:** Eficiencia operativa

| Actividad | Inversión/mes |
|-----------|---------------|
| Content | Freelance writer €750/mes |
| Ads | €1,500/mes |
| Partnerships | Tu tiempo |
| Support | Considerar VA part-time €500/mes |

---

## 💰 Plan de Distribución de Revenue

### Regla del 40/30/20/10

| Categoría | % | Con €10k MRR | Con €20k MRR |
|-----------|---|--------------|--------------|
| Reserva/Treasury | 40% | €4,000 | €8,000 |
| Growth (ads, content) | 30% | €3,000 | €6,000 |
| Sueldo personal | 20% | €2,000 | €4,000 |
| Inversiones | 10% | €1,000 | €2,000 |

### Prioridades de Gasto por Fase

**Fase 1 (€0-5k MRR):**
| Item | Coste/mes |
|------|-----------|
| Hosting (Render + Supabase) | €100 |
| Dominio + Email (Google Workspace) | €20 |
| Herramientas gratis (Canva, Buffer) | €0 |
| **Total** | **€120** |

**Fase 2 (€5k-10k MRR):**
| Item | Coste/mes |
|------|-----------|
| Infraestructura | €150 |
| Ads | €500-750 |
| Email service (Resend) | €50 |
| Analytics (PostHog free tier) | €0 |
| **Total** | **€700-900** |

**Fase 3 (€10k-20k MRR):**
| Item | Coste/mes |
|------|-----------|
| Infraestructura | €200 |
| Ads | €1,500 |
| Content writer | €750 |
| Support tool (Crisp) | €50 |
| VA part-time | €500 |
| **Total** | **€3,000** |

---

## 📞 Política Anti-Llamadas

### En lugar de llamadas:

| Situación | Solución |
|-----------|----------|
| "¿Podemos hacer una llamada?" | "Prefiero email/chat para darte respuesta más rápida. ¿Qué necesitas?" |
| Demo request | Link a demo interactiva + video Loom de 3 min |
| Soporte complejo | Video Loom explicando + email |
| Enterprise inquiry | Formulario con preguntas específicas |
| "Solo 15 minutos" | "Mi calendario no permite llamadas, pero respondo emails en <24h" |

### Template de respuesta:

```
Subject: Re: Quick call request

Hi [Name],

Thanks for reaching out! I work async to keep prices low 
and response times fast.

Here's what might help:
- Demo video: [link]
- Documentation: [link]
- Common questions: [link]

If you have specific questions, just reply here and 
I'll get back within 24 hours.

Best,
[Tu nombre]
```

### Excepciones (cuando SÍ hacer llamada):

- Enterprise deal > €2,000/mes (raro, caso por caso)
- Partnership estratégico con alcance significativo
- Investor meeting (si buscas funding)

---

## ⚙️ Stack de Automatización

### Tier 1: Gratuito (€0/mes)
- **Analytics**: PostHog (free tier) o Plausible self-hosted
- **Email personal**: Gmail
- **Scheduling**: Calendly free (para lo mínimo necesario)
- **Forms**: Tally.so
- **Design**: Canva free

### Tier 2: Básico (€100-150/mes)
- **Email marketing**: Resend (€20)
- **Support widget**: Crisp (€25)
- **Billing**: Stripe (2.9% + €0.30)
- **Monitoring**: UptimeRobot (free) + Sentry (free tier)
- **Docs**: Notion (€10)

### Tier 3: Escala (€300-500/mes)
- **Ads**: Meta + Google (variable)
- **Content**: Freelancer (€500-750)
- **Automation**: n8n self-hosted o Make (€30)
- **Advanced analytics**: Amplitude (si necesario)

---

## 📈 Métricas Semanales (15 min)

| Métrica | Fuente | Action Threshold |
|---------|--------|------------------|
| MRR | Stripe | Si baja 10%, investigar inmediatamente |
| Trials esta semana | DB / PostHog | Si < 5/semana, revisar acquisition |
| Trial → Paid rate | Stripe | Si < 20%, revisar onboarding |
| Churn este mes | Stripe | Si > 6%, pausar acquisition, fix retention |
| Support tickets | Crisp | Si > 15/semana, mejorar docs/producto |
| ARPU | Stripe | Si < €250, revisar upgrade flow |

Ver **metrics-dashboard.md** para setup completo.

---

## 🎯 OKRs Trimestrales

### Q1 Ejemplo (Year 1)

**Objetivo:** Llegar a 25 clientes pagando con unit economics sanos

| Key Result | Target | Cómo medir |
|------------|--------|------------|
| Clientes activos | 25 | Stripe subscriptions |
| MRR | €6,000 | Stripe MRR |
| ARPU | €240+ | MRR / Clientes |
| Trial → Paid | 25%+ | Trials vs conversions |
| Churn | < 8% | Cancelaciones / Total |
| Blog posts | 10 | Published count |

---

## 🚫 Lo que NO hacer

| Anti-patrón | Por qué evitar |
|-------------|----------------|
| Llamadas de ventas | No escala, pierdes horas |
| Custom features para un cliente | Distrae del producto core |
| Descuentos agresivos | Atrae clientes que churnearan |
| Responder inmediatamente 24/7 | Burnout, crea expectativas imposibles |
| Contratar antes de €15k MRR | El dinero se va muy rápido |
| Competir en precio | Race to bottom, imposible ganar |
| Múltiples productos a la vez | Focus es tu ventaja |

---

## ✅ Rutinas

### Daily (30 min máx)

- [ ] Check Stripe dashboard (2 min)
- [ ] Responder emails críticos (10 min)
- [ ] Responder support tickets (10 min)
- [ ] 1 acción de growth: post, DM, o iteración (10 min)

### Weekly (2h total)

- [ ] Revisar métricas (15 min) - Ver metrics-dashboard.md
- [ ] Publicar 1 pieza de contenido (45 min)
- [ ] Revisar feedback de usuarios (15 min)
- [ ] 1 mejora en producto o docs (30 min)
- [ ] Planificar semana siguiente (15 min)

### Monthly (3h)

- [ ] Revisar P&L completo
- [ ] Analizar churn (quién y por qué)
- [ ] Actualizar roadmap
- [ ] Revisar competencia
- [ ] Ajustar distribución de revenue si necesario

---

## 🆘 Contingencias

### Si el churn sube a >10%

1. PARAR todo gasto en acquisition
2. Contactar personalmente a cada churned user
3. Identificar patrón (producto, precio, competencia)
4. Fix antes de volver a adquirir

### Si MRR baja 20%+ en un mes

1. Activar modo austeridad (solo gastos esenciales)
2. Extender runway a 18+ meses
3. Priorizar retención sobre acquisition
4. Considerar pivot si persiste 3 meses

### Si un competidor grande entra

1. No entrar en pánico
2. Duplicar diferenciación (self-serve, precio, simplicidad)
3. Acelerar nicho específico
4. Considerar "built for X" positioning

Ver **contingency-playbook.md** para planes detallados.

---

## 📞 Contactos de Emergencia

| Situación | Recurso |
|-----------|---------|
| Hosting down | Render support |
| Database issue | Supabase support |
| Payment processing | Stripe support |
| Legal question | [Tu abogado/gestor] |
| Burnout | [Tu persona de confianza] |

---

## 🎓 Mentalidad

### Recordatorios para días difíciles

1. **37 clientes = €10k MRR.** No necesitas miles.
2. **Cada "no" te acerca a un "sí".** El rechazo es parte del proceso.
3. **El churn es feedback.** Úsalo para mejorar.
4. **Slow is smooth, smooth is fast.** Consistencia > velocidad.
5. **Tu tiempo es tu único recurso no renovable.** Protégelo.

### Señales de que vas bien

- Clientes refieren sin que les pidas
- El soporte es mayormente "how to" no "it's broken"
- Trial → Paid rate estable o subiendo
- Puedes tomar vacaciones sin que todo se rompa
