# ❓ FAQ Y AYUDA - INSTALACIÓN DE SAMPLIT

Textos para la sección de ayuda, FAQ, tooltips y mensajes del sistema.

---

## 📚 FAQ - SECCIÓN DE AYUDA GENERAL

### Categoría: Instalación

#### P: ¿Cuánto tarda la instalación?

**R:** La instalación toma aproximadamente **5 minutos**. Solo necesitas copiar una línea de código y pegarla en tu sitio web. No requiere conocimientos técnicos avanzados.

---

#### P: ¿Necesito saber programar para instalar Samplit?

**R:** No. La instalación es tan simple como copiar y pegar. Si puedes editar el HTML de tu sitio (o tienes acceso a tu CMS), puedes instalar Samplit.

Si no te sientes cómodo haciéndolo tú mismo, puedes enviar nuestra guía a tu desarrollador o webmaster.

---

#### P: ¿Afecta Samplit la velocidad de mi sitio?

**R:** No. Samplit está diseñado para tener **cero impacto** en la velocidad:

- Script ligero (~15KB minificado)
- Carga asíncrona (no bloquea el render)
- CDN global para máxima velocidad
- Optimizado para performance

De hecho, muchos clientes reportan que sus sitios se vuelven más rápidos después de usar Samplit gracias a las optimizaciones que descubren.

---

#### P: ¿Es compatible con mi plataforma?

**R:** Samplit funciona con **todas las plataformas web**:

✅ WordPress  
✅ Shopify  
✅ Wix  
✅ Squarespace  
✅ Webflow  
✅ HTML/CSS/JavaScript  
✅ React, Vue, Angular  
✅ Next.js, Nuxt, Gatsby  
✅ Cualquier CMS o framework  

Si tu sitio carga en un navegador, Samplit funciona.

---

#### P: ¿Puedo instalar Samplit yo mismo o necesito un desarrollador?

**R:** Depende de tu nivel técnico:

**Puedes hacerlo tú mismo si:**
- Tienes acceso al HTML de tu sitio
- Sabes cómo editar archivos o usar tu CMS
- Te sientes cómodo siguiendo instrucciones paso a paso

**Necesitas un desarrollador si:**
- No tienes acceso al código de tu sitio
- Tu empresa tiene políticas estrictas sobre cambios en código
- Prefieres que un profesional lo haga

En ambos casos, proporcionamos guías detalladas.

---

#### P: ¿Qué pasa si me equivoco al instalar?

**R:** No te preocupes, es muy difícil romper algo:

- El código es una sola línea de JavaScript
- No modifica tu sitio permanentemente
- Si algo sale mal, simplemente elimina el código
- Siempre puedes pedir ayuda a nuestro soporte

**Consejo:** Haz una copia de seguridad antes de hacer cambios (buena práctica general).

---

#### P: ¿Tengo que instalar el código en todas las páginas?

**R:** Depende de tu plataforma:

**NO necesitas instalarlo en cada página si:**
- Usas WordPress, Shopify, u otro CMS
- Instalas en el template/header principal
- El código se aplicará automáticamente a todo el sitio

**SÍ necesitas instalarlo en cada página si:**
- Tienes un sitio HTML estático
- Cada página es un archivo .html separado

---

#### P: ¿Puedo usar Samplit con Google Analytics / otras herramientas?

**R:** ¡Absolutamente! Samplit es **100% compatible** con:

- Google Analytics (GA4 y Universal)
- Google Tag Manager
- Facebook Pixel
- Hotjar
- Mixpanel
- Segment
- Cualquier otra herramienta de analytics

De hecho, muchos clientes integran Samplit con sus herramientas existentes para obtener análisis más profundos.

---

#### P: ¿Afecta al SEO de mi sitio?

**R:** No, de ninguna manera. Samplit:

- No oculta contenido de los motores de búsqueda
- No usa técnicas de cloaking
- No duplica contenido
- Google puede rastrear todas las variantes

Los cambios que hagas con Samplit son transparentes para los buscadores.

---

#### P: ¿Qué pasa si cambio de tema o rediseño mi sitio?

**R:** Si cambias el tema/template de tu sitio:

1. Tendrás que **reinstalar el código** en el nuevo tema
2. Solo toma 5 minutos (misma línea de código)
3. Tu token sigue siendo el mismo
4. No pierdes datos ni experimentos

**Consejo:** En WordPress, usa un plugin para evitar perder el código al cambiar temas.

---

#### P: ¿Puedo instalar Samplit en múltiples sitios?

**R:** Sí, pero cada sitio necesita su propio código con un token único:

- Sitio 1: `token=inst_abc123`
- Sitio 2: `token=inst_def456`
- Sitio 3: `token=inst_ghi789`

Desde tu dashboard puedes gestionar todos tus sitios en un solo lugar.

---

#### P: ¿El código expira o tengo que renovarlo?

**R:** No. Una vez instalado, el código funciona **permanentemente**. No hay renovación, actualización ni mantenimiento. 

La única excepción es si tú mismo eliminas el código o cambias tu token desde el dashboard.

---

#### P: ¿Cómo sé si la instalación funcionó?

**R:** Hay varias formas de verificar:

**Método 1 (más rápido):**
1. Abre tu sitio
2. Presiona F12
3. Ve a "Console"
4. Busca: `[Samplit] Tracker initialized`

**Método 2 (automático):**
1. Dashboard de Samplit
2. Click en "Verificar instalación"
3. Espera 10-20 segundos

**Método 3 (manual):**
1. Ver código fuente de tu página (Ctrl+U)
2. Buscar: `cdn.samplit.com`

---

### Categoría: Problemas Técnicos

#### P: No veo el código funcionando, ¿qué hago?

**R:** Sigue estos pasos en orden:

1. **Refresca la página** con Ctrl+Shift+R (recarga forzada)
2. **Limpia la caché** del navegador
3. **Prueba en modo incógnito**
4. **Verifica** que el código esté en el `<head>`
5. **Comprueba** que el token sea correcto

Si nada funciona, contacta a soporte con:
- URL de tu sitio
- Plataforma que usas (WordPress, Shopify, etc.)
- Captura de la consola del navegador (F12)

---

#### P: Veo errores en la consola del navegador

**R:** Los errores más comunes:

**Error: "Failed to load t.js"**
- Problema de red o firewall
- Desactiva bloqueadores de ads temporalmente
- Verifica tu conexión a internet

**Error: "Token not found"**
- El token no está correctamente configurado
- Verifica que hayas copiado el token completo
- Asegúrate de que no haya espacios extra

**Error: "CORS blocked"**
- Raro, pero puede pasar con configuraciones especiales
- Contacta a soporte para resolverlo

---

#### P: El código aparece visible en mi página

**R:** Esto significa que el código no está en el lugar correcto:

**Problema:** El código está fuera del `<head>` o dentro del `<body>`

**Solución:**
1. Encuentra la etiqueta `<head>` en tu HTML
2. Pega el código **dentro** del head
3. Debe estar **antes** de `</head>`
4. Guarda y verifica nuevamente

---

#### P: Los cambios no se reflejan en mi sitio

**R:** Probablemente es un problema de caché:

**Caché del navegador:**
- Ctrl+Shift+R (Windows) o Cmd+Shift+R (Mac)
- Prueba en modo incógnito

**Caché del sitio:**
- WordPress: Limpia caché de plugin (WP Rocket, W3 Total Cache)
- Shopify: Espera 5-10 minutos para propagación
- CDN: Limpia caché de Cloudflare u otro CDN

**No guardaste los cambios:**
- Verifica que hayas clickeado "Guardar" o "Publicar"

---

#### P: Mi sitio va más lento después de instalar Samplit

**R:** Esto es **extremadamente raro** porque:

- Script optimizado y ligero
- Carga asíncrona (no bloquea)
- CDN global ultra-rápido

**Posibles causas:**

1. **Coincidencia:** Otro factor ralentizó tu sitio al mismo tiempo
2. **Caché no activa:** Activa caché en tu sitio
3. **Error en instalación:** Verifica que uses `async` en el script

**Diagnóstico:**
- Usa PageSpeed Insights antes y después
- Desactiva temporalmente Samplit y compara
- Contacta a soporte con los resultados

---

### Categoría: Seguridad y Privacidad

#### P: ¿Es seguro Samplit?

**R:** Sí, completamente:

✅ **Conexión cifrada:** HTTPS/SSL siempre  
✅ **Sin datos personales:** No recopilamos emails, nombres, etc.  
✅ **Cumple GDPR:** Compatible con regulaciones europeas  
✅ **Sin vulnerabilidades:** Código auditado regularmente  
✅ **Empresa confiable:** Miles de sitios nos confían  

---

#### P: ¿Qué datos recopila Samplit?

**R:** Samplit recopila **solo lo necesario** para los A/B tests:

✅ **Lo que SÍ recopilamos:**
- URL de la página visitada
- Variante asignada al usuario
- Si el usuario convirtió (evento de conversión)
- ID de usuario anónimo (generado en tu navegador)
- Metadatos técnicos (navegador, resolución)

❌ **Lo que NO recopilamos:**
- Nombres, emails, teléfonos
- Datos financieros
- Información personal identificable
- Contraseñas
- Conversaciones o inputs del usuario

---

#### P: ¿Es compatible con GDPR/LOPD?

**R:** Sí. Samplit no recopila información personal identificable (PII), por lo que cumple con GDPR.

**Recomendación opcional:**
Algunos clientes prefieren incluir Samplit en su banner de cookies por transparencia, aunque técnicamente no es obligatorio ya que no procesamos datos personales.

Puedes añadir un texto como:
```
"Usamos Samplit para optimizar tu experiencia en el sitio mediante pruebas A/B. No recopilamos datos personales."
```

---

#### P: ¿Puedo ver qué datos se envían?

**R:** ¡Por supuesto! Somos 100% transparentes:

1. Abre DevTools (F12)
2. Ve a la pestaña "Network"
3. Busca requests a `api.samplit.com`
4. Click en cualquier request
5. Ve la pestaña "Payload" para ver qué se envía

Todo el código es visible y auditable.

---

### Categoría: Plataformas Específicas

#### P: WordPress - ¿Necesito un plugin?

**R:** No es obligatorio, pero **sí recomendado**:

**Con plugin (recomendado):**
- Más fácil de instalar
- No se pierde al cambiar de tema
- Método más seguro para no técnicos
- Plugin recomendado: "Insert Headers and Footers"

**Sin plugin:**
- Editas directamente el archivo header.php
- Más rápido para desarrolladores
- Se pierde al actualizar el tema (usa child theme)

---

#### P: Shopify - ¿Afecta mis ventas mientras instalo?

**R:** No. El código es solo una línea y no afecta tu proceso de checkout ni ventas.

**Pasos seguros:**
1. Haz una copia del tema (Theme → Duplicate)
2. Edita la copia
3. Prueba que todo funcione
4. Publica la copia como tema activo

Total downtime: 0 minutos.

---

#### P: Wix - ¿Por qué necesito un plan de pago?

**R:** Las funciones de código personalizado en Wix solo están disponibles en planes Business o superiores. Esto es una limitación de Wix, no de Samplit.

**Alternativas si tienes plan gratuito:**
- Actualiza a plan Business
- Usa otro método si Wix lo permite en el futuro
- Contacta con Wix para más información

---

#### P: HTML estático - ¿Tengo que editar cada página?

**R:** Depende de tu setup:

**Si todas las páginas comparten un header.html:**
- Solo edita header.html una vez
- Se aplicará a todas las páginas

**Si cada página es independiente:**
- Sí, necesitas añadir el código a cada archivo .html
- O usa un sistema de templates/includes
- Considera migrar a un CMS para facilitar futuras actualizaciones

---

### Categoría: Soporte y Ayuda

#### P: ¿Cómo contacto al soporte?

**R:** Varias formas:

**Email:** soporte@samplit.com  
Respuesta en 24-48h

**Chat en vivo:** Desde tu dashboard  
Horario: Lun-Vie 9am-6pm CET

**Documentación:** docs.samplit.com  
Guías, videos y tutoriales

**Comunidad:** community.samplit.com  
Pregunta a otros usuarios

---

#### P: ¿Puedo hablar con un técnico?

**R:** Sí. Si tu problema requiere asistencia técnica avanzada:

1. Contacta por email con:
   - URL de tu sitio
   - Plataforma/framework que usas
   - Descripción del problema
   - Capturas de pantalla relevantes

2. Un técnico revisará tu caso

3. En casos complejos, podemos hacer una videollamada

---

#### P: ¿Ofrecen servicio de instalación?

**R:** Para clientes con planes Enterprise, sí. Nuestro equipo puede:

- Instalar el código por ti
- Configurar tus primeros experimentos
- Entrenar a tu equipo
- Optimización personalizada

Contacta a ventas@samplit.com para más información.

---

## 💬 TOOLTIPS - TEXTOS CORTOS

### Campo: URL del sitio

```
Incluye el protocolo (https://) y el dominio completo.
Ejemplo: https://misitio.com
```

### Campo: Nombre del sitio

```
Nombre descriptivo para identificar este sitio en tu dashboard.
Ejemplo: "Mi Tienda Online" o "Blog Corporativo"
```

### Botón: Copiar código

```
Copia el código de instalación al portapapeles.
Luego pégalo en el <head> de tu sitio.
```

### Botón: Verificar instalación

```
Comprobaremos automáticamente que el código esté
correctamente instalado en tu sitio.
Esto tarda 10-30 segundos.
```

### Botón: Descargar PDF

```
Descarga la guía completa de instalación en formato PDF.
Ideal para enviar a tu desarrollador.
```

### Sección: Token de instalación

```
🔐 Este token es único y privado para tu sitio.
No lo compartas públicamente.
```

### Sección: Instrucciones

```
Sigue estos pasos para instalar Samplit en tu sitio.
Si tienes dudas, consulta nuestra documentación
o contacta al soporte.
```

---

## 🚨 MENSAJES DE ERROR

### Error: Token inválido

```
❌ Token inválido

El token que proporcionaste no es válido o ha sido revocado.

¿Qué hacer?
• Verifica que copiaste el token completo
• Genera un nuevo código desde el dashboard
• Contacta a soporte si el problema persiste
```

### Error: Sitio no accesible

```
❌ No podemos acceder a tu sitio

No pudimos verificar la instalación porque tu sitio
no está accesible públicamente.

Posibles causas:
• El sitio está en localhost/desarrollo
• Hay restricciones de firewall
• El sitio está en mantenimiento
• URL incorrecta

¿Qué hacer?
• Verifica que la URL sea correcta
• Asegúrate de que el sitio esté online
• Puedes marcar como instalado manualmente
```

### Error: Código no detectado

```
⚠️ Código no detectado aún

No hemos encontrado el código de Samplit en tu sitio.

Esto puede ser porque:
• Los cambios no se han guardado/publicado
• El sitio tiene caché activa
• El código no está en el <head>

¿Qué hacer?
• Verifica que el código esté instalado correctamente
• Limpia la caché y espera 5 minutos
• Reintenta la verificación
• Consulta la guía de troubleshooting
```

### Error: Tiempo de espera agotado

```
⏱️ Tiempo de espera agotado

La verificación tardó demasiado.

Esto puede pasar si:
• El sitio tarda mucho en cargar
• Hay problemas de red
• El servidor está sobrecargado

¿Qué hacer?
• Intenta nuevamente en unos minutos
• Verifica manualmente usando la consola del navegador
• Contacta a soporte si persiste
```

---

## ✅ MENSAJES DE ÉXITO

### Éxito: Código generado

```
✅ Código generado correctamente

Tu código de instalación está listo.
Copia el código de abajo y pégalo en tu sitio.

Tiempo estimado: 5 minutos
```

### Éxito: Instalación verificada

```
🎉 ¡Instalación exitosa!

Hemos verificado que Samplit está correctamente
instalado en tu sitio.

Ya puedes empezar a crear experimentos y
optimizar tu sitio web.

🚀 Siguiente paso: Crear tu primer experimento
```

### Éxito: Código copiado

```
✓ Código copiado al portapapeles

Ahora pégalo en el <head> de tu sitio.
```

---

## ℹ️ MENSAJES INFORMATIVOS

### Info: Verificación en progreso

```
🔍 Verificando instalación...

Estamos comprobando que el código de Samplit
esté correctamente instalado en tu sitio.

Esto puede tardar entre 10 y 30 segundos.
Por favor, espera...
```

### Info: Primera instalación

```
👋 ¡Primera vez instalando Samplit!

No te preocupes, es muy simple.
Sigue las instrucciones paso a paso
y estarás listo en menos de 5 minutos.

¿Necesitas ayuda? Estamos aquí para ti.
```

### Info: Instalación manual

```
💡 Instalación manual

Has marcado este sitio como instalado manualmente.

Asegúrate de que el código esté correctamente
instalado para que los experimentos funcionen.

Puedes verificar en cualquier momento desde
la configuración del sitio.
```

---

## 📱 NOTIFICACIONES PUSH (si aplica)

### Notificación: Código generado

```
🔔 Código de instalación listo
Tu código para tusitio.com está listo.
Click para ver instrucciones →
```

### Notificación: Instalación verificada

```
🎉 ¡Sitio instalado correctamente!
tusitio.com está ahora conectado a Samplit.
Crea tu primer experimento →
```

### Notificación: Recordatorio

```
⏰ Recordatorio: Instalación pendiente
Generaste un código hace 24h pero aún no
lo hemos detectado en tu sitio.
¿Necesitas ayuda? →
```

---

## 📧 SUBJECT LINES (Emails)

```
✅ Tu código de Samplit está listo
👋 ¿Ya instalaste Samplit?
🎉 ¡Instalación verificada!
⚠️ Problema con la instalación de Samplit
💡 Tips para instalar Samplit más rápido
🚀 Siguiente paso: Crea tu primer experimento
```

---

## 🎯 CALL-TO-ACTIONS

### Botones principales

```
Generar código de instalación →
Ya instalé el código →
Crear mi primer experimento →
Ver guía completa
Contactar soporte
Reintentar verificación
```

### Botones secundarios

```
Descargar PDF
Enviar por email
Copiar código
Ver instrucciones
Marcar como instalado
Más información
```

---

Estos textos cubren todos los casos de uso para guiar a los usuarios durante la instalación. ¿Necesitas algún texto adicional o modificación?
