# Marketing Roadmap — Sampelit

**Última actualización:** Diciembre 2025  
**Precio actual:** €149 / €399 / €999 / €2,499

---

## Resumen Ejecutivo

| Fase | Duración | Objetivo |
|------|----------|----------|
| **Fase 0** | 1-2 días | Corregir inconsistencias actuales |
| **Fase 1** | 1-2 semanas | Preparar assets para launch |
| **Fase 2** | 2-4 semanas | Launch y primeros usuarios |
| **Fase 3** | Ongoing | Growth y optimización |

---

## Fase 0: Housekeeping (Urgente)

> Corregir errores e inconsistencias antes de cualquier otra cosa.

### 0.1 Actualizar Precios en Todos los Documentos

| Archivo | Cambio | Tiempo | Estado |
|---------|--------|--------|--------|
| `content/marketing/landing.md` | €49 → €149 en todas las menciones | 5 min | ☐ |
| `content/marketing/public_pages.md` | FAQ: €49 → €149, actualizar tiers | 10 min | ☐ |
| `content/marketing/email_seq.md` | Email 3: €49 → €149, early adopter 50% = €74.50 | 5 min | ☐ |
| `content/marketing/review_exchange.md` | Ajustar compensación (ver 0.2) | 10 min | ☐ |
| `docs/business/financial-plan.md` | Recalcular con €149 base | 20 min | ☐ |
| `docs/business/pricing-strategy.md` | Verificar consistencia | 5 min | ☐ |

**Responsable:** Tú  
**Dependencias:** Ninguna  
**Total estimado:** 1 hora

---

### 0.2 Ajustar Compensación de Reviews

**Problema actual:** 12 meses gratis = €1,788 de valor por un review. Excesivo.

**Nueva propuesta:**

| Opción | Valor | Para quién |
|--------|-------|------------|
| **A** | 2 meses gratis (€298) | Usuarios con review detallado |
| **B** | 50% descuento año 2 (€894 ahorro) | Power users comprometidos |
| **C** | Feature en case study + 1 mes gratis | Usuarios con datos interesantes |

**Actualizar en:** `content/marketing/review_exchange.md`

**Responsable:** Tú  
**Tiempo:** 15 min

---

### 0.3 Definir Política de Emojis

**Problema:** Brand voice dice "no emojis" pero varios docs los usan.

**Decisión propuesta:**

| Contexto | Emojis | Ejemplo |
|----------|--------|---------|
| Landing page | ❌ No | Copy limpio, profesional |
| Blog posts | ❌ No | Texto corrido sin decoración |
| Internal docs | ✅ Sí | READMEs, roadmaps (este doc) |
| Social media | ⚠️ Mínimo | 1-2 max por post, nunca en headlines |
| Emails | ❌ No | Consistente con brand voice |

**Actualizar en:** `content/brand-voice.md` (añadir sección "Emoji Policy")

**Responsable:** Tú  
**Tiempo:** 10 min

---

## Fase 1: Pre-Launch Assets (Semana 1-2)

> Crear todo el contenido necesario antes de abrir al público.

### 1.1 Pricing Page (NO EXISTE — Crítico)

**Archivo a crear:** `content/marketing/pricing_page.md`

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 1.1.1 | Definir features incluidos por tier | 30 min | ☐ |
| 1.1.2 | Escribir headline + subheadline | 15 min | ☐ |
| 1.1.3 | Escribir descripción de cada tier | 45 min | ☐ |
| 1.1.4 | Crear comparison table (features vs tiers) | 30 min | ☐ |
| 1.1.5 | Escribir FAQ específico de pricing (5-7 preguntas) | 30 min | ☐ |
| 1.1.6 | Copy para toggle mensual/anual | 10 min | ☐ |
| 1.1.7 | Copy para "Enterprise: Contact us" | 10 min | ☐ |
| 1.1.8 | Implementar en HTML (`static/pricing.html`) | 2-3 h | ☐ |

**Estructura propuesta:**

```
PRICING PAGE STRUCTURE
─────────────────────────────────────────────
HEADLINE: "Simple pricing. No surprises."
SUBHEADLINE: "Start testing in minutes. Scale when you're ready."

[Toggle: Monthly / Annual (20% off)]

┌─────────────┬─────────────┬─────────────┬─────────────┐
│   STARTER   │    PRO      │    SCALE    │ ENTERPRISE  │
│   €149/mo   │   €399/mo   │   €999/mo   │  €2,499/mo  │
│             │  POPULAR    │             │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ 5 exp       │ 25 exp      │ Unlimited   │ Unlimited   │
│ 25k visitors│ 100k visit  │ 500k visit  │ Unlimited   │
│ 1 site      │ 3 sites     │ 10 sites    │ Unlimited   │
│ Email support│ Priority   │ Dedicated   │ SLA + Phone │
│             │ Visual Edit │ API Access  │ Custom Int. │
│             │             │ White-label │ On-premise  │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ [Start]     │ [Start]     │ [Start]     │ [Contact]   │
└─────────────┴─────────────┴─────────────┴─────────────┘

FAQ SECTION (below)

"Still have questions?" → Link to /contact
```

**Responsable:** Tú (copy) + Tú/Freelancer (HTML)  
**Dependencias:** 0.1 completado  
**Total estimado:** 4-5 horas

---

### 1.2 Onboarding Email Sequence (NO EXISTE — Crítico)

**Archivo a crear:** `content/marketing/onboarding_emails.md`

> Estos emails se envían DESPUÉS de que alguien paga, no durante waitlist.

#### Emails a escribir:

| # | Email | Trigger | Objetivo |
|---|-------|---------|----------|
| 1.2.1 | Welcome + Quick Start | Inmediato post-pago | Activación rápida |
| 1.2.2 | "¿Instalaste el tracker?" | Día 3 si no hay datos | Reducir abandono |
| 1.2.3 | "Crea tu primer experimento" | Día 5 si no hay exp | Feature education |
| 1.2.4 | "Tus primeros resultados" | Día 14 o primer resultado | Celebrar + next steps |
| 1.2.5 | "Tips para mejores tests" | Día 21 | Engagement + value |
| 1.2.6 | "¿Cómo va todo?" | Día 28 (pre-renewal) | NPS + feedback |

#### Subtareas detalladas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 1.2.1a | Escribir Welcome email (copy) | 20 min | ☐ |
| 1.2.1b | Definir links/CTAs del Welcome | 10 min | ☐ |
| 1.2.2a | Escribir "Tracker check" email | 15 min | ☐ |
| 1.2.2b | Definir condición de trigger (sin datos 72h) | 5 min | ☐ |
| 1.2.3a | Escribir "First experiment" email | 20 min | ☐ |
| 1.2.3b | Incluir mini-tutorial o video link | 10 min | ☐ |
| 1.2.4a | Escribir "First results" email | 20 min | ☐ |
| 1.2.4b | Definir data points a incluir (personalizados) | 15 min | ☐ |
| 1.2.5a | Escribir "Tips" email | 25 min | ☐ |
| 1.2.6a | Escribir "Check-in" email con NPS ask | 20 min | ☐ |
| 1.2.7 | Crear diagrama de flujo de la secuencia | 30 min | ☐ |

**Email 1 - Welcome (Ejemplo de estructura):**

```
Subject: You're in. Here's how to start.

Hi,

Your Sampelit account is ready.

Here's what to do next (takes ~10 minutes):

1. Install the tracker
   Copy one line of code into your site's <head>.
   → [Installation guide]

2. Create your first experiment
   Start with your homepage headline—it's the highest-leverage test.
   → [Create experiment]

3. Wait for data
   You'll see results within 7-14 days depending on your traffic.

Questions? Reply to this email. I read everything.

—
[Name]
Sampelit

P.S. — Stuck on installation? Here's a 2-minute video: [link]
```

**Responsable:** Tú  
**Dependencias:** Email provider configurado (1.4)  
**Total estimado:** 3-4 horas

---

### 1.3 Lifecycle Emails (NO EXISTEN — Importante)

**Archivo a crear:** `content/marketing/lifecycle_emails.md`

#### Emails a escribir:

| # | Email | Trigger | Objetivo |
|---|-------|---------|----------|
| 1.3.1 | Experiment completed | Exp reaches 95% confidence | Next action |
| 1.3.2 | Inactive warning | 14 días sin login | Re-engagement |
| 1.3.3 | Churn prevention | Cancellation initiated | Save the customer |
| 1.3.4 | Win-back | 30 días post-cancel | Re-acquisition |
| 1.3.5 | Upgrade nudge | Hitting plan limits | Upsell |

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 1.3.1 | Escribir "Experiment completed" email | 20 min | ☐ |
| 1.3.2 | Escribir "We miss you" email (sin ser cringe) | 20 min | ☐ |
| 1.3.3 | Escribir "Before you go" email | 25 min | ☐ |
| 1.3.4 | Escribir "Come back" email con oferta | 20 min | ☐ |
| 1.3.5 | Escribir "You're growing" upgrade email | 15 min | ☐ |
| 1.3.6 | Definir triggers técnicos para cada email | 30 min | ☐ |

**Responsable:** Tú  
**Dependencias:** 1.2 completado  
**Total estimado:** 2.5 horas

---

### 1.4 Email Infrastructure Setup

**Proveedor recomendado:** Resend (€20/mes, developer-friendly)

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 1.4.1 | Crear cuenta en Resend | 5 min | ☐ |
| 1.4.2 | Verificar dominio (DNS records) | 15 min | ☐ |
| 1.4.3 | Crear API key | 5 min | ☐ |
| 1.4.4 | Añadir RESEND_API_KEY a .env | 2 min | ☐ |
| 1.4.5 | Crear template HTML base (header/footer) | 1.5 h | ☐ |
| 1.4.6 | Implementar función send_email en backend | 1 h | ☐ |
| 1.4.7 | Implementar cron job para scheduled emails | 1 h | ☐ |
| 1.4.8 | Test end-to-end con email real | 30 min | ☐ |

**Template HTML base (estructura):**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, sans-serif; line-height: 1.6; color: #1a1a1a; }
    .container { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
    .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5; color: #666; font-size: 14px; }
    a { color: #2563eb; }
  </style>
</head>
<body>
  <div class="container">
    <!-- CONTENT HERE -->
    
    <div class="footer">
      <p>Sampelit · Barcelona</p>
      <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
    </div>
  </div>
</body>
</html>
```

**Responsable:** Tú  
**Dependencias:** Dominio configurado  
**Total estimado:** 4-5 horas

---

### 1.5 Blog Content (Parcialmente existe)

**Estado actual:** 1/7 artículos escritos (`copy-testing-guide.md`)

#### Prioridad de escritura:

| # | Artículo | Por qué prioritario | Tiempo | Estado |
|---|----------|---------------------|--------|--------|
| 1.5.1 | Complete Guide to A/B Testing | SEO cornerstone, alto volumen | 4-5 h | ☐ |
| 1.5.2 | How Much Traffic Do You Need | Filtro de leads, FAQ común | 2-3 h | ☐ |
| 1.5.3 | 7 Critical A/B Testing Mistakes | Shareability, pain points | 2-3 h | ☐ |

#### Subtareas para cada artículo:

| # | Tarea | Tiempo |
|---|-------|--------|
| X.a | Research: revisar competencia y keywords | 30 min |
| X.b | Outline: estructura de secciones | 20 min |
| X.c | Escribir draft completo | 2-3 h |
| X.d | Añadir ejemplos concretos | 30 min |
| X.e | Crear 1-2 gráficos/tablas | 30 min |
| X.f | SEO: meta description, internal links | 15 min |
| X.g | Review final y publicar | 15 min |

**Responsable:** Tú o Freelance writer (€100-200/artículo)  
**Dependencias:** Ninguna  
**Total estimado:** 10-15 horas para los 3 artículos

---

### 1.6 Case Study #1 (NO EXISTE — Importante)

**Archivo a crear:** `content/blog/case-studies/homepage-headline-test.md`

> Documentar el experimento que estás corriendo en tu propia landing.

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 1.6.1 | Definir qué métricas mostrar | 15 min | ☐ |
| 1.6.2 | Capturar screenshots del dashboard | 10 min | ☐ |
| 1.6.3 | Escribir "Background" section | 20 min | ☐ |
| 1.6.4 | Escribir "Hypothesis" section | 10 min | ☐ |
| 1.6.5 | Documentar variantes probadas | 15 min | ☐ |
| 1.6.6 | Escribir "Results" section | 30 min | ☐ |
| 1.6.7 | Escribir "What We Learned" section | 20 min | ☐ |
| 1.6.8 | Escribir "Next Steps" section | 10 min | ☐ |
| 1.6.9 | Formatear según template en README | 15 min | ☐ |

**Estructura del case study:**

```markdown
# Landing Page Headline Test: Our First Public Experiment

## Summary
- **What we tested:** Homepage headline (9 variants)
- **Duration:** 21 days
- **Traffic:** 4,500 visitors
- **Result:** Variant B won
- **Impact:** +18% signup rate

## Background
We practice what we preach. Before asking customers to test their sites...

## Hypothesis
"We believe that a benefit-focused headline will outperform 
a feature-focused headline because visitors care about outcomes, 
not tools."

## Variants
| # | Headline | Rationale |
|---|----------|-----------|
| Control | "A/B Testing Platform" | Descriptive, neutral |
| A | "Test Your Copy. Increase Conversions." | Benefit-focused |
| B | "Stop Guessing. Start Testing." | Pain-focused |
...

## Results
[Chart/Screenshot]

## What We Learned
1. Pain-focused copy resonated more than benefit-focused
2. Shorter headlines performed better overall
3. The word "Guessing" triggered recognition

## Next Steps
Testing CTA button copy next (Sign Up vs Get Started vs Try Free)
```

**Responsable:** Tú  
**Dependencias:** Experimento con datos suficientes  
**Total estimado:** 2.5 horas

---

### 1.7 Ad Creativos/Diseños (NO EXISTEN)

**Necesario para:** Instagram ads definidos en `instagram_ads.md`

#### Subtareas:

| # | Tarea | Especificaciones | Tiempo | Estado |
|---|-------|------------------|--------|--------|
| 1.7.1 | Definir specs de imágenes | 1080x1080 (feed), 1080x1920 (stories) | 10 min | ☐ |
| 1.7.2 | Crear mockup de dashboard (clean) | Para Ad 1 "Live Experiment" | 1 h | ☐ |
| 1.7.3 | Crear pricing comparison graphic | Para Ad 2 "Price Differentiator" | 30 min | ☐ |
| 1.7.4 | Crear audit trail screenshot | Para Ad 3 "Transparency" | 30 min | ☐ |
| 1.7.5 | Crear minimal graph visualization | Para Ad 4 "Understatement" | 30 min | ☐ |
| 1.7.6 | Barcelona/European aesthetic image | Para Ad 5 "European Craft" | 30 min | ☐ |
| 1.7.7 | Neuro/brain visual | Para Ad 6 "Data Statement" | 30 min | ☐ |
| 1.7.8 | Adaptar cada imagen a formato stories | 1080x1920 vertical | 1 h | ☐ |
| 1.7.9 | Crear OG images para blog posts | 1200x630 | 1 h | ☐ |

**Herramientas:**
- Figma (diseño)
- Canva (alternativa rápida)
- Screenshots reales del dashboard

**Responsable:** Tú o Freelance designer (€50-100/set)  
**Dependencias:** Dashboard funcional para screenshots  
**Total estimado:** 5-6 horas DIY, 2h + €100 con freelancer

---

### 1.8 Analytics/Tracking Implementation

**Referencia:** `content/marketing/conv_track.md` (eventos ya definidos)

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 1.8.1 | Elegir analytics tool (Plausible vs PostHog) | 15 min | ☐ |
| 1.8.2 | Crear cuenta y obtener script | 10 min | ☐ |
| 1.8.3 | Implementar script en todas las páginas | 30 min | ☐ |
| 1.8.4 | Implementar evento `landing_view` | 15 min | ☐ |
| 1.8.5 | Implementar evento `simulate_start` | 15 min | ☐ |
| 1.8.6 | Implementar evento `simulate_complete` | 15 min | ☐ |
| 1.8.7 | Implementar evento `email_submit` | 15 min | ☐ |
| 1.8.8 | Implementar evento `dashboard_click` | 15 min | ☐ |
| 1.8.9 | Definir estructura de UTM parameters | 20 min | ☐ |
| 1.8.10 | Documentar UTM naming convention | 15 min | ☐ |
| 1.8.11 | Test end-to-end de todos los eventos | 30 min | ☐ |

**UTM Structure propuesta:**

```
utm_source: [platform]     → instagram, google, linkedin, email
utm_medium: [type]         → paid, organic, cpc, newsletter
utm_campaign: [name]       → launch_2024, waitlist, retarget
utm_content: [variant]     → ad1_dashboard, ad2_pricing, cta_blue
utm_term: [keyword]        → ab_testing (solo para search ads)

Ejemplo completo:
https://sampelit.com/?utm_source=instagram&utm_medium=paid&utm_campaign=launch_2024&utm_content=ad1_dashboard
```

**Responsable:** Tú  
**Dependencias:** Ninguna  
**Total estimado:** 3 horas

---

## Fase 2: Launch (Semana 3-4)

> Activar canales y conseguir primeros usuarios de pago.

### 2.1 Waitlist → Paid Conversion

**Referencia:** `content/marketing/email_seq.md`

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 2.1.1 | Segmentar waitlist por engagement | 30 min | ☐ |
| 2.1.2 | Escribir email de "Spots opening" | 20 min | ☐ |
| 2.1.3 | Definir early adopter discount (50% off = €74.50/mo) | 10 min | ☐ |
| 2.1.4 | Crear landing page específica para waitlist | 1 h | ☐ |
| 2.1.5 | Enviar batch 1 (top 20% engaged) | 15 min | ☐ |
| 2.1.6 | Monitorear conversiones 48h | — | ☐ |
| 2.1.7 | Enviar batch 2 (resto) | 15 min | ☐ |
| 2.1.8 | Follow-up a no-openers | 15 min | ☐ |

**Email "Spots Opening" (estructura):**

```
Subject: Your spot is ready

Hi,

A spot opened up. You can now access Sampelit.

What you get:
- Full access to the testing platform
- Visual Editor for no-code setup
- Adaptive optimization from day one

Pricing:
- Starter: €149/month (5 experiments, 25k visitors)
- Professional: €399/month (25 experiments, 100k visitors)

As an early adopter, you get 50% off your first year.
That's €74.50/month for Starter.

Set up your account: [link]

This offer is valid for 7 days.

—
Sampelit
```

**Responsable:** Tú  
**Dependencias:** 1.2, 1.4 completados  
**Total estimado:** 3 horas

---

### 2.2 Instagram Ads Launch

**Referencia:** `content/marketing/instagram_ads.md`

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 2.2.1 | Crear Meta Business Account (si no existe) | 15 min | ☐ |
| 2.2.2 | Configurar Meta Pixel en el sitio | 30 min | ☐ |
| 2.2.3 | Crear Custom Audience: Waitlist emails | 20 min | ☐ |
| 2.2.4 | Crear Lookalike Audience (1%) | 10 min | ☐ |
| 2.2.5 | Subir creativos (1.7) | 20 min | ☐ |
| 2.2.6 | Crear Campaign: Conversions objective | 20 min | ☐ |
| 2.2.7 | Crear Ad Set 1: DACH countries | 15 min | ☐ |
| 2.2.8 | Crear Ad Set 2: Nordics | 15 min | ☐ |
| 2.2.9 | Crear Ad Set 3: US/UK | 15 min | ☐ |
| 2.2.10 | Crear 6 ads (copy de instagram_ads.md) | 1 h | ☐ |
| 2.2.11 | Set daily budget: €20/día inicial | 5 min | ☐ |
| 2.2.12 | Launch y monitorear 48h | — | ☐ |
| 2.2.13 | Kill underperformers, scale winners | 30 min | ☐ |

**Budget por fase (de `growth-tactics.md`):**

| MRR | Budget/mes | Target CPA |
|-----|------------|------------|
| €0-2k | €200 | €150 |
| €2k-5k | €500 | €120 |
| €5k-10k | €1000 | €100 |

**Responsable:** Tú  
**Dependencias:** 1.7, 1.8 completados  
**Total estimado:** 4 horas setup, ongoing optimization

---

### 2.3 LinkedIn Organic Content

**Referencia:** `docs/business/growth-tactics.md`

#### Content Calendar (Semana 1-4):

| Día | Tipo | Tema | Estado |
|-----|------|------|--------|
| Lun S1 | Contrarian | "Most A/B tests are inconclusive. That's okay." | ☐ |
| Mie S1 | Micro case study | Tu primer resultado de experimento | ☐ |
| Vie S1 | Educational | "The 95% confidence myth" | ☐ |
| Lun S2 | Contrarian | "Testing doesn't create demand" | ☐ |
| Mie S2 | Behind the scenes | "We test our own landing pages" | ☐ |
| Vie S2 | Educational | "When to stop an A/B test" | ☐ |
| Lun S3 | Micro case study | Resultado de segundo experimento | ☐ |
| Mie S3 | Contrarian | "Most teams test the wrong things" | ☐ |
| Vie S3 | Educational | "Copy testing > Design testing" | ☐ |
| Lun S4 | Announcement | "We're live. Here's what we learned." | ☐ |
| Mie S4 | Social proof | First customer testimonial | ☐ |
| Vie S4 | Educational | Link to blog post | ☐ |

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 2.3.1 | Escribir 12 posts (batch writing) | 3 h | ☐ |
| 2.3.2 | Programar en Buffer/native scheduler | 30 min | ☐ |
| 2.3.3 | Engagement: respond to comments daily | 10 min/día | ☐ |
| 2.3.4 | Track: clicks, impressions, followers | 15 min/sem | ☐ |

**Post template (Contrarian):**

```
Most people think A/B testing is about finding winners.

It's not.

It's about reducing uncertainty.

Most tests are inconclusive. That's okay.
The value is in the process, not just the wins.

---

We built Sampelit to help teams test smarter.
Not to promise miracles.

Link in comments.
```

**Responsable:** Tú  
**Dependencias:** Ninguna  
**Total estimado:** 4 horas inicial, 2h/semana ongoing

---

### 2.4 SEO Quick Wins

#### Subtareas:

| # | Tarea | Tiempo | Estado |
|---|-------|--------|--------|
| 2.4.1 | Submit sitemap to Google Search Console | 15 min | ☐ |
| 2.4.2 | Submit sitemap to Bing Webmaster | 10 min | ☐ |
| 2.4.3 | Verificar todas las páginas tienen meta descriptions | 30 min | ☐ |
| 2.4.4 | Verificar OG tags en todas las páginas | 20 min | ☐ |
| 2.4.5 | Crear y subir robots.txt | 10 min | ☐ |
| 2.4.6 | Verificar mobile-friendliness (Google tool) | 15 min | ☐ |
| 2.4.7 | Check PageSpeed score, fix critical issues | 1 h | ☐ |
| 2.4.8 | Set up rank tracking (Ahrefs free o SERPWatcher) | 20 min | ☐ |

**Responsable:** Tú  
**Dependencias:** Blog posts publicados  
**Total estimado:** 3 horas

---

## Fase 3: Growth (Ongoing)

> Optimizar canales, escalar lo que funciona, eliminar lo que no.

### 3.1 Weekly Marketing Routine

| Día | Tarea | Tiempo |
|-----|-------|--------|
| **Lunes** | Review métricas semana anterior | 30 min |
| | Publicar LinkedIn post #1 | 10 min |
| **Martes** | Respond to comments/emails | 20 min |
| **Miércoles** | Publicar LinkedIn post #2 | 10 min |
| | Check ad performance, adjust bids | 20 min |
| **Jueves** | Write/edit blog content | 1-2 h |
| **Viernes** | Publicar LinkedIn post #3 | 10 min |
| | Week review, plan siguiente semana | 30 min |

**Total semanal:** ~5-6 horas

---

### 3.2 Monthly Review Checklist

| Métrica | Target | Cómo medir |
|---------|--------|------------|
| Website visitors | +20% MoM | Analytics |
| Email open rate | >40% | Resend dashboard |
| Email click rate | >10% | Resend dashboard |
| Instagram CTR | >1% | Meta Ads Manager |
| Instagram CPA | <€150 | Meta Ads Manager |
| Blog posts published | 4/mes | Content calendar |
| LinkedIn followers | +100/mes | LinkedIn |
| Signups | — | Database |
| Paid conversions | — | Stripe |
| Churn rate | <5% | Stripe |

---

### 3.3 Content Backlog (Post-Launch)

**Prioridad media:** Escribir cuando haya tiempo

| Artículo | Keyword target | Status |
|----------|----------------|--------|
| A/B vs Multivariate Testing | "multivariate testing" | ☐ Outline |
| Statistical Significance Explained | "statistical significance ab test" | ☐ Outline |
| A/B Test Hypothesis Framework | "ab test hypothesis" | ☐ Outline |
| Case Study #2 | — | ☐ Pendiente datos |
| Case Study #3 | — | ☐ Pendiente datos |

---

### 3.4 Channel Expansion (Mes 3+)

> Solo después de validar Instagram + LinkedIn

| Canal | Prerequisito | Esfuerzo |
|-------|--------------|----------|
| Google Ads | Blog posts rankeando | Alto |
| Twitter/X | Audiencia tech activa | Medio |
| YouTube | Tutoriales grabados | Alto |
| Podcast guesting | 10+ customers | Bajo |
| Product Hunt | Product estable | Medio |
| Partnerships | 20+ customers | Alto |

---

## Resumen de Tiempos

| Fase | Total estimado |
|------|----------------|
| Fase 0: Housekeeping | 2-3 horas |
| Fase 1: Pre-Launch | 35-45 horas |
| Fase 2: Launch | 15-20 horas |
| Fase 3: Ongoing | 5-6 horas/semana |

**Timeline realista:**
- Fase 0: 1 día
- Fase 1: 2-3 semanas (trabajando ~15h/semana en marketing)
- Fase 2: 1-2 semanas
- Fase 3: Ongoing

---

## Archivos a Crear (Resumen)

| Archivo | Prioridad | Fase |
|---------|-----------|------|
| `content/marketing/pricing_page.md` | 🔴 Crítico | 1.1 |
| `content/marketing/onboarding_emails.md` | 🔴 Crítico | 1.2 |
| `content/marketing/lifecycle_emails.md` | 🟡 Importante | 1.3 |
| `content/blog/case-studies/homepage-headline-test.md` | 🟡 Importante | 1.6 |
| `content/blog/ab-testing-fundamentals/complete-guide.md` | 🟡 Importante | 1.5 |
| `content/blog/ab-testing-fundamentals/traffic-requirements.md` | 🟡 Importante | 1.5 |
| `content/blog/ab-testing-fundamentals/common-mistakes.md` | 🟢 Nice to have | 1.5 |

---

## Quick Reference: Precios Correctos

```
Starter:      €149/mes   (Early adopter: €74.50/mes)
Professional: €399/mes   (Early adopter: €199.50/mes)
Scale:        €999/mes   (Early adopter: €499.50/mes)
Enterprise:   €2,499/mes (Custom)

Annual discount: 20% (equivale a 2 meses gratis)
```

---

**Siguiente paso:** ¿Por cuál fase/subtarea quieres empezar?
