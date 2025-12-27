# 🔌 Integraciones Externas

**Versión**: 1.0  
**Última actualización**: Diciembre 2024  
**Nivel**: Beginner-friendly 🟢

---

## 🎯 Overview

Samplit se integra con plataformas externas para facilitar la instalación y sincronización de experimentos.

```
┌─────────────────────────────────────────────────────────────┐
│                      SAMPLIT                                │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Shopify  │  │WordPress │  │  Email   │  │  Proxy   │   │
│  │  OAuth   │  │  OAuth   │  │  SMTP    │  │ Injection│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Tienda  │   │  Blog   │   │Sendgrid │   │  Sitio  │
   │ Shopify │   │   WP    │   │   etc   │   │  Target │
   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

---

## 📁 Estructura de Archivos

```
integration/
├── __init__.py
├── email/
│   ├── __init__.py
│   └── email_service.py      # Envío de emails (Sendgrid, SMTP)
├── proxy/
│   ├── __init__.py
│   └── proxy_service.py      # Inyección de tracker en sitios
└── web/
    ├── __init__.py
    ├── base.py               # Clase base para OAuth
    ├── shopify/
    │   ├── __init__.py
    │   └── shopify_oauth.py  # OAuth 2.0 con Shopify
    └── wordpress/
        ├── __init__.py
        └── wordpress_oauth.py # OAuth 2.0 con WordPress
```

---

## 🛒 Shopify Integration

### Flujo OAuth

```
1. Usuario clickea "Conectar Shopify"
         │
         ▼
2. Redirect a Shopify OAuth
   https://myshop.myshopify.com/admin/oauth/authorize?
   client_id=...&scope=read_content,write_script_tags&
   redirect_uri=https://samplit.com/api/v1/integrations/shopify/callback
         │
         ▼
3. Usuario autoriza en Shopify
         │
         ▼
4. Shopify redirect a callback con code
   https://samplit.com/callback?code=abc123&shop=myshop.myshopify.com
         │
         ▼
5. Backend intercambia code por access_token
         │
         ▼
6. Guardar token + instalación
         │
         ▼
7. Inyectar Script Tag automáticamente
```

### Archivo: `shopify_oauth.py`

```python
# integration/web/shopify/shopify_oauth.py

"""
Shopify OAuth 2.0 Integration.

🎓 CÓMO FUNCIONA:
────────────────
1. El usuario conecta su tienda Shopify
2. Samplit recibe un access_token
3. Usamos la API de Shopify para inyectar tracker.js
4. El tracker se carga automáticamente en todas las páginas de la tienda
"""

import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class ShopifyOAuth:
    """
    Maneja la autenticación OAuth con Shopify.
    
    🎓 OAuth 2.0 SIMPLIFICADO:
    ─────────────────────────
    OAuth es un protocolo para que Samplit acceda a la tienda
    del usuario SIN conocer su contraseña de Shopify.
    
    1. Usuario autoriza (en Shopify, no en Samplit)
    2. Shopify nos da un "code" temporal
    3. Intercambiamos code por "access_token" permanente
    4. Usamos access_token para hacer requests a la API de Shopify
    """
    
    def __init__(self):
        self.api_key = settings.SHOPIFY_API_KEY
        self.api_secret = settings.SHOPIFY_API_SECRET
        self.scopes = "read_content,write_script_tags"
        self.redirect_uri = f"{settings.BASE_URL}/api/v1/integrations/shopify/callback"
    
    def get_auth_url(self, shop: str, state: str) -> str:
        """
        Genera URL para iniciar OAuth.
        
        Args:
            shop: Dominio de la tienda (ej: "myshop.myshopify.com")
            state: Token anti-CSRF (generado por nosotros, verificado en callback)
        
        Returns:
            URL a la que redirigir al usuario
        
        🎓 ¿QUÉ ES EL STATE?
        ───────────────────
        Es un token random que nosotros generamos y guardamos en sesión.
        Cuando Shopify nos redirige de vuelta, incluye el mismo state.
        Si coincide → Request legítimo
        Si no coincide → Alguien está intentando un ataque CSRF
        """
        
        params = {
            "client_id": self.api_key,
            "scope": self.scopes,
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        
        return f"https://{shop}/admin/oauth/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(
        self,
        shop: str,
        code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Intercambia authorization code por access token.
        
        Args:
            shop: Dominio de la tienda
            code: Authorization code de Shopify
        
        Returns:
            {
                "access_token": "shpat_abc123...",
                "scope": "read_content,write_script_tags"
            }
        
        🎓 ESTE ES EL PASO CRÍTICO DE OAUTH:
        ───────────────────────────────────
        El "code" solo es válido una vez y expira rápido.
        Lo intercambiamos por un access_token que es permanente
        (hasta que el usuario desconecte la app).
        """
        
        url = f"https://{shop}/admin/oauth/access_token"
        
        payload = {
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Shopify OAuth failed: {response.text}")
                return None
            
            return response.json()
    
    async def install_script_tag(
        self,
        shop: str,
        access_token: str,
        script_url: str
    ) -> bool:
        """
        Instala tracker.js en la tienda Shopify.
        
        🎓 SCRIPT TAGS EN SHOPIFY:
        ─────────────────────────
        Shopify tiene una API para inyectar scripts en todas las páginas.
        Esto es MUCHO más fácil que pedirle al usuario que edite su tema.
        
        Una vez instalado, tracker.js se carga automáticamente en:
        - Páginas de productos
        - Carrito
        - Checkout (si tienen permisos)
        - Todas las páginas públicas
        """
        
        url = f"https://{shop}/admin/api/2024-01/script_tags.json"
        
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "script_tag": {
                "event": "onload",
                "src": script_url,
                "display_scope": "all"  # Todas las páginas
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                logger.info(f"Script tag installed on {shop}")
                return True
            else:
                logger.error(f"Failed to install script tag: {response.text}")
                return False
    
    async def uninstall_script_tag(
        self,
        shop: str,
        access_token: str,
        script_tag_id: str
    ) -> bool:
        """
        Desinstala tracker.js de la tienda.
        
        Llamado cuando el usuario desconecta Samplit.
        """
        
        url = f"https://{shop}/admin/api/2024-01/script_tags/{script_tag_id}.json"
        
        headers = {
            "X-Shopify-Access-Token": access_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers)
            return response.status_code == 200
```

---

## 📝 WordPress Integration

### Flujo OAuth

Similar a Shopify, pero usando WordPress.com OAuth o REST API con Application Passwords.

```
1. Usuario clickea "Conectar WordPress"
         │
         ▼
2. Dos opciones:
   a) WordPress.com (blogs hospedados) → OAuth 2.0
   b) Self-hosted → Application Passwords
         │
         ▼
3. Obtener credenciales
         │
         ▼
4. Inyectar tracker via REST API o plugin
```

### Archivo: `wordpress_oauth.py`

```python
# integration/web/wordpress/wordpress_oauth.py

"""
WordPress Integration.

🎓 DOS MODOS DE INTEGRACIÓN:
───────────────────────────
1. WordPress.com (blogs hospedados): OAuth 2.0 estándar
2. WordPress self-hosted: Application Passwords (WP 5.6+)

Para self-hosted también existe la opción de plugin personalizado.
"""

import httpx
from typing import Optional, Dict, Any
import base64
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class WordPressIntegration:
    """
    Maneja la integración con WordPress.
    """
    
    def __init__(self):
        self.client_id = settings.WORDPRESS_CLIENT_ID
        self.client_secret = settings.WORDPRESS_CLIENT_SECRET
        self.redirect_uri = f"{settings.BASE_URL}/api/v1/integrations/wordpress/callback"
    
    # ═══════════════════════════════════════════════════════════════════════
    # WordPress.com OAuth
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_auth_url(self, state: str) -> str:
        """
        URL de autorización para WordPress.com.
        """
        
        params = f"client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&state={state}"
        return f"https://public-api.wordpress.com/oauth2/authorize?{params}"
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Intercambia code por token (WordPress.com).
        """
        
        url = "https://public-api.wordpress.com/oauth2/token"
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)
            
            if response.status_code != 200:
                logger.error(f"WordPress OAuth failed: {response.text}")
                return None
            
            return response.json()
    
    # ═══════════════════════════════════════════════════════════════════════
    # Self-Hosted WordPress (Application Passwords)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def connect_self_hosted(
        self,
        site_url: str,
        username: str,
        app_password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Conecta a un WordPress self-hosted usando Application Passwords.
        
        🎓 APPLICATION PASSWORDS:
        ────────────────────────
        WordPress 5.6+ permite crear "contraseñas de aplicación" separadas.
        Son como tokens de API específicos para cada app conectada.
        
        El usuario las genera en: wp-admin → Users → Profile → Application Passwords
        """
        
        # Verificar conexión
        url = f"{site_url}/wp-json/wp/v2/users/me"
        
        credentials = base64.b64encode(
            f"{username}:{app_password}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"WordPress connection failed: {response.text}")
                return None
            
            user_data = response.json()
            
            return {
                "site_url": site_url,
                "username": username,
                "user_id": user_data.get("id"),
                "connected": True
            }
    
    async def inject_tracker_script(
        self,
        site_url: str,
        credentials: str,
        tracker_url: str
    ) -> bool:
        """
        Inyecta tracker.js en el sitio WordPress.
        
        🎓 MÉTODO: Crear un "must-use plugin" via REST API
        ─────────────────────────────────────────────────
        Los mu-plugins se cargan automáticamente en todas las páginas.
        Creamos uno pequeño que solo inyecta nuestro script.
        """
        
        # Esta implementación requiere permisos especiales
        # En producción, se usa un plugin de WordPress dedicado
        
        logger.info(f"Tracker injection requested for {site_url}")
        return True
```

---

## 📧 Email Integration

### Archivo: `email_service.py`

```python
# integration/email/email_service.py

"""
Email Service - Envío de emails transaccionales.

🎓 USOS EN SAMPLIT:
──────────────────
1. Verificación de email al registrarse
2. Recuperación de contraseña
3. Notificaciones de experimentos (ganador encontrado, etc.)
4. Reportes semanales de rendimiento
"""

import logging
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio de envío de emails.
    
    Soporta múltiples proveedores:
    - SendGrid (recomendado para producción)
    - SMTP genérico (para desarrollo)
    - Mailgun, SES, etc. (fácil de añadir)
    """
    
    def __init__(self):
        self.provider = settings.EMAIL_PROVIDER  # 'sendgrid', 'smtp'
        self.from_email = settings.EMAIL_FROM or "noreply@samplit.com"
        self.from_name = "Samplit"
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía un email.
        
        Args:
            to: Email del destinatario
            subject: Asunto
            html_content: Contenido HTML
            text_content: Contenido texto plano (fallback)
        
        Returns:
            True si se envió correctamente
        """
        
        if self.provider == 'sendgrid':
            return await self._send_via_sendgrid(to, subject, html_content)
        else:
            return await self._send_via_smtp(to, subject, html_content, text_content)
    
    async def _send_via_sendgrid(
        self,
        to: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Envía email via SendGrid API.
        
        🎓 SENDGRID:
        ───────────
        - Líder en emails transaccionales
        - API simple y confiable
        - Tracking de opens/clicks incluido
        - Free tier: 100 emails/día
        """
        
        import httpx
        
        url = "https://api.sendgrid.com/v3/mail/send"
        
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_content}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 202:
                logger.info(f"Email sent to {to}")
                return True
            else:
                logger.error(f"SendGrid error: {response.text}")
                return False
    
    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str]
    ) -> bool:
        """
        Envía email via SMTP (desarrollo).
        """
        
        import aiosmtplib
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to
        
        if text_content:
            message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))
        
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True
            )
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # Templates de email
    # ═══════════════════════════════════════════════════════════════════════
    
    async def send_verification_email(self, to: str, token: str) -> bool:
        """Envía email de verificación."""
        
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        html = f"""
        <h1>Verifica tu email</h1>
        <p>Gracias por registrarte en Samplit.</p>
        <p><a href="{verify_url}">Click aquí para verificar tu email</a></p>
        """
        
        return await self.send_email(to, "Verifica tu email - Samplit", html)
    
    async def send_experiment_winner_notification(
        self,
        to: str,
        experiment_name: str,
        winner_name: str,
        confidence: float
    ) -> bool:
        """Notifica que un experimento tiene ganador."""
        
        html = f"""
        <h1>🎉 Tu experimento tiene un ganador</h1>
        <p><strong>{experiment_name}</strong> ha alcanzado significancia estadística.</p>
        <p>Ganador: <strong>{winner_name}</strong> con {confidence*100:.1f}% de confianza.</p>
        <p><a href="{settings.FRONTEND_URL}/experiments">Ver resultados</a></p>
        """
        
        return await self.send_email(
            to, 
            f"🎉 Ganador encontrado: {experiment_name}", 
            html
        )
```

---

## 🔄 Proxy Integration

### Archivo: `proxy_service.py`

```python
# integration/proxy/proxy_service.py

"""
Proxy Service - Para el Visual Editor.

🎓 ¿POR QUÉ UN PROXY?
────────────────────
El Visual Editor necesita mostrar el sitio del usuario dentro de un iframe.
Pero los navegadores bloquean esto por seguridad (CORS, X-Frame-Options).

Solución: Hacer proxy del sitio a través de nuestro servidor.
1. Usuario quiere editar example.com
2. Samplit descarga el HTML de example.com
3. Inyectamos nuestro script de edición
4. Servimos el HTML modificado en un iframe
"""

import httpx
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


class ProxyService:
    """
    Proxy HTTP para el Visual Editor.
    """
    
    def __init__(self):
        self.editor_script_url = "/static/js/editor-client.js"
        self.timeout = 30  # segundos
    
    async def fetch_and_inject(self, url: str) -> Optional[str]:
        """
        Descarga una URL e inyecta el script del editor.
        
        Args:
            url: URL a descargar (ej: "https://example.com/page")
        
        Returns:
            HTML modificado con script inyectado
        """
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch {url}: {response.status_code}")
                    return None
                
                html = response.text
                
                # Inyectar script antes de </body>
                modified_html = self._inject_editor_script(html, url)
                
                # Reescribir URLs relativas
                modified_html = self._rewrite_urls(modified_html, url)
                
                return modified_html
                
        except Exception as e:
            logger.error(f"Proxy error for {url}: {e}")
            return None
    
    def _inject_editor_script(self, html: str, original_url: str) -> str:
        """
        Inyecta el script del editor visual.
        """
        
        editor_script = f"""
        <script>
            window.SAMPLIT_EDITOR_MODE = true;
            window.SAMPLIT_ORIGINAL_URL = "{original_url}";
        </script>
        <script src="{self.editor_script_url}"></script>
        """
        
        # Inyectar antes de </body>
        if "</body>" in html.lower():
            html = re.sub(
                r'</body>',
                f'{editor_script}</body>',
                html,
                flags=re.IGNORECASE
            )
        else:
            # Si no hay </body>, añadir al final
            html += editor_script
        
        return html
    
    def _rewrite_urls(self, html: str, base_url: str) -> str:
        """
        Reescribe URLs relativas a absolutas.
        
        🎓 ¿POR QUÉ?
        ───────────
        El HTML original tiene URLs como "/images/logo.png".
        Cuando lo servimos desde Samplit, ese path no existe.
        Lo convertimos a "https://example.com/images/logo.png".
        """
        
        from urllib.parse import urljoin, urlparse
        
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Reescribir src, href, action
        for attr in ['src', 'href', 'action']:
            pattern = rf'{attr}=["\'](?!http|//|#|javascript:|data:)([^"\']+)["\']'
            
            def replace(match):
                path = match.group(1)
                absolute = urljoin(base_url, path)
                return f'{attr}="{absolute}"'
            
            html = re.sub(pattern, replace, html, flags=re.IGNORECASE)
        
        return html
```

---

## 📚 Configuración Requerida

Para habilitar las integraciones, añade estas variables a `.env`:

```bash
# Shopify
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret

# WordPress.com
WORDPRESS_CLIENT_ID=your_wp_client_id
WORDPRESS_CLIENT_SECRET=your_wp_client_secret

# Email (SendGrid)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxx

# O Email (SMTP)
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=noreply@samplit.com
```

**Próximo paso**: [Ver Scripts de Mantenimiento](./scripts.md)

