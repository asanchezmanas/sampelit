# Guía de Integración

Este documento detalla cómo integrar Stitch AI (Samplit) en tu sitio web.

## 1. Integración Universal (HTML)

La forma más rápida de instalar Samplit es añadiendo el siguiente snippet en el `<head>` de tu sitio web. Esto cargará el script de rastreo de forma asíncrona y comenzará a ejecutar tus experimentos automáticamente.

```html
<!-- Stitch AI Code -->
<script src="https://cdn.samplit.com/t.js?token=TU_TOKEN_DE_INSTALACION" async></script>
<!-- End Stitch AI Code -->
```

> **Nota:** Reemplaza `TU_TOKEN_DE_INSTALACION` con el token único de tu proyecto, que puedes encontrar en el Dashboard bajo **Settings > Installation**.

---

## 2. Aplicaciones Single Page (React, Vue, Next.js)

Para aplicaciones modernas que no recargan la página completa, se recomienda cargar el script una vez y dejar que maneje los cambios de ruta.

### React / Next.js

Puedes usar un hook `useEffect` en tu componente root (`_app.js` o `layout.js`):

```javascript
import { useEffect } from 'react';

function MyApp({ Component, pageProps }) {
  useEffect(() => {
    // Cargar script de Stitch AI
    const script = document.createElement('script');
    script.src = "https://cdn.samplit.com/t.js?token=TU_TOKEN";
    script.async = true;
    document.head.appendChild(script);

    return () => {
      // Limpieza opcional (aunque generalmente quieres mantenerlo)
      // document.head.removeChild(script);
    };
  }, []);

  return <Component {...pageProps} />;
}
```

### Vue.js / Nuxt

En tu `App.vue` o layout principal:

```javascript
export default {
  mounted() {
    const script = document.createElement('script');
    script.src = "https://cdn.samplit.com/t.js?token=TU_TOKEN";
    script.async = true;
    document.head.appendChild(script);
  }
}
```

---

## 3. CMS y E-commerce

### WordPress

1. Instala un plugin como **WPCode** o **Insert Headers and Footers**.
2. Ve a la configuración del plugin.
3. En la sección **"Scripts in Header"**, pega el snippet universal HTML.
4. Guarda los cambios.

### Shopify

1. Ve a **Online Store > Themes**.
2. Haz clic en **... > Edit code**.
3. Abre el archivo `theme.liquid`.
4. Pega el snippet universal justo antes de la etiqueta de cierre `</head>`.
5. Guarda el archivo.

### Webflow

1. Ve a **Project Settings**.
2. Pestaña **Custom Code**.
3. En la sección **Head Code**, pega el snippet.
4. Publica tu sitio.

---

## 4. Verificación

Para confirmar que la instalación es correcta:

1. Abre tu sitio web en una nueva pestaña.
2. Abre las herramientas de desarrollador (F12) y ve a la **Consola**.
3. Escribe `window.samplit.isReady()`. Debería devolver `true`.
4. También puedes buscar mensajes con el prefijo `[Samplit]` si el modo debug está activo.

## API del Cliente

Una vez cargado, puedes interactuar con Samplit mediante `window.samplit`:

- `window.samplit.getUserId()`: Obtiene el ID anónimo del usuario actual.
- `window.samplit.convert(experimentId)`: Fuerza una conversión manual.
- `window.samplit.refresh()`: Re-checkea experimentos (útil para cambios de ruta en SPAs).
