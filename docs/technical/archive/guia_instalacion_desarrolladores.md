# 📘 GUÍA DE INSTALACIÓN DE Sampelit
## Para Desarrolladores, Freelancers y Equipos Técnicos

**Versión:** 1.0  
**Última actualización:** Diciembre 2024  
**Tiempo estimado:** 5 minutos  
**Dificultad:** ⭐☆☆☆☆ Básico  

---

## 📋 Contenido

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Instrucciones Generales](#instrucciones-generales)
3. [Guías por Plataforma](#guías-por-plataforma)
4. [Verificación](#verificación)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)
7. [Soporte](#soporte)

---

## 🎯 Resumen Ejecutivo

### ¿Qué es Sampelit?

Sampelit es una plataforma de A/B testing que permite optimizar sitios web mediante pruebas automáticas. Esta guía te ayudará a instalar el código de tracking en cualquier sitio web.

### ¿Qué necesitas hacer?

Añadir **una línea de JavaScript** en el `<head>` de tu sitio web. Nada más.

### Código a instalar

```html
<script src="https://cdn.Sampelit.com/t.js?token=TU_TOKEN_AQUI" async></script>
```

⚠️ **Importante:** Reemplaza `TU_TOKEN_AQUI` con el token único proporcionado por el cliente.

### Ubicación

Dentro de la etiqueta `<head>`, preferiblemente al final (justo antes de `</head>`).

### Requisitos técnicos

- **Dependencias:** Ninguna
- **Compatibilidad:** Todos los navegadores modernos
- **Peso:** ~15KB minificado
- **Impacto en performance:** Cero (carga asíncrona)
- **Compatible con:** Todos los CMS y frameworks

---

## 📝 Instrucciones Generales

### Paso 1: Obtener el token

El cliente debe proporcionarte un token único que comienza con `inst_`. Ejemplo:

```
inst_abc123xyz456def789ghi
```

Este token es privado y único para cada sitio.

### Paso 2: Localizar el archivo correcto

Dependiendo de la plataforma, necesitarás editar:

| Plataforma | Archivo |
|------------|---------|
| WordPress | `header.php` o plugin |
| Shopify | `theme.liquid` |
| HTML estático | `index.html` y demás páginas |
| React | `public/index.html` |
| Next.js | `pages/_document.js` |
| Vue.js | `public/index.html` |
| Nuxt | `nuxt.config.js` |
| Angular | `src/index.html` |

### Paso 3: Añadir el código

Busca la etiqueta `<head>` y añade el script **antes de** `</head>`.

**ANTES:**
```html
<head>
  <meta charset="UTF-8">
  <title>Mi Sitio</title>
  <link rel="stylesheet" href="styles.css">
</head>
```

**DESPUÉS:**
```html
<head>
  <meta charset="UTF-8">
  <title>Mi Sitio</title>
  <link rel="stylesheet" href="styles.css">
  
  <!-- Sampelit A/B Testing -->
  <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
</head>
```

### Paso 4: Guardar y publicar

1. **Guarda** los cambios
2. **Publica/despliega** (si aplica)
3. **Limpia la caché** del sitio (si tiene)

### Paso 5: Verificar

Abre el sitio y verifica que el script se carga correctamente (ver sección [Verificación](#verificación)).

---

## 🏗️ Guías por Plataforma

### WordPress

#### Método 1: Plugin (Recomendado) ⭐

**Ventajas:**
- No requiere editar código
- Cambios no se pierden al actualizar el tema
- Más seguro para no técnicos

**Pasos:**

1. Instala el plugin gratuito **"Insert Headers and Footers"**:
   - Dashboard → Plugins → Añadir nuevo
   - Busca: "Insert Headers and Footers"
   - Instalar y Activar

2. Configura el plugin:
   - Settings → Insert Headers and Footers
   - Pega el código en la sección **"Scripts in Header"**
   - Click en "Save"

3. ✅ Listo

**Captura de ejemplo:**
```
[Settings] → [Insert Headers and Footers]

┌──────────────────────────────────────────┐
│ Scripts in Header                        │
│ ┌──────────────────────────────────────┐ │
│ │ <script src="https://cdn.Sampelit... │ │
│ │   async></script>                    │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ [Save Changes]                           │
└──────────────────────────────────────────┘
```

#### Método 2: Editar header.php

**Solo si el cliente necesita evitar plugins**

1. Apariencia → Editor de temas
2. Busca `header.php` en la lista de archivos
3. Encuentra `</head>`
4. Pega el código **antes** de `</head>`
5. Click en "Actualizar archivo"

⚠️ **Advertencia:** Los cambios se perderán al actualizar el tema. Recomendamos usar un child theme o el Método 1.

#### Método 3: functions.php

Añade este código en el archivo `functions.php` de tu tema:

```php
<?php
function Sampelit_tracking_code() {
    ?>
    <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
    <?php
}
add_action('wp_head', 'Sampelit_tracking_code');
?>
```

---

### Shopify

1. Desde el admin de Shopify:
   - **Tienda online** → **Temas**

2. En tu tema activo:
   - **Acciones** → **Editar código**

3. En la carpeta **"Layout"**:
   - Abre el archivo `theme.liquid`

4. Busca la etiqueta `</head>`

5. Pega el código **antes** de `</head>`:

```liquid
  <!-- Sampelit A/B Testing -->
  <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
</head>
```

6. **Guardar**

7. ✅ Listo

**Nota:** Aparecerá automáticamente en todas las páginas de la tienda.

---

### Wix

1. Desde el editor de Wix:
   - **Configuración** (⚙️) → **Custom Code**

2. Click en **"+ Add Custom Code"**

3. Configuración:
   - **Name:** "Sampelit Tracker"
   - **Code snippet:** Pega el código de Sampelit
   - **Add Code to:** Selecciona **"Head"**
   - **Load code on:** Selecciona **"All pages"**

4. Click en **"Apply"**

5. **Publicar** el sitio

6. ✅ Listo

---

### Squarespace

1. Ve a **Settings** → **Advanced** → **Code Injection**

2. En la sección **"Header"**, pega el código de Sampelit

3. **Save**

4. ✅ Listo

**Nota:** Requiere plan Business o superior.

---

### Webflow

1. Ve a **Project Settings** (⚙️) → **Custom Code**

2. En la sección **"Head Code"**, pega el código

3. **Save Changes**

4. **Publica** el sitio

5. ✅ Listo

---

### HTML Estático

Edita directamente tus archivos `.html`:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mi Sitio</title>
  
  <!-- Sampelit A/B Testing -->
  <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
</head>
<body>
  <!-- Tu contenido -->
</body>
</html>
```

**Importante:** Debes añadirlo en **todas** las páginas donde quieras hacer A/B testing.

---

### React (Create React App)

Edita `public/index.html`:

```html
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React App</title>
    
    <!-- Sampelit A/B Testing -->
    <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
```

---

### Next.js

Edita o crea `pages/_document.js`:

```javascript
import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="es">
      <Head>
        {/* Sampelit A/B Testing */}
        <script 
          src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" 
          async 
        />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}
```

**Importante:** No uses `next/script` para este código. Debe ir en el `<Head>` de `_document.js`.

---

### Vue.js (Vue CLI)

Edita `public/index.html`:

```html
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Vue App</title>
    
    <!-- Sampelit A/B Testing -->
    <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
  </head>
  <body>
    <div id="app"></div>
  </body>
</html>
```

---

### Nuxt.js

Edita `nuxt.config.js`:

```javascript
export default {
  head: {
    title: 'Mi App Nuxt',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' }
    ],
    script: [
      {
        src: 'https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456',
        async: true
      }
    ]
  }
}
```

---

### Angular

Edita `src/index.html`:

```html
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Angular App</title>
  <base href="/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  
  <!-- Sampelit A/B Testing -->
  <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
</head>
<body>
  <app-root></app-root>
</body>
</html>
```

---

### Google Tag Manager

Si el cliente prefiere gestionar todos los scripts desde GTM:

1. Crea una nueva etiqueta → **Custom HTML**

2. Pega el código:
   ```html
   <script src="https://cdn.Sampelit.com/t.js?token=inst_abc123xyz456" async></script>
   ```

3. Configuración de activación:
   - **Tipo:** Page View
   - **Se activa en:** All Pages

4. **Guardar** y **Publicar**

⚠️ **Nota:** Esto retrasará ligeramente la carga del tracker. Preferible instalarlo directamente en el HTML si es posible.

---

## 🔍 Verificación

### Método 1: Consola del navegador (Recomendado)

**Pasos:**

1. Abre el sitio en Chrome, Firefox o Edge
2. Presiona **F12** para abrir las DevTools
3. Ve a la pestaña **"Console"**
4. Busca este mensaje:

```
[Sampelit] Tracker initialized
[Sampelit] Version: 2.0.0
[Sampelit] Token: inst_abc...
```

5. **Si lo ves** → ✅ TODO CORRECTO

**Captura de ejemplo:**
```
Console
──────────────────────────────────────
▼ [Sampelit] Tracker initialized
  [Sampelit] Version: 2.0.0
  [Sampelit] Token: inst_abc123...
  [Sampelit] Found 0 active experiments
──────────────────────────────────────
```

---

### Método 2: Inspeccionar código fuente

1. Abre el sitio
2. Click derecho → **"Ver código fuente"** (o Ctrl+U)
3. Busca (Ctrl+F): `cdn.Sampelit.com`
4. **Si aparece** → ✅ Código instalado

---

### Método 3: Network Tab

1. Abre DevTools (F12)
2. Ve a la pestaña **"Network"**
3. Recarga la página (Ctrl+R)
4. Busca `t.js` en la lista de requests
5. **Status debe ser 200** → ✅ Script cargando correctamente

**Captura de ejemplo:**
```
Network
──────────────────────────────────────────────────
Name          Status  Type        Size    Time
──────────────────────────────────────────────────
t.js          200     script      15.2KB  45ms  ← Busca esto
──────────────────────────────────────────────────
```

---

### Método 4: Verificación automática desde Sampelit

El cliente puede verificar desde su dashboard:

1. Dashboard de Sampelit → Sitios
2. Click en "Verificar instalación"
3. Espera 10-30 segundos
4. **Si detecta el código** → ✅ TODO CORRECTO

---

## ⚠️ Troubleshooting

### Problema 1: No veo el mensaje en la consola

**Posibles causas:**

1. **El código no está instalado correctamente**
   - Verifica que esté dentro de `<head></head>`
   - Verifica que no falten caracteres (< o >)
   - Reemplazaste el token correcto?

2. **La caché está activa**
   - Haz un hard refresh: Ctrl+Shift+R (o Cmd+Shift+R en Mac)
   - Limpia la caché del navegador
   - Prueba en modo incógnito

3. **Hay errores de sintaxis**
   - Mira la consola en busca de errores en rojo
   - Verifica que no rompiste el HTML

**Solución:**
```
1. Ctrl+Shift+R para forzar recarga
2. F12 → Console → buscar errores
3. Verifica el código en el HTML fuente
```

---

### Problema 2: Error "Failed to fetch"

**Posibles causas:**

1. Problema de conectividad
2. Firewall bloqueando `cdn.Sampelit.com`
3. Bloqueador de ads

**Solución:**
```
1. Verifica la conexión a internet
2. Desactiva temporalmente bloqueadores de ads
3. Comprueba firewall/antivirus
4. Prueba desde otra red
```

---

### Problema 3: El código aparece visible en la página

**Causa:** El código está fuera del `<head>` o hay un error de sintaxis.

**Solución:**
```
1. Verifica que esté dentro de <head></head>
2. Verifica que comience con <script y termine con </script>
3. Copia el código original nuevamente
```

---

### Problema 4: WordPress no permite editar archivos

**Causa:** Permisos restringidos o configuración de seguridad.

**Solución:**
```
1. Usa el plugin "Insert Headers and Footers" (Método 1)
2. O contacta con el hosting para editar wp-config.php
3. O usa un child theme
```

---

### Problema 5: Los cambios no se ven

**Posibles causas:**

1. Caché del sitio
2. Caché del navegador
3. CDN cache
4. Cambios no publicados

**Solución:**
```
1. Limpia la caché del plugin de caché (WP Rocket, W3 Total Cache, etc.)
2. Limpia la caché del navegador
3. Prueba en modo incógnito
4. Espera 5-10 minutos (propagación de CDN)
5. Verifica que hayas guardado/publicado los cambios
```

---

### Problema 6: Afecta la velocidad del sitio

**Respuesta:**

No debería afectar. El script:
- Es ligero (~15KB minificado)
- Usa `async` (no bloquea el render)
- Se carga de forma asíncrona

Si notas problemas de velocidad:
1. Usa herramientas como PageSpeed Insights
2. Verifica que el `async` esté presente
3. Contacta al soporte de Sampelit

---

## ❓ Preguntas Frecuentes

### ¿Afecta al SEO del sitio?

**No.** El código es JavaScript del lado del cliente. Los bots de Google pueden rastrear el contenido sin problemas.

### ¿Ralentiza el sitio?

**No.** El script es ligero (15KB) y se carga de forma asíncrona (`async`), por lo que no bloquea el render de la página.

### ¿Funciona en todos los navegadores?

**Sí.** Compatible con:
- Chrome/Edge (últimas versiones)
- Firefox (últimas versiones)
- Safari (últimas versiones)
- Navegadores modernos en general

### ¿Necesito instalarlo en todas las páginas?

Si instalas en el `<head>` del template principal (header.php en WordPress, theme.liquid en Shopify, etc.), **se aplicará automáticamente a todas las páginas**.

Para HTML estático, sí necesitas añadirlo en cada archivo `.html`.

### ¿Qué pasa si cambio de tema/template?

Tendrás que **reinstalar el código** en el nuevo tema. Por eso recomendamos:
- WordPress: Usar plugin (no se pierde al cambiar tema)
- Shopify: Reinstalar en el nuevo theme.liquid
- Otros CMS: Reinstalar según el nuevo template

### ¿Puedo tener múltiples sitios?

**No** con el mismo token. Cada sitio necesita su propio token único. El cliente debe generar un código diferente para cada sitio desde su dashboard.

### ¿El código expira?

**No.** El token es permanente mientras el cliente no lo elimine o regenere.

### ¿Es compatible con otros trackers?

**Sí.** Es 100% compatible con:
- Google Analytics
- Google Tag Manager
- Facebook Pixel
- Hotjar
- Mixpanel
- Cualquier otro tracker

### ¿Qué datos recopila?

Sampelit recopila únicamente:
- URL de la página visitada
- Variante asignada al usuario
- Eventos de conversión
- ID de usuario anónimo (generado localmente)
- ID de sesión

**No recopila** datos personales identificables (nombre, email, etc.).

### ¿Es compatible con GDPR/LOPD?

**Sí.** No recopila datos personales identificables. De todas formas, el cliente puede incluir Sampelit en su banner de cookies si lo desea.

---

## 📞 Soporte

Si tienes problemas con la instalación:

### Email
**soporte@Sampelit.com**  
Tiempo de respuesta: 24-48 horas

### Documentación
**https://docs.Sampelit.com**  
Guías detalladas y tutoriales en video

### Chat en vivo
Disponible desde el dashboard del cliente

---

## ✅ Checklist de Instalación

Usa este checklist para asegurarte de que todo está correcto:

```
□ Token obtenido del cliente
□ Token reemplazado en el código (inst_...)
□ Código añadido en el <head>
□ Código colocado ANTES de </head>
□ Atributo async presente
□ Cambios guardados
□ Cambios publicados/desplegados
□ Caché limpiada
□ Mensaje en consola verificado
□ Request a t.js verificado (Network tab)
□ Cliente notificado de instalación completa
```

---

## 📄 Información de Contacto

**Sitio web:** https://Sampelit.com  
**Documentación:** https://docs.Sampelit.com  
**Soporte:** soporte@Sampelit.com  
**Estado del servicio:** https://status.Sampelit.com

---

**Documento generado por Sampelit**  
**Versión 1.0 - Diciembre 2024**

---

*Esta guía puede ser distribuida libremente a desarrolladores, freelancers y equipos técnicos que necesiten instalar Sampelit.*
