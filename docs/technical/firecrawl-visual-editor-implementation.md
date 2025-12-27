# Plan de Implementación: Firecrawl + Visual Editor

## Resumen Ejecutivo

Integrar Firecrawl como capa de proxy para el Visual Editor, permitiendo:
- Renderizado de JavaScript (SPAs, React, Vue)
- Bypass de anti-bot protection
- HTML limpio para inyección de scripts del editor
- Screenshots opcionales para preview

**Esfuerzo estimado:** 1 semana  
**Costo estimado:** €50-100/mes (uso moderado)

---

## 1. Análisis del Código Actual

### Problema Principal
El endpoint `/api/v1/visual-editor/proxy` usa `httpx` básico:

```python
# visual_editor.py (actual)
async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=15.0) as client:
    resp = await client.get(url)
```

**Limitaciones:**
- ❌ No ejecuta JavaScript → SPAs aparecen vacías
- ❌ Sin manejo de anti-bot → muchos sitios bloquean
- ❌ CORS problemático en algunos casos
- ❌ Contenido dinámico no capturado

### Flujo Actual
```
Usuario → URL → httpx.get() → HTML estático → Inyectar scripts → iframe
```

### Flujo con Firecrawl
```
Usuario → URL → Firecrawl /scrape → HTML renderizado → Inyectar scripts → iframe
```

---

## 2. Arquitectura Propuesta

### 2.1 Nueva Estructura de Archivos

```
integration/
├── firecrawl/
│   ├── __init__.py
│   ├── client.py          # Cliente Firecrawl wrapper
│   └── visual_proxy.py    # Proxy específico para Visual Editor
```

### 2.2 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    Visual Editor Frontend                    │
│  (visual-editor.html + visual-editor.js + editor-client.js) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              /api/v1/visual-editor/proxy                    │
│                    (visual_editor.py)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              FirecrawlVisualProxy                           │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  Cache Layer    │    │  Fallback httpx │                │
│  │  (Redis/Memory) │    │  (si FC falla)  │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Firecrawl API                             │
│            POST /v1/scrape + formats=["html"]               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Implementación Detallada

### 3.1 Cliente Firecrawl (`integration/firecrawl/client.py`)

```python
"""
Firecrawl Client Wrapper
Maneja autenticación, rate limiting, y retry logic.
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    """Resultado de scraping con Firecrawl"""
    success: bool
    html: Optional[str] = None
    markdown: Optional[str] = None
    screenshot: Optional[str] = None  # Base64
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    credits_used: int = 0


class FirecrawlClient:
    """
    Cliente async para Firecrawl API.
    
    Uso:
        client = FirecrawlClient()
        result = await client.scrape("https://ejemplo.com")
    """
    
    BASE_URL = "https://api.firecrawl.dev/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.FIRECRAWL_API_KEY
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy initialization del cliente HTTP"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def scrape(
        self,
        url: str,
        formats: list[str] = ["html"],
        wait_for: int = 0,
        include_screenshot: bool = False,
        mobile: bool = False,
        remove_base64_images: bool = True
    ) -> ScrapeResult:
        """
        Scrape una URL con Firecrawl.
        
        Args:
            url: URL a scrapear
            formats: ["html", "markdown", "links", "screenshot"]
            wait_for: ms adicionales de espera para JS
            include_screenshot: Capturar screenshot
            mobile: Emular dispositivo móvil
            remove_base64_images: Eliminar imágenes base64 del output
        
        Returns:
            ScrapeResult con el contenido
        """
        try:
            client = await self._get_client()
            
            payload = {
                "url": url,
                "formats": formats,
                "waitFor": wait_for,
                "mobile": mobile,
                "removeBase64Images": remove_base64_images,
                "timeout": 25000  # 25s timeout
            }
            
            if include_screenshot:
                payload["formats"].append("screenshot")
            
            # Realizar request
            response = await client.post("/scrape", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    return ScrapeResult(
                        success=True,
                        html=data.get("data", {}).get("html"),
                        markdown=data.get("data", {}).get("markdown"),
                        screenshot=data.get("data", {}).get("screenshot"),
                        metadata=data.get("data", {}).get("metadata"),
                        credits_used=data.get("creditsUsed", 1)
                    )
                else:
                    return ScrapeResult(
                        success=False,
                        error=data.get("error", "Unknown Firecrawl error")
                    )
            
            elif response.status_code == 402:
                logger.warning("Firecrawl: Sin créditos disponibles")
                return ScrapeResult(success=False, error="No credits available")
            
            elif response.status_code == 429:
                logger.warning("Firecrawl: Rate limit exceeded")
                return ScrapeResult(success=False, error="Rate limit exceeded")
            
            else:
                return ScrapeResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except httpx.TimeoutException:
            logger.error(f"Firecrawl timeout for {url}")
            return ScrapeResult(success=False, error="Request timeout")
            
        except Exception as e:
            logger.error(f"Firecrawl error: {e}")
            return ScrapeResult(success=False, error=str(e))
    
    async def close(self):
        """Cerrar cliente HTTP"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
```

### 3.2 Proxy Visual Editor (`integration/firecrawl/visual_proxy.py`)

```python
"""
Visual Editor Proxy con Firecrawl
Proxy inteligente con fallback y caching.
"""

import httpx
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta
import logging

from integration.firecrawl.client import FirecrawlClient, ScrapeResult
from config.settings import settings

logger = logging.getLogger(__name__)


class FirecrawlVisualProxy:
    """
    Proxy para Visual Editor con Firecrawl.
    
    Features:
    - Renderizado JS via Firecrawl
    - Cache en memoria (TTL 5 min)
    - Fallback a httpx si Firecrawl falla
    - Inyección automática de editor scripts
    """
    
    # Cache simple en memoria (en producción usar Redis)
    _cache: dict = {}
    CACHE_TTL = timedelta(minutes=5)
    
    def __init__(self):
        self.firecrawl = FirecrawlClient()
        self._httpx_client: Optional[httpx.AsyncClient] = None
    
    def _get_cache_key(self, url: str) -> str:
        """Generar key de cache"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cached(self, url: str) -> Optional[str]:
        """Obtener HTML del cache si existe y no expiró"""
        key = self._get_cache_key(url)
        if key in self._cache:
            html, timestamp = self._cache[key]
            if datetime.now() - timestamp < self.CACHE_TTL:
                logger.debug(f"Cache hit for {url[:50]}")
                return html
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, url: str, html: str):
        """Guardar HTML en cache"""
        key = self._get_cache_key(url)
        self._cache[key] = (html, datetime.now())
        
        # Limpieza básica si el cache crece mucho
        if len(self._cache) > 100:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Eliminar entradas expiradas"""
        now = datetime.now()
        expired = [
            k for k, (_, ts) in self._cache.items()
            if now - ts > self.CACHE_TTL
        ]
        for k in expired:
            del self._cache[k]
    
    async def _fallback_fetch(self, url: str) -> Tuple[bool, str]:
        """Fallback con httpx si Firecrawl no está disponible"""
        try:
            if self._httpx_client is None or self._httpx_client.is_closed:
                self._httpx_client = httpx.AsyncClient(
                    verify=False,
                    follow_redirects=True,
                    timeout=15.0
                )
            
            resp = await self._httpx_client.get(url)
            return True, resp.text
            
        except Exception as e:
            logger.error(f"Fallback fetch failed: {e}")
            return False, str(e)
    
    def _inject_editor_scripts(self, html: str, base_url: str) -> str:
        """
        Inyectar scripts del Visual Editor en el HTML.
        
        Args:
            html: HTML original
            base_url: URL base para resolver recursos relativos
        """
        injection = f'''
            <base href="{base_url}">
            <script src="/static/js/editor-client.js"></script>
            <style>
                .samplit-highlight {{ 
                    outline: 2px dashed #3b82f6 !important; 
                    cursor: pointer !important; 
                    transition: all 0.2s ease;
                    background: rgba(59, 130, 246, 0.1);
                }}
                .samplit-selected {{ 
                    outline: 2px solid #2563eb !important; 
                    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.2);
                    z-index: 99999;
                    position: relative;
                }}
            </style>
        '''
        
        # Inyectar en <head> o al final
        if "<head>" in html:
            html = html.replace("<head>", f"<head>{injection}", 1)
        elif "</body>" in html:
            html = html.replace("</body>", f"{injection}</body>", 1)
        else:
            html += injection
        
        return html
    
    async def fetch_page(
        self,
        url: str,
        use_cache: bool = True,
        force_firecrawl: bool = False
    ) -> Tuple[bool, str, dict]:
        """
        Obtener página renderizada para el Visual Editor.
        
        Args:
            url: URL a cargar
            use_cache: Usar cache si disponible
            force_firecrawl: Forzar uso de Firecrawl (no fallback)
        
        Returns:
            Tuple[success, html_or_error, metadata]
        """
        # Normalizar URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Verificar cache
        if use_cache:
            cached = self._get_cached(url)
            if cached:
                return True, cached, {"source": "cache"}
        
        # Intentar Firecrawl si hay API key configurada
        if settings.FIRECRAWL_API_KEY:
            result = await self.firecrawl.scrape(
                url=url,
                formats=["html"],
                wait_for=1000,  # Esperar 1s extra para JS
                remove_base64_images=True
            )
            
            if result.success and result.html:
                # Inyectar scripts
                html = self._inject_editor_scripts(result.html, url)
                
                # Guardar en cache
                if use_cache:
                    self._set_cache(url, html)
                
                logger.info(f"Firecrawl success: {url[:50]} ({result.credits_used} credits)")
                return True, html, {
                    "source": "firecrawl",
                    "credits_used": result.credits_used,
                    "metadata": result.metadata
                }
            
            elif not force_firecrawl:
                logger.warning(f"Firecrawl failed, trying fallback: {result.error}")
        
        # Fallback a httpx
        if not force_firecrawl:
            success, content = await self._fallback_fetch(url)
            if success:
                html = self._inject_editor_scripts(content, url)
                
                if use_cache:
                    self._set_cache(url, html)
                
                logger.info(f"Fallback success: {url[:50]}")
                return True, html, {"source": "fallback"}
            else:
                return False, content, {"source": "error"}
        
        return False, "No se pudo cargar la página", {"source": "error"}
    
    async def close(self):
        """Cerrar conexiones"""
        await self.firecrawl.close()
        if self._httpx_client and not self._httpx_client.is_closed:
            await self._httpx_client.aclose()


# Singleton para reusar conexiones
_proxy_instance: Optional[FirecrawlVisualProxy] = None

def get_visual_proxy() -> FirecrawlVisualProxy:
    """Obtener instancia singleton del proxy"""
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = FirecrawlVisualProxy()
    return _proxy_instance
```

### 3.3 Actualizar Router (`public_api/routers/visual_editor.py`)

```python
# Añadir al inicio del archivo
from integration.firecrawl.visual_proxy import get_visual_proxy

# Reemplazar el endpoint /proxy existente:

@router.get("/proxy", response_class=HTMLResponse)
async def visual_proxy(
    url: str = Query(..., description="Target URL to proxy"),
    user_id: str = Depends(get_current_user),
    force_js: bool = Query(False, description="Forzar renderizado JS con Firecrawl")
):
    """
    Proxies a target website with JavaScript rendering.
    Usa Firecrawl para renderizar SPAs y contenido dinámico.
    
    Args:
        url: URL a cargar
        force_js: Forzar Firecrawl aunque falle (no usar fallback)
    """
    proxy = get_visual_proxy()
    
    success, content, metadata = await proxy.fetch_page(
        url=url,
        use_cache=True,
        force_firecrawl=force_js
    )
    
    if success:
        return HTMLResponse(content=content)
    else:
        # Página de error amigable
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error de Carga</title>
            <style>
                body {{ 
                    font-family: Inter, sans-serif; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    height: 100vh; 
                    margin: 0;
                    background: #f3f4f6;
                }}
                .error-box {{
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 400px;
                }}
                h1 {{ color: #ef4444; margin-bottom: 1rem; }}
                p {{ color: #6b7280; }}
                code {{ 
                    background: #f3f4f6; 
                    padding: 0.25rem 0.5rem; 
                    border-radius: 4px;
                    font-size: 0.875rem;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>No se pudo cargar</h1>
                <p>La página <code>{url[:50]}...</code> no está disponible.</p>
                <p style="font-size: 0.875rem; margin-top: 1rem;">
                    Error: {content}
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=502)
```

### 3.4 Configuración (`config/settings.py`)

```python
# Añadir a la clase Settings:

class Settings(BaseSettings):
    # ... existentes ...
    
    # Firecrawl
    FIRECRAWL_API_KEY: Optional[str] = None
    FIRECRAWL_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
```

### 3.5 Variables de Entorno (`.env`)

```bash
# Firecrawl (Visual Editor JS rendering)
FIRECRAWL_API_KEY=fc-your-api-key-here
FIRECRAWL_ENABLED=true
```

---

## 4. Casos de Uso Mejorados

### 4.1 Antes vs Después

| Escenario | Antes (httpx) | Después (Firecrawl) |
|-----------|---------------|---------------------|
| Sitio estático (WordPress) | ✅ Funciona | ✅ Funciona |
| SPA React/Vue | ❌ HTML vacío | ✅ Contenido renderizado |
| Sitio con Cloudflare | ❌ Bloqueado | ✅ Bypass automático |
| Sitio con lazy loading | ❌ Sin contenido | ✅ Contenido cargado |
| E-commerce dinámico | ❌ Parcial | ✅ Productos visibles |

### 4.2 Flujo del Usuario

```
1. Usuario ingresa URL en Visual Editor
2. Frontend llama: GET /api/v1/visual-editor/proxy?url=https://tienda.com
3. Backend:
   a. Verifica cache → Si existe, retorna
   b. Llama Firecrawl con wait_for=1000ms
   c. Firecrawl renderiza JS, retorna HTML completo
   d. Backend inyecta editor-client.js
   e. Guarda en cache (5 min TTL)
   f. Retorna HTML al frontend
4. Frontend carga HTML en iframe
5. Usuario puede seleccionar elementos (incluso los generados por JS)
```

---

## 5. Manejo de Errores y Edge Cases

### 5.1 Matriz de Fallback

```
┌──────────────────────────────────────────────────────────┐
│                   Flujo de Decisión                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Cache existe?  ─── Sí ───► Retornar cache               │
│       │                                                  │
│       No                                                 │
│       ▼                                                  │
│  Firecrawl key?  ─── No ───► httpx fallback             │
│       │                                                  │
│       Sí                                                 │
│       ▼                                                  │
│  Firecrawl OK?  ─── No ───► httpx fallback              │
│       │                           │                      │
│       Sí                          ▼                      │
│       ▼                    httpx OK? ─── No ──► Error   │
│  Retornar HTML                    │                      │
│                                   Sí                     │
│                                   ▼                      │
│                            Retornar HTML                 │
│                            (sin JS render)               │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Errores Específicos

| Error | Causa | Acción |
|-------|-------|--------|
| `402 Payment Required` | Sin créditos Firecrawl | Fallback + alerta admin |
| `429 Rate Limit` | Demasiados requests | Fallback + exponential backoff |
| `Timeout` | Sitio muy lento | Fallback + mensaje usuario |
| `Blocked` | Anti-bot agresivo | Intentar con `proxy: "stealth"` |

---

## 6. Testing

### 6.1 Tests Unitarios

```python
# tests/integration/test_firecrawl_proxy.py

import pytest
from unittest.mock import AsyncMock, patch
from integration.firecrawl.client import FirecrawlClient, ScrapeResult
from integration.firecrawl.visual_proxy import FirecrawlVisualProxy


class TestFirecrawlClient:
    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test scrape exitoso"""
        client = FirecrawlClient(api_key="test-key")
        
        with patch.object(client, '_get_client') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {"html": "<html>Test</html>"},
                "creditsUsed": 1
            }
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.scrape("https://example.com")
            
            assert result.success
            assert result.html == "<html>Test</html>"
            assert result.credits_used == 1
    
    @pytest.mark.asyncio
    async def test_scrape_no_credits(self):
        """Test sin créditos disponibles"""
        client = FirecrawlClient(api_key="test-key")
        
        with patch.object(client, '_get_client') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 402
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.scrape("https://example.com")
            
            assert not result.success
            assert "credits" in result.error.lower()


class TestVisualProxy:
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache funciona"""
        proxy = FirecrawlVisualProxy()
        
        # Simular cache
        proxy._set_cache("https://test.com", "<html>Cached</html>")
        
        success, html, meta = await proxy.fetch_page("https://test.com")
        
        assert success
        assert meta["source"] == "cache"
    
    @pytest.mark.asyncio
    async def test_script_injection(self):
        """Test inyección de scripts"""
        proxy = FirecrawlVisualProxy()
        
        html = "<html><head></head><body>Test</body></html>"
        result = proxy._inject_editor_scripts(html, "https://test.com")
        
        assert "editor-client.js" in result
        assert "samplit-highlight" in result
        assert '<base href="https://test.com">' in result
```

### 6.2 Tests E2E

```python
# tests/e2e/test_visual_editor_firecrawl.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_visual_proxy_spa_site():
    """Test que Firecrawl renderiza SPAs correctamente"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # React SPA de ejemplo
        response = await client.get(
            "/api/v1/visual-editor/proxy",
            params={"url": "https://react.dev"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        assert "editor-client.js" in response.text
        # Verificar que el contenido fue renderizado
        assert "React" in response.text


@pytest.mark.asyncio
async def test_visual_proxy_fallback():
    """Test fallback cuando Firecrawl no disponible"""
    # Deshabilitar Firecrawl temporalmente
    # ...
    pass
```

---

## 7. Métricas y Monitoreo

### 7.1 Eventos a Trackear

```python
# orchestration/services/analytics_events.py

VISUAL_EDITOR_EVENTS = {
    "visual_editor.proxy.request": {
        "url": str,
        "source": str,  # "firecrawl" | "fallback" | "cache"
        "success": bool,
        "latency_ms": int,
        "credits_used": int
    },
    "visual_editor.proxy.error": {
        "url": str,
        "error_type": str,
        "error_message": str
    },
    "visual_editor.firecrawl.credits_low": {
        "remaining_credits": int
    }
}
```

### 7.2 Dashboard Sugerido

- Requests/día por source (Firecrawl vs Fallback vs Cache)
- Cache hit rate
- Créditos Firecrawl consumidos/día
- Errores por tipo
- Latencia p50/p95/p99

---

## 8. Costos Estimados

### 8.1 Pricing Firecrawl

| Plan | Créditos/mes | Precio | Costo/crédito |
|------|--------------|--------|---------------|
| Free | 500 | $0 | $0 |
| Hobby | 3,000 | $19 | $0.006 |
| Standard | 100,000 | $99 | $0.001 |

### 8.2 Estimación de Uso (Sampelit)

| Escenario | Requests/día | Créditos/mes | Costo estimado |
|-----------|--------------|--------------|----------------|
| Beta (10 usuarios) | 50 | 1,500 | €0 (Free tier) |
| Launch (50 usuarios) | 200 | 6,000 | €19-38 |
| Growth (200 usuarios) | 800 | 24,000 | €49-99 |

**Nota:** Con cache de 5 min, el uso real será 30-50% menor.

---

## 9. Timeline de Implementación

| Día | Tarea | Entregable |
|-----|-------|------------|
| 1 | Setup Firecrawl account + API key | Credenciales configuradas |
| 2 | Implementar `FirecrawlClient` | Cliente funcional |
| 3 | Implementar `FirecrawlVisualProxy` | Proxy con cache |
| 4 | Actualizar router + tests unitarios | Endpoint actualizado |
| 5 | Tests E2E + fix bugs | Tests pasando |
| 6 | Documentación + deploy staging | PR listo |
| 7 | QA + deploy producción | Feature live |

---

## 10. Checklist de Implementación

- [ ] Crear cuenta Firecrawl y obtener API key
- [ ] Crear `integration/firecrawl/__init__.py`
- [ ] Crear `integration/firecrawl/client.py`
- [ ] Crear `integration/firecrawl/visual_proxy.py`
- [ ] Actualizar `config/settings.py` con variables Firecrawl
- [ ] Actualizar `.env.example` con `FIRECRAWL_API_KEY`
- [ ] Actualizar `public_api/routers/visual_editor.py`
- [ ] Escribir tests unitarios
- [ ] Escribir tests E2E
- [ ] Probar con sitios SPA reales (React, Vue, Angular)
- [ ] Configurar alertas de créditos bajos
- [ ] Documentar en README
- [ ] Deploy a staging
- [ ] QA manual
- [ ] Deploy a producción

---

## 11. Preguntas Pendientes

1. **¿Redis para cache?** El cache en memoria es simple pero se pierde en restart. ¿Implementar Redis?

2. **¿Límite de uso por usuario?** ¿Máximo de requests de proxy por usuario/día?

3. **¿Screenshots?** Firecrawl puede capturar screenshots. ¿Útil para preview en el sidebar del editor?

4. **¿Stealth mode?** Para sitios con anti-bot agresivo, ¿usar `proxy: "stealth"` (5 créditos/request)?

---

*Documento creado: 2025-12-26*  
*Versión: 1.0*
