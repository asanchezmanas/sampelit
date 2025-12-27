# Estrategia de Precios

Pricing para Europa Rica (DACH, Nordics) + Anglo markets.

**Última actualización:** Diciembre 2024

---

## Modelo de Adquisición

### Trial → Paid (No Freemium)

```
Visitante → Trial 14 días (sin tarjeta) → Paid
```

**Por qué trial en lugar de freemium:**
- Freemium atrae usuarios que nunca pagan
- Trial crea urgencia y compromiso
- 14 días es suficiente para ver valor (1-2 experimentos)
- Sin tarjeta inicial reduce fricción de entrada
- Pedimos tarjeta al día 10 (antes de que expire)

---

## Tiers Actuales

| Plan | Precio | Visitors/mes | Experimentos | Target |
|------|--------|--------------|--------------|--------|
| **Starter** | €149/mes | 50,000 | 5 activos | Indie hackers, startups pequeñas |
| **Professional** | €399/mes | 200,000 | 25 activos | Startups con producto validado |
| **Scale** | €999/mes | 1,000,000 | Ilimitados | Scale-ups, equipos de 10+ |
| **Enterprise** | €2,499/mes | Custom | Custom | Empresas grandes, requisitos custom |

### Descuento Anual
- 20% off en pago anual (2 meses gratis)
- Starter anual: €1,430/año (vs €1,788)
- Professional anual: €3,830/año (vs €4,788)

---

## Posicionamiento vs Competencia

| Herramienta | Precio entrada | Precio mid-market | Modelo |
|-------------|----------------|-------------------|--------|
| Optimizely | ~€50k/año | €100k+ | Enterprise sales |
| VWO | €199/mes | €800+/mes | Self-serve + sales |
| AB Tasty | ~€1,500/mes | €3,000+/mes | Enterprise |
| Convert | €249/mes | €599/mes | Self-serve |
| **Sampelit** | €149/mes | €399/mes | 100% self-serve |

### Diferenciadores de precio

1. **100% self-serve**: Sin llamadas de ventas = costes bajos = precios bajos
2. **Solo A/B testing**: No heatmaps, no surveys = producto focused = más barato
3. **Europa-first**: Pricing en euros, GDPR nativo, sin markup de conversión

---

## Por qué €149 y no €49

| Factor | €49 | €149 |
|--------|-----|------|
| Percepción en DACH/Nordics | "Barato, ¿será bueno?" | "Razonable para B2B" |
| LTV con 5% churn | €980 | €2,980 |
| CAC permitido | €100 | €300 |
| Clientes para €10k MRR | 204 | 67 |
| Soporte por cliente | Insostenible | Manejable |

**Conclusión:** €149 permite mejor marketing, mejor soporte, menos clientes más valiosos.

---

## Trial Mechanics

### Día 0-7: Onboarding
- Acceso completo a Professional features
- Límite: 10,000 visitors (suficiente para probar)
- Emails: Día 1, 3, 5 (ver onboarding_emails.md)

### Día 8-10: Conversión
- Email día 8: "Tu trial termina en 6 días"
- Email día 10: "Añade método de pago para continuar"
- In-app: Banner persistente

### Día 11-14: Urgencia
- Email día 12: "Últimos 2 días"
- Email día 14: "Trial terminado"
- Experimentos pausados automáticamente

### Post-Trial (sin pago)
- Datos guardados 30 días
- Puede reactivar con pago
- No puede crear nuevos experimentos

---

## Upgrade Path

```
Trial → Starter: Al terminar trial
Starter → Professional: > 50k visitors o > 5 experimentos activos
Professional → Scale: > 200k visitors o > 25 experimentos
Scale → Enterprise: Necesita SLA, SSO, o custom integrations
```

### Triggers de upgrade (in-app)

| Trigger | Mensaje |
|---------|---------|
| 80% visitors usados | "Estás cerca del límite. Upgrade para más tráfico." |
| 5/5 experimentos activos | "Has llegado al máximo. Upgrade para más experimentos." |
| Intenta crear experimento 6 | Modal de upgrade con comparación de planes |

---

## Pricing Psychology

### Anchoring en pricing page

1. Mostrar Enterprise primero (€2,499) → ancla alta
2. Destacar Professional como "Most Popular"
3. Starter parece "deal" comparado

### Framing correcto

```
✓ "€399/month = €13/day"
✓ "€399/month = less than 1 hour of a CRO consultant"
✓ "Most A/B tools charge €1,500+/month for similar features"
✓ "No setup fees, no contracts, cancel anytime"

✗ "Just €399/month!" (suena cheap)
✗ "Affordable pricing" (devalúa)
✗ "Cheapest on the market" (race to bottom)
```

---

## Descuentos

### Permitidos

| Descuento | Cuándo | Límite |
|-----------|--------|--------|
| 20% anual | Siempre disponible | Standard |
| 30% startups | < €1M raised, < 10 empleados | Verificación manual |
| 50% early adopter | Primeros 50 clientes | Ya cerrado |

### NO permitidos

| Práctica | Por qué evitar |
|----------|----------------|
| Descuentos por "negociación" | Crea precedente, no escala |
| Custom pricing por cliente | Complejidad operativa |
| Bajar precio para cerrar deal | Devalúa producto |
| Meses gratis sin razón | Atrae clientes de bajo valor |

---

## Métricas de Pricing

| Métrica | Target | Alarma |
|---------|--------|--------|
| ARPU | €275+ | < €200 |
| % en Starter | 40-50% | > 70% |
| % en Professional | 35-45% | < 25% |
| % en Scale/Enterprise | 10-15% | < 5% |
| Trial → Paid conversion | 25%+ | < 15% |
| Annual vs Monthly | 30%+ annual | < 15% annual |

---

## Revisión de Precios

### Cuándo subir precios

- ARPU estancado y churn bajo
- Competidores suben precios
- Features significativos añadidos
- Inflación acumulada > 10%

### Cuándo NO tocar precios

- Churn alto (problema de valor, no de precio)
- Primeros 100 clientes (aún validando)
- Sin mejoras significativas en producto

### Grandfather policy

- Clientes existentes mantienen precio 12 meses
- Aviso 60 días antes de subida
- Opción de lock-in anual al precio actual
