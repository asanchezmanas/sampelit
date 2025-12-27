# 🎯 Glosario de Términos Públicos

**Documento OBLIGATORIO para frontend y marketing**

Este documento define cómo comunicar las features sin revelar la tecnología interna.

---

## ⚠️ REGLA DE ORO

> **Nunca mencionar algoritmos específicos al usuario final.**
> Comunicar el BENEFICIO, no el MECANISMO.

---

## 📝 Tabla de Traducción

| ❌ Término Técnico (NUNCA usar) | ✅ Término Público (SIEMPRE usar) |
|--------------------------------|-----------------------------------|
| Thompson Sampling | **Optimización Inteligente** |
| Multi-Armed Bandit | **Distribución Adaptativa** |
| Bayesian Analysis | **Análisis Predictivo** |
| Win Probability | **Probabilidad de éxito** |
| Confidence Interval | **Rango de certeza** |
| Statistical Significance | **Resultado confiable** |
| Regret | **Oportunidades perdidas** |
| Posterior Distribution | **Predicción basada en datos** |
| Prior | (no mencionar) |
| Beta Distribution | (no mencionar) |
| Hash Chain | **Registro verificable** |
| Cryptographic Audit | **Historial seguro** |
| Algorithm Decision | **Decisión del sistema** |

---

## 🎨 Ejemplos en UI

### Panel de Optimización

```
❌ MAL (revela tecnología):
┌─────────────────────────────────────────┐
│ Thompson Sampling Distribution          │
│ Bayesian Win Probability: 94.2%         │
│ Beta(α=127, β=8) vs Beta(α=43, β=12)    │
└─────────────────────────────────────────┘

✅ BIEN (comunica valor):
┌─────────────────────────────────────────┐
│ Optimización Inteligente                │
│ Probabilidad de éxito: 94.2%            │
│ El sistema envía más tráfico al ganador │
└─────────────────────────────────────────┘
```

### Recomendación

```
❌ MAL:
"El análisis Bayesiano indica que la variante B 
tiene un posterior probability of being best de 94.2%"

✅ BIEN:
"Variante B tiene 94% de probabilidad de ser la mejor.
Puedes implementarla con confianza."
```

### Distribución de Tráfico

```
❌ MAL:
"Thompson Sampling asigna tráfico según Beta sampling"

✅ BIEN:
"El sistema aprende en tiempo real y envía 
más visitantes a la variante que mejor funciona"
```

### Audit Trail

```
❌ MAL:
"Hash chain criptográfico con SHA-256"

✅ BIEN:
"Todas las decisiones quedan registradas 
y son verificables. Nadie puede modificarlas."
```

---

## 💬 Frases Aprobadas

### Para Optimización Inteligente (antes Thompson Sampling)

- "El sistema aprende automáticamente cuál funciona mejor"
- "Más tráfico va al ganador mientras el test corre"
- "Optimización continua basada en resultados reales"
- "Menos visitantes ven versiones perdedoras"

### Para Análisis Predictivo (antes Bayesian)

- "Probabilidad de que cada versión sea la mejor"
- "Predicción basada en tus datos reales"
- "Saber cuándo tienes suficiente confianza para decidir"
- "No solo 'ganó' o 'perdió', sino cuánto"

### Para Registro Verificable (antes Hash Chain)

- "Historial completo de cada decisión"
- "Resultados auditables y verificables"
- "Nadie puede manipular los datos después"
- "Transparencia total en cada paso"

---

## 🚫 Palabras Prohibidas en UI/Marketing

| Palabra | Por qué evitar |
|---------|----------------|
| Thompson | Nombre de algoritmo = ventaja competitiva |
| Bayesian / Bayes | Técnico, asusta a usuarios normales |
| Multi-Armed Bandit | Suena a casino, confuso |
| Beta Distribution | Muy técnico |
| Posterior / Prior | Jerga estadística |
| SHA-256 / Hash | Técnico, innecesario |
| Regret minimization | Concepto académico |

---

## ✅ Checklist para Copys

Antes de publicar cualquier texto en frontend:

- [ ] ¿Menciona algún algoritmo por nombre? → Reemplazar
- [ ] ¿Usa jerga estadística? → Simplificar
- [ ] ¿Un usuario normal lo entendería? → Si no, reescribir
- [ ] ¿Comunica el beneficio, no el mecanismo? → Si no, cambiar enfoque

---

## 📚 Más info

Este glosario se basa en principios de:
- Comunicar VALOR, no TECNOLOGÍA
- El usuario quiere RESULTADOS, no saber CÓMO funciona
- Proteger ventaja competitiva

