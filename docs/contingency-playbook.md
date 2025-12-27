# Contingency Playbook

Planes de acción para escenarios negativos. Léelo antes de que pase.

**Última actualización:** Diciembre 2024

---

## 🎯 Filosofía

1. **Planifica en frío, ejecuta en caliente.** Las crisis no son momento para improvisar.
2. **Triggers claros.** Define cuándo activar cada plan ANTES de que pase.
3. **Acciones concretas.** Nada de "evaluar opciones" — lista de pasos específicos.
4. **Reversibilidad.** Prioriza acciones que puedas deshacer si te equivocas.

---

## 🔴 Escenario 1: Churn Spike

### Trigger
- Churn > 10% en un mes
- O 5+ churns en una semana (cuando tienes <50 clientes)

### Diagnóstico inmediato (Día 1)

```
[ ] Listar todos los churns del período
[ ] Clasificar por:
    - Tier (Starter/Pro/Scale)
    - Tiempo como cliente
    - Última actividad
    - Razón declarada (si hay)
[ ] Buscar patrón común
```

### Patrones comunes y acciones

| Patrón | Causa probable | Acción |
|--------|----------------|--------|
| Todos son Starter, <2 meses | No ven valor rápido | Mejorar onboarding |
| Todos mencionan competidor X | Feature gap o precio | Análisis competitivo |
| Todos son de un canal específico | Wrong audience | Pausar ese canal |
| Random, sin patrón | Producto o market fit | Entrevistas profundas |
| Todos post-experimento fallido | Expectativas vs realidad | Mejorar educación |

### Plan de acción

**Semana 1:**
1. PAUSAR todo gasto en acquisition
2. Email personal a cada churned user pidiendo 10 min de feedback
3. Ofrecer: "Te devuelvo el último mes si me das 15 min de tu tiempo"
4. Documentar CADA respuesta

**Semana 2:**
5. Analizar respuestas, identificar top 3 razones
6. Priorizar fix más impactante
7. Implementar fix o workaround

**Semana 3:**
8. Contactar usuarios en riesgo (baja actividad) proactivamente
9. Ofrecer ayuda personalizada
10. Monitorear si churn se estabiliza

**Semana 4:**
11. Si churn < 8%, reactivar acquisition gradualmente
12. Si churn sigue alto, repetir ciclo

### Scripts de contacto

**Email a churned user:**
```
Subject: Quick question about your Sampelit experience

Hi [Name],

I noticed you cancelled your Sampelit subscription. 
No hard feelings — I just want to understand what happened.

Would you have 10 minutes for a quick call or email exchange? 
I'll refund your last month as a thank you for your time.

What didn't work for you?

[Tu nombre]
Founder, Sampelit
```

**Email a usuario en riesgo (sin actividad 14+ días):**
```
Subject: Everything okay with your experiments?

Hi [Name],

I noticed you haven't run any experiments lately. 
Just checking in — is everything working okay?

If you're stuck on something, reply and I'll personally help you out.

[Tu nombre]
```

---

## 🔴 Escenario 2: MRR Drop Severo

### Trigger
- MRR baja 20%+ en un mes
- O MRR baja 10%+ dos meses consecutivos

### Clasificación

| Causa | Síntomas | Plan |
|-------|----------|------|
| Churn spike | Muchas cancelaciones | Ver Escenario 1 |
| Downgrades | Scale→Pro, Pro→Starter | Revisar value por tier |
| Payment failures | Tarjetas rechazadas | Fix dunning + outreach |
| Seasonality | Mismo patrón año anterior | Aguantar, ajustar runway |
| Macro event | Todo el mercado afectado | Modo supervivencia |

### Plan de acción inmediato (Día 1-3)

```
[ ] Identificar causa exacta (churn vs downgrade vs payment)
[ ] Calcular nuevo runway con burn actual
[ ] Si runway < 12 meses: activar modo austeridad
```

### Modo Austeridad

**Cortar inmediatamente:**
- [ ] Ads (todo)
- [ ] Herramientas no esenciales
- [ ] Freelancers/contractors
- [ ] Cualquier gasto "nice to have"

**Mantener:**
- [ ] Hosting/infra (obvio)
- [ ] Dominio/email
- [ ] Stripe (no hay opción)
- [ ] Tu sueldo mínimo vital

**Objetivo:** Extender runway a 18+ meses

### Comunicación

**NO hacer:**
- Anunciar públicamente que hay problemas
- Subir precios de golpe
- Enviar emails desesperados

**SÍ hacer:**
- Contacto personal con top customers
- Ofrecer lock-in anual con descuento
- Pedir referrals a clientes satisfechos

---

## 🔴 Escenario 3: Competidor Grande Entra

### Trigger
- Optimizely/VWO lanza tier barato
- Nuevo player con funding significativo
- Feature parity con precio menor

### Diagnóstico

| Pregunta | Acción según respuesta |
|----------|------------------------|
| ¿Compiten en MI nicho exacto? | Sí: preocupante. No: menos urgente |
| ¿Precio significativamente menor? | Sí: no competir en precio. No: ok |
| ¿Mejor producto objetivamente? | Sí: acelerar roadmap. No: marketing |
| ¿Mis clientes mencionan el competidor? | Sí: urgente. No: ruido externo |

### Plan de acción

**Semana 1: Intel**
1. Crear cuenta en el competidor (trial)
2. Documentar: pricing, features, UX, onboarding
3. Identificar sus debilidades
4. Actualizar competitor-intel.md

**Semana 2: Positioning**
5. Reforzar diferenciadores únicos
6. Actualizar landing page con comparación implícita
7. Crear/actualizar página de comparación directa

**Semana 3: Retention**
8. Contactar top 20 clientes personalmente
9. Preguntar si han visto al competidor
10. Ofrecer lock-in anual si hay riesgo

**Ongoing:**
- NO entrar en guerra de precios
- NO copiar features solo porque ellos los tienen
- SÍ duplicar lo que te hace único
- SÍ acelerar en tu nicho específico

### Posibles pivots de positioning

| Si competidor es... | Pivot a... |
|---------------------|------------|
| Enterprise-focused | "Built for startups & SMBs" |
| Feature-heavy | "Simple, focused, fast" |
| US-centric | "Made in Europe, for Europe" |
| Requires sales calls | "100% self-serve, start in 5 min" |
| Expensive | "Same power, fair price" |

---

## 🔴 Escenario 4: Problema Técnico Grave

### Trigger
- Downtime > 4 horas
- Data loss (cualquier cantidad)
- Security breach
- Bug que afecta experimentos activos

### Plan inmediato (Hora 1)

```
[ ] Confirmar alcance del problema
[ ] Si es seguridad: activar incident response
[ ] Poner página de status o banner
[ ] NO comunicar hasta entender el problema
```

### Comunicación según severidad

**Nivel 1: Downtime < 1 hora, sin data loss**
- No requiere comunicación pública
- Monitorear que no se repita

**Nivel 2: Downtime 1-4 horas, sin data loss**
```
Email a clientes afectados:

Subject: Sampelit service interruption - resolved

Hi [Name],

We experienced a service interruption today from [time] to [time]. 
The issue has been resolved and all your data is safe.

What happened: [brief explanation]
What we're doing: [prevention measures]

Sorry for any inconvenience. Your experiments have resumed normally.

[Tu nombre]
```

**Nivel 3: Downtime > 4 horas O data loss**
```
Email a TODOS los clientes:

Subject: Important: Sampelit service incident

Hi [Name],

I want to personally inform you about a service incident 
we experienced today.

What happened:
[Honest explanation without technical jargon]

Impact to your account:
[Specific impact, if any]

What we're doing:
1. [Immediate fix]
2. [Prevention measure]
3. [Compensation if applicable]

I take full responsibility for this. If you have questions, 
reply directly to this email.

[Tu nombre]
Founder, Sampelit
```

**Nivel 4: Security breach**
- Consultar con abogado antes de comunicar
- Notificar según GDPR si aplica (72h)
- Comunicación debe ser legal-reviewed

### Compensación

| Impacto | Compensación |
|---------|--------------|
| Downtime < 4h | Nada o email de disculpa |
| Downtime 4-24h | 1 semana gratis |
| Downtime > 24h | 1 mes gratis |
| Data loss (recoverable) | 1 mes gratis + sesión personal |
| Data loss (permanent) | Refund completo + ayuda a migrar |

---

## 🔴 Escenario 5: Burnout Personal

### Señales de alerta

- [ ] Trabajando 60+ horas/semana consistentemente
- [ ] No puedes desconectar en fines de semana
- [ ] Ansiedad al ver notificaciones
- [ ] Resentimiento hacia clientes/producto
- [ ] Problemas de sueño relacionados con trabajo
- [ ] Descuidando salud, relaciones, hobbies

### Plan de acción

**Inmediato (esta semana):**
1. Bloquear calendario: NO trabajo después de las 19h
2. Desactivar notificaciones de email en móvil
3. Identificar las 3 tareas que más estrés causan
4. Delegar o eliminar 1 de esas tareas

**Corto plazo (próximas 2 semanas):**
5. Configurar auto-responder: "Respondo en 24-48h"
6. Batch emails: solo 2x al día
7. Planificar 2 días off (no "vacaciones", solo desconexión)
8. Hablar con alguien de confianza sobre el estado

**Estructural (próximo mes):**
9. Revisar qué tareas puedes automatizar
10. Considerar contractor para soporte si tienes budget
11. Establecer límites claros con clientes
12. Aceptar que 80% está bien, no todo tiene que ser perfecto

### Recordatorios

- El negocio no vale nada si tú no estás sano
- Los clientes pueden esperar 24h para una respuesta
- Nadie se muere si hay un bug por unas horas
- 37 clientes no requieren 60h/semana de trabajo

---

## 🔴 Escenario 6: Cash Flow Crisis

### Trigger
- Runway < 6 meses
- O gastos > revenue por 3+ meses

### Plan de acción

**Semana 1: Cortar**
```
[ ] Cancelar TODOS los gastos no esenciales
[ ] Lista de gastos ordenada por prescindibilidad
[ ] Cortar de abajo hacia arriba
[ ] Calcular nuevo runway
```

**Semana 2: Ingresar**
```
[ ] Ofrecer descuento 40% por pago anual adelantado
[ ] Contactar clientes grandes para upgrade
[ ] Pedir pagos adelantados si hay deals en pipeline
[ ] Considerar consulting/freelance temporal
```

**Semana 3: Evaluar**
```
[ ] Si runway > 12 meses: crisis resuelta, mantener disciplina
[ ] Si runway 6-12 meses: seguir en modo austeridad
[ ] Si runway < 6 meses: considerar opciones drásticas
```

### Opciones drásticas (último recurso)

| Opción | Pros | Cons |
|--------|------|------|
| Buscar funding | Cash inmediato | Dilución, pérdida de control |
| Vender negocio | Exit, aunque pequeño | Fin del proyecto |
| Pausar negocio | Preservar lo construido | Momentum perdido |
| Pivot radical | Nueva oportunidad | Riesgo alto |
| Trabajo part-time | Cash seguro | Menos tiempo para Sampelit |

---

## 📋 Checklist Pre-Crisis

Cosas que deberías tener listas ANTES de que pase algo:

### Documentación
- [ ] Accesos a todas las cuentas en password manager
- [ ] Documentación de arquitectura básica
- [ ] Backup de datos de clientes (automático)
- [ ] Contacto de abogado/gestor guardado

### Financiero
- [ ] 12+ meses de runway
- [ ] Línea de crédito pre-aprobada (por si acaso)
- [ ] Gastos clasificados por esencialidad

### Comunicación
- [ ] Templates de crisis guardados
- [ ] Lista de emails de todos los clientes
- [ ] Página de status configurada

### Personal
- [ ] Persona de confianza que sabe del negocio
- [ ] Actividades fuera del trabajo
- [ ] Límites de horario establecidos

---

## 📞 Contactos de Emergencia

| Situación | Contacto |
|-----------|----------|
| Legal/contractual | [Nombre abogado] |
| Fiscal | [Nombre gestor] |
| Hosting down | Render support |
| Database | Supabase support |
| Payments | Stripe support |
| Burnout/mental health | [Persona de confianza / profesional] |
