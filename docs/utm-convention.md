# UTM Naming Convention

**Objetivo:** Tracking consistente para atribuir conversiones correctamente  
**Aplicar en:** Todos los links externos (ads, emails, social, partnerships)

---

## Estructura de UTM

```
https://sampelit.com/?utm_source=X&utm_medium=X&utm_campaign=X&utm_content=X&utm_term=X
```

| Parámetro | Qué es | Obligatorio |
|-----------|--------|-------------|
| `utm_source` | Plataforma/origen | ✓ Sí |
| `utm_medium` | Tipo de tráfico | ✓ Sí |
| `utm_campaign` | Nombre de campaña | ✓ Sí |
| `utm_content` | Variante específica | Recomendado |
| `utm_term` | Keyword (solo search ads) | Solo para search |

---

## Reglas Generales

1. **Todo en minúsculas** — `instagram` no `Instagram`
2. **Sin espacios** — Usar guiones: `email-sequence` no `email sequence`
3. **Sin caracteres especiales** — Solo letras, números, guiones
4. **Consistencia** — Mismo nombre = mismo valor siempre
5. **Descriptivo pero corto** — `launch-jan-2025` no `january-2025-product-launch-campaign`

---

## UTM_SOURCE — Valores Permitidos

| Valor | Usar para |
|-------|-----------|
| `instagram` | Instagram (orgánico y paid) |
| `linkedin` | LinkedIn (orgánico y paid) |
| `twitter` | Twitter/X |
| `facebook` | Facebook (si usas) |
| `google` | Google Ads |
| `email` | Newsletters y secuencias |
| `resend` | Emails transaccionales |
| `partner` | Referrals de partners |
| `direct` | Links que compartes manualmente |
| `producthunt` | Product Hunt |
| `blog` | Links desde blogs externos |

---

## UTM_MEDIUM — Valores Permitidos

| Valor | Usar para |
|-------|-----------|
| `paid` | Cualquier ad pagado |
| `organic` | Posts orgánicos en social |
| `email` | Newsletters |
| `transactional` | Emails de sistema (onboarding, etc.) |
| `referral` | Links de partners/afiliados |
| `cpc` | Cost-per-click ads (Google) |
| `social` | Social media genérico |
| `pr` | Press/publicity |

---

## UTM_CAMPAIGN — Formato

```
[tipo]-[nombre]-[fecha-o-version]
```

### Ejemplos por Tipo

**Ads:**
- `ads-launch-jan2025`
- `ads-retargeting-q1`
- `ads-competitor-optimizely`

**Email:**
- `email-onboarding`
- `email-newsletter-weekly`
- `email-winback-30d`

**Social orgánico:**
- `social-casestudy-headline`
- `social-tips-weekly`

**Lanzamientos:**
- `launch-producthunt-jan2025`
- `launch-beta-invite`

---

## UTM_CONTENT — Formato

Identifica la variante específica dentro de una campaña.

```
[elemento]-[variante]
```

### Ejemplos

**Para ads:**
- `ad-dashboard` (ad mostrando dashboard)
- `ad-pricing` (ad mostrando pricing)
- `ad-testimonial` (ad con testimonial)

**Para emails:**
- `cta-header` (CTA en header)
- `cta-footer` (CTA en footer)
- `link-blog` (link al blog)

**Para A/B tests de ads:**
- `headline-a`
- `headline-b`
- `image-v1`
- `image-v2`

---

## UTM_TERM — Solo para Search Ads

Keyword que triggereó el ad.

```
utm_term=ab-testing-tool
utm_term=optimizely-alternative
utm_term=conversion-optimization
```

---

## Ejemplos Completos

### Instagram Ad

```
https://sampelit.com/?utm_source=instagram&utm_medium=paid&utm_campaign=ads-launch-jan2025&utm_content=ad-dashboard
```

### LinkedIn Organic Post

```
https://sampelit.com/blog/headline-test?utm_source=linkedin&utm_medium=organic&utm_campaign=social-casestudy-headline
```

### Newsletter Link

```
https://sampelit.com/pricing?utm_source=email&utm_medium=email&utm_campaign=email-newsletter-weekly&utm_content=cta-pricing
```

### Onboarding Email

```
https://sampelit.com/dashboard?utm_source=resend&utm_medium=transactional&utm_campaign=email-onboarding&utm_content=cta-dashboard
```

### Google Ads

```
https://sampelit.com/?utm_source=google&utm_medium=cpc&utm_campaign=ads-competitor-optimizely&utm_term=optimizely-alternative
```

### Product Hunt

```
https://sampelit.com/?utm_source=producthunt&utm_medium=referral&utm_campaign=launch-producthunt-jan2025
```

### Partner Referral

```
https://sampelit.com/?utm_source=partner&utm_medium=referral&utm_campaign=partner-[partnername]
```

---

## Quick Reference Table

| Canal | Source | Medium | Campaign (ejemplo) |
|-------|--------|--------|-------------------|
| Instagram Ad | `instagram` | `paid` | `ads-launch-jan2025` |
| Instagram Organic | `instagram` | `organic` | `social-tips-weekly` |
| LinkedIn Ad | `linkedin` | `paid` | `ads-retargeting-q1` |
| LinkedIn Organic | `linkedin` | `organic` | `social-casestudy-headline` |
| Google Ads | `google` | `cpc` | `ads-competitor-optimizely` |
| Newsletter | `email` | `email` | `email-newsletter-weekly` |
| Onboarding | `resend` | `transactional` | `email-onboarding` |
| Win-back | `resend` | `transactional` | `email-winback-30d` |
| Product Hunt | `producthunt` | `referral` | `launch-producthunt-jan2025` |
| Blog externo | `blog` | `referral` | `pr-[blogname]` |

---

## UTM Builder Template

### Google Sheets Formula

```
=CONCATENATE(
  "https://sampelit.com",
  A2,
  "?utm_source=", B2,
  "&utm_medium=", C2,
  "&utm_campaign=", D2,
  IF(E2<>"", CONCATENATE("&utm_content=", E2), ""),
  IF(F2<>"", CONCATENATE("&utm_term=", F2), "")
)
```

| A (Path) | B (Source) | C (Medium) | D (Campaign) | E (Content) | F (Term) |
|----------|------------|------------|--------------|-------------|----------|
| /pricing | instagram | paid | ads-launch-jan2025 | ad-dashboard | |
| /blog/case-study | linkedin | organic | social-casestudy | | |

---

## Tracking en Analytics

### En Plausible/PostHog

Los UTMs aparecen automáticamente en:
- Acquisition → Campaigns
- Acquisition → Sources
- Acquisition → Mediums

### Filtros Útiles

| Para ver... | Filtrar por... |
|-------------|----------------|
| Todo el paid | `medium = paid OR medium = cpc` |
| Todo email | `medium = email OR medium = transactional` |
| Una campaña específica | `campaign = [nombre]` |
| Performance de un ad | `content = [ad-variant]` |

---

## Errores Comunes a Evitar

| ❌ Mal | ✅ Bien | Por qué |
|--------|---------|---------|
| `Instagram` | `instagram` | Capitalización rompe consistencia |
| `email newsletter` | `email-newsletter` | Espacios rompen el tracking |
| `jan_2025` | `jan2025` | Underscores inconsistentes |
| `utm_source=ig` | `utm_source=instagram` | Abreviaciones confunden |
| Sin UTMs en ads | Siempre con UTMs | No puedes atribuir sin ellos |
| UTMs en links internos | Solo links externos | Rompe el tracking de sesión |

---

## Checklist Pre-Lanzamiento de Campaña

- [ ] Todos los links tienen UTMs
- [ ] Source está en la lista de valores permitidos
- [ ] Medium está en la lista de valores permitidos
- [ ] Campaign sigue el formato `[tipo]-[nombre]-[fecha]`
- [ ] Content identifica variantes si hay A/B test
- [ ] Todo en minúsculas, sin espacios
- [ ] Links testeados (no rotos)
- [ ] Documentado en spreadsheet de tracking

---

## Spreadsheet de Tracking (Template)

Mantén un Google Sheet con todas las URLs:

| Fecha | Canal | Campaña | URL Completa | Notas |
|-------|-------|---------|--------------|-------|
| 2025-01-15 | Instagram Ad | ads-launch-jan2025 | [url] | Dashboard creative |
| 2025-01-15 | Instagram Ad | ads-launch-jan2025 | [url] | Pricing creative |
| 2025-01-16 | LinkedIn | social-casestudy | [url] | Headline test post |
| 2025-01-20 | Newsletter | email-newsletter-weekly | [url] | Issue #1 |

Esto te permite:
- Buscar qué links usaste
- No repetir/confundir campaigns
- Auditar si algo no trackea bien
