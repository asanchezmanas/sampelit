# Integration Guide

This document details how to integrate Sampelit into your website.

## 1. Universal Integration (HTML)

The fastest way to install Sampelit is by adding the following snippet into the `<head>` of your website. This will load the tracking script asynchronously and start executing your experiments automatically.

```html
<!-- Sampelit Code -->
<script src="https://cdn.Sampelit.com/t.js?token=YOUR_INSTALLATION_TOKEN" async></script>
<!-- End Sampelit Code -->
```

> **Note:** Replace `YOUR_INSTALLATION_TOKEN` with your project's unique token, which can be found in the Dashboard under **Settings > Installation**.

---

## 2. Single Page Applications (React, Vue, Next.js)

For modern applications that do not perform full page reloads, it is recommended to load the script once and let it handle route changes.

### React / Next.js

You can use a `useEffect` hook in your root component (`_app.js` or `layout.js`):

```javascript
import { useEffect } from 'react';

function MyApp({ Component, pageProps }) {
  useEffect(() => {
    // Load Sampelit script
    const script = document.createElement('script');
    script.src = "https://cdn.Sampelit.com/t.js?token=YOUR_TOKEN";
    script.async = true;
    document.head.appendChild(script);

    return () => {
      // Optional cleanup (usually you want to keep it)
      // document.head.removeChild(script);
    };
  }, []);

  return <Component {...pageProps} />;
}
```

### Vue.js / Nuxt

In your `App.vue` or main layout:

```javascript
export default {
  mounted() {
    const script = document.createElement('script');
    script.src = "https://cdn.Sampelit.com/t.js?token=YOUR_TOKEN";
    script.async = true;
    document.head.appendChild(script);
  }
}
```

---

## 3. CMS and E-commerce

### WordPress

1. Install a plugin like **WPCode** or **Insert Headers and Footers**.
2. Go to the plugin settings.
3. In the **"Scripts in Header"** section, paste the universal HTML snippet.
4. Save the changes.

### Shopify

1. Go to **Online Store > Themes**.
2. Click **... > Edit code**.
3. Open the `theme.liquid` file.
4. Paste the universal snippet just before the closing `</head>` tag.
5. Save the file.

### Webflow

1. Go to **Project Settings**.
2. Tab **Custom Code**.
3. In the **Head Code** section, paste the snippet.
4. Publish your site.

---

## 4. Verification

To confirm the installation is correct:

1. Open your website in a new tab.
2. Open developer tools (F12) and go to the **Console**.
3. Type `window.Sampelit.isReady()`. It should return `true`.
4. You can also look for messages prefixed with `[Sampelit]` if debug mode is active.

## Client API

Once loaded, you can interact with Sampelit using `window.Sampelit`:

- `window.Sampelit.getUserId()`: Retrieves the current user's anonymous ID.
- `window.Sampelit.convert(experimentId)`: Forces a manual conversion.
- `window.Sampelit.refresh()`: Re-checks experiments (useful for route changes in SPAs).
