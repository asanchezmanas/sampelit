# Eventos de Tracking - Sistema Completo

## Landing / Bio

| Evento | Qué mide | Cuándo se activa |
|--------|----------|------------------|
| `landing_view` | Cuántos entran al bloque de simulador | Al cargar la sección de simulador |
| `simulate_start` | Click en "Calcular / Ver impacto" | Cuando hacen click en CTA para iniciar simulación |
| `simulate_complete` | Usuario termina de introducir datos y ve resultado | Al mostrar resultados de simulación personalizada |
| `email_gate_view` | Cuántos ven el email gate | Al cargar la sección de email después del simulador |
| `email_submit` | Usuario deja su email | Al hacer submit del email |
| `dashboard_click` | Click al link "ver dashboard público" | Cuando hacen click para abrir dashboard read-only |
| `cta_soft_click` | Click en CTA suave (ej: "Start trial") | Cuando hacen click en CTA sin comprar aún |

---

## Stories (Instagram)

| Evento | Qué mide | Cuándo se activa |
|--------|----------|------------------|
| `story_view` | Cuántos ven cada story | Cada vez que se abre el story |
| `story_poll_interact` | Enganche con encuesta / poll | Cuando responden encuesta o votación |
| `story_link_click` | Click al enlace en bio desde story | Cuando hacen click en el swipe-up / link in bio |

---

## Email Follow-up

| Evento | Qué mide | Cuándo se activa |
|--------|----------|------------------|
| `email_open` | Cuántos abren el email | Tracking pixel del email |
| `email_click_dashboard` | Click al dashboard público | Click en link del email |
| `email_click_trial` | Click al CTA "start trial" | Click en link de prueba |
| `email_engagement` | Interacciones dentro del email | Click en otros links |

---

## Dashboard Público

| Evento | Qué mide | Cuándo se activa |
|--------|----------|------------------|
| `dashboard_view` | Cuántos visitan el dashboard público | Al cargar la página read-only |
| `variant_hover` | Interacción con variantes | Cuando pasan mouse sobre variante |
| `variant_expand` | Expanden detalles de una variante | Click en "+ info" o similar |
| `dashboard_share` | Click en botón de compartir | Cada vez que alguien comparte el dashboard |

---

## Recomendaciones de Implementación

✅ **Usar IDs anónimos por usuario** → No guardas emails para tracking individual

✅ **Marcar variantes de landing y simulador** → Para medir impacto por copy

✅ **Separar tráfico orgánico de ads** → Comparar CTR y engagement según fuente

✅ **Medir tiempo en sección** → Especialmente para el simulador y dashboard

✅ **Eventos en stories** → Solo link click y poll; respeta privacidad

✅ **UTM parameters** → Trackea origen de cada ad (país, plataforma, variante)
