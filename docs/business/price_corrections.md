# Correcciones de Precio — Cambios Requeridos

**Precio correcto:** €149 / €399 / €999 / €2,499  
**Precio incorrecto (legacy):** €49

---

## Archivos a Corregir

### 1. landing.md

**Buscar y reemplazar:**

| Ubicación | Texto actual | Cambiar a |
|-----------|--------------|-----------|
| Pricing section | `€49/month` | `€149/month` |
| CTA o menciones | `just €49` | `€149` |
| Early adopter | `50% = €24.50` | `50% = €74.50` |

---

### 2. public_pages.md

**En FAQ section:**

| Pregunta | Texto actual | Cambiar a |
|----------|--------------|-----------|
| "How much does it cost?" | `Starting at €49/month` | `Starting at €149/month` |
| Cualquier mención de tiers | `€49/€99/€199` | `€149/€399/€999` |

---

### 3. email_seq.md

**Email 3 (Scarcity + Offer):**

| Ubicación | Texto actual | Cambiar a |
|-----------|--------------|-----------|
| Precio mencionado | `€49/month` | `€149/month` |
| Early adopter discount | `50% off = €24.50` | `50% off = €74.50` |
| Value anchor | `Less than €2/day` | `Less than €5/day` |

---

### 4. review_exchange.md

**Compensación:**

| Actual | Problema | Cambiar a |
|--------|----------|-----------|
| 12 meses gratis | €1,788 de valor (excesivo) | 2 meses gratis (€298 valor) |

**Texto sugerido:**

```
Compensation for detailed review:
- 2 months free on your current plan
- OR: Featured in our case study section with backlink

Requirements:
- Minimum 30 days as paying customer
- Review must be 100+ words
- Posted on G2, Capterra, or LinkedIn
```

---

### 5. financial-plan.md

**Recalcular proyecciones con €149 base:**

| Métrica | Valor actual (€49) | Valor correcto (€149) |
|---------|--------------------|-----------------------|
| MRR por cliente Starter | €49 | €149 |
| Break-even customers | ~X | ~Y (recalcular) |
| Year 1 projection | Basado en €49 | Recalcular |

**Nota:** Este archivo necesita recálculo completo, no solo find/replace.

---

## Verificación Rápida

Después de hacer los cambios, buscar en todos los archivos:

```bash
grep -r "€49" content/
grep -r "49/month" content/
grep -r "€24" content/  # early adopter price antiguo
```

No debería haber resultados.

---

## Precios de Referencia (Copiar/Pegar)

### Precios Mensuales
```
Starter:      €149/month
Professional: €399/month
Scale:        €999/month
Enterprise:   €2,499/month
```

### Precios Anuales (20% descuento)
```
Starter:      €119/month (€1,428/year)
Professional: €319/month (€3,828/year)
Scale:        €799/month (€9,588/year)
Enterprise:   Custom
```

### Early Adopter (50% off primer año)
```
Starter:      €74.50/month
Professional: €199.50/month
Scale:        €499.50/month
```

### Value Anchors (para copy)
```
Starter:      "Less than €5/day"
Professional: "Less than €14/day"
Scale:        "Less than €33/day"
```

---

## Checklist Final

- [ ] landing.md actualizado
- [ ] public_pages.md actualizado
- [ ] email_seq.md actualizado
- [ ] review_exchange.md actualizado
- [ ] financial-plan.md recalculado
- [ ] Grep verification: no results for €49
- [ ] pricing_page.md creado (nuevo archivo)
- [ ] onboarding_emails.md creado (nuevo archivo)
