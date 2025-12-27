# tests/integration/test_firecrawl.py

"""
Tests para la integración de Firecrawl con Visual Editor.

Ejecutar:
    pytest tests/integration/test_firecrawl.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import httpx

# Imports del módulo (ajustar path según estructura real)
import sys
sys.path.insert(0, '/home/claude/sampelit-firecrawl')

from integration.firecrawl.client import FirecrawlClient, ScrapeResult
from integration.firecrawl.visual_proxy import FirecrawlVisualProxy, ProxyResult


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def firecrawl_client():
    """Cliente Firecrawl con API key de test"""
    return FirecrawlClient(api_key="fc-test-key-12345")


@pytest.fixture
def visual_proxy():
    """Proxy visual editor para testing"""
    return FirecrawlVisualProxy(firecrawl_api_key="fc-test-key-12345")


@pytest.fixture
def sample_html():
    """HTML de ejemplo para tests"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Hello World</h1>
        <button id="cta">Click me</button>
    </body>
    </html>
    """


@pytest.fixture
def firecrawl_success_response():
    """Respuesta exitosa de Firecrawl"""
    return {
        "success": True,
        "data": {
            "html": "<html><head></head><body><h1>Rendered Content</h1></body></html>",
            "metadata": {
                "title": "Test Page",
                "sourceURL": "https://example.com"
            }
        },
        "creditsUsed": 1
    }


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: FirecrawlClient
# ═══════════════════════════════════════════════════════════════════════════

class TestFirecrawlClient:
    """Tests para FirecrawlClient"""
    
    def test_is_configured_with_key(self, firecrawl_client):
        """Test que el cliente detecta cuando tiene API key"""
        assert firecrawl_client.is_configured is True
    
    def test_is_configured_without_key(self):
        """Test que el cliente detecta cuando NO tiene API key"""
        client = FirecrawlClient(api_key=None)
        assert client.is_configured is False
    
    @pytest.mark.asyncio
    async def test_scrape_without_api_key(self):
        """Test scrape sin API key retorna error"""
        client = FirecrawlClient(api_key=None)
        result = await client.scrape("https://example.com")
        
        assert result.success is False
        assert "not configured" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_success(self, firecrawl_client, firecrawl_success_response):
        """Test scrape exitoso"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = firecrawl_success_response
        
        with patch.object(firecrawl_client, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            result = await firecrawl_client.scrape("https://example.com")
        
        assert result.success is True
        assert result.html is not None
        assert "Rendered Content" in result.html
        assert result.credits_used == 1
    
    @pytest.mark.asyncio
    async def test_scrape_no_credits(self, firecrawl_client):
        """Test scrape cuando no hay créditos"""
        mock_response = MagicMock()
        mock_response.status_code = 402
        
        with patch.object(firecrawl_client, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            result = await firecrawl_client.scrape("https://example.com")
        
        assert result.success is False
        assert "credits" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_rate_limit(self, firecrawl_client):
        """Test scrape con rate limit"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch.object(firecrawl_client, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            result = await firecrawl_client.scrape("https://example.com")
        
        assert result.success is False
        assert "rate limit" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_invalid_api_key(self, firecrawl_client):
        """Test scrape con API key inválida"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch.object(firecrawl_client, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            result = await firecrawl_client.scrape("https://example.com")
        
        assert result.success is False
        assert "invalid" in result.error.lower() or "api key" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_timeout(self, firecrawl_client):
        """Test scrape con timeout"""
        with patch.object(firecrawl_client, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_get_client.return_value = mock_client
            
            result = await firecrawl_client.scrape("https://example.com")
        
        assert result.success is False
        assert "timeout" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: FirecrawlVisualProxy
# ═══════════════════════════════════════════════════════════════════════════

class TestFirecrawlVisualProxy:
    """Tests para FirecrawlVisualProxy"""
    
    def test_normalize_url_adds_https(self, visual_proxy):
        """Test que se añade https a URLs sin protocolo"""
        assert visual_proxy._normalize_url("example.com") == "https://example.com"
        assert visual_proxy._normalize_url("www.test.com") == "https://www.test.com"
    
    def test_normalize_url_preserves_http(self, visual_proxy):
        """Test que se preserva http si ya está presente"""
        assert visual_proxy._normalize_url("http://example.com") == "http://example.com"
        assert visual_proxy._normalize_url("https://example.com") == "https://example.com"
    
    def test_inject_editor_scripts_in_head(self, visual_proxy, sample_html):
        """Test inyección de scripts en <head>"""
        result = visual_proxy._inject_editor_scripts(sample_html, "https://example.com")
        
        assert "editor-client.js" in result
        assert "samplit-highlight" in result
        assert '<base href="https://example.com">' in result
        # Script debe estar después de <head>
        assert result.index("editor-client.js") > result.lower().index("<head>")
    
    def test_inject_editor_scripts_no_head(self, visual_proxy):
        """Test inyección de scripts cuando no hay <head>"""
        html = "<body><h1>Test</h1></body>"
        result = visual_proxy._inject_editor_scripts(html, "https://example.com")
        
        assert "editor-client.js" in result
        assert "samplit-highlight" in result
    
    def test_cache_set_and_get(self, visual_proxy, sample_html):
        """Test básico de cache"""
        url = "https://test-cache.com"
        
        # Inicialmente no hay cache
        assert visual_proxy._get_cached(url) is None
        
        # Guardar en cache
        visual_proxy._set_cache(url, sample_html)
        
        # Ahora debe existir
        cached = visual_proxy._get_cached(url)
        assert cached is not None
        assert "Hello World" in cached
    
    def test_cache_expiration(self, visual_proxy, sample_html):
        """Test que el cache expira correctamente"""
        url = "https://test-expiry.com"
        
        # Configurar TTL muy corto para test
        visual_proxy.cache_ttl = timedelta(milliseconds=1)
        
        visual_proxy._set_cache(url, sample_html)
        
        # Esperar a que expire
        import time
        time.sleep(0.01)
        
        # Debe haber expirado
        assert visual_proxy._get_cached(url) is None
    
    def test_clear_cache(self, visual_proxy, sample_html):
        """Test limpiar cache"""
        visual_proxy._set_cache("https://a.com", sample_html)
        visual_proxy._set_cache("https://b.com", sample_html)
        
        assert len(visual_proxy._cache) == 2
        
        visual_proxy.clear_cache()
        
        assert len(visual_proxy._cache) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_page_from_cache(self, visual_proxy, sample_html):
        """Test fetch desde cache"""
        url = "https://cached-page.com"
        
        # Pre-poblar cache
        visual_proxy._set_cache(url, sample_html)
        
        result = await visual_proxy.fetch_page(url, use_cache=True)
        
        assert result.success is True
        assert result.source == "cache"
        assert "Hello World" in result.html
    
    @pytest.mark.asyncio
    async def test_fetch_page_skip_cache(self, visual_proxy, sample_html, firecrawl_success_response):
        """Test fetch ignorando cache"""
        url = "https://skip-cache.com"
        
        # Pre-poblar cache
        visual_proxy._set_cache(url, sample_html)
        
        # Mock Firecrawl
        with patch.object(visual_proxy.firecrawl, 'scrape') as mock_scrape:
            mock_scrape.return_value = ScrapeResult(
                success=True,
                html="<html><body>Fresh content</body></html>",
                credits_used=1
            )
            
            result = await visual_proxy.fetch_page(url, use_cache=False)
        
        assert result.success is True
        assert result.source == "firecrawl"
        assert "Fresh content" in result.html
    
    @pytest.mark.asyncio
    async def test_fetch_page_firecrawl_success(self, visual_proxy, firecrawl_success_response):
        """Test fetch exitoso con Firecrawl"""
        url = "https://firecrawl-test.com"
        
        with patch.object(visual_proxy.firecrawl, 'scrape') as mock_scrape:
            mock_scrape.return_value = ScrapeResult(
                success=True,
                html="<html><head></head><body><h1>JS Rendered</h1></body></html>",
                credits_used=1,
                metadata={"title": "Test"}
            )
            
            result = await visual_proxy.fetch_page(url)
        
        assert result.success is True
        assert result.source == "firecrawl"
        assert "editor-client.js" in result.html
        assert result.metadata.get("credits_used") == 1
    
    @pytest.mark.asyncio
    async def test_fetch_page_fallback_on_firecrawl_failure(self, visual_proxy, sample_html):
        """Test fallback a httpx cuando Firecrawl falla"""
        url = "https://fallback-test.com"
        
        with patch.object(visual_proxy.firecrawl, 'scrape') as mock_scrape:
            mock_scrape.return_value = ScrapeResult(
                success=False,
                error="Firecrawl unavailable"
            )
            
            with patch.object(visual_proxy, '_fallback_fetch') as mock_fallback:
                mock_fallback.return_value = (True, sample_html)
                
                result = await visual_proxy.fetch_page(url)
        
        assert result.success is True
        assert result.source == "fallback"
        assert "editor-client.js" in result.html
    
    @pytest.mark.asyncio
    async def test_fetch_page_force_firecrawl_no_fallback(self, visual_proxy):
        """Test que force_firecrawl evita el fallback"""
        url = "https://no-fallback.com"
        
        with patch.object(visual_proxy.firecrawl, 'scrape') as mock_scrape:
            mock_scrape.return_value = ScrapeResult(
                success=False,
                error="Firecrawl error"
            )
            
            result = await visual_proxy.fetch_page(url, force_firecrawl=True)
        
        assert result.success is False
        assert result.source == "error"
    
    @pytest.mark.asyncio
    async def test_fetch_page_total_failure(self, visual_proxy):
        """Test cuando tanto Firecrawl como fallback fallan"""
        url = "https://total-failure.com"
        
        with patch.object(visual_proxy.firecrawl, 'scrape') as mock_scrape:
            mock_scrape.return_value = ScrapeResult(success=False, error="Firecrawl down")
            
            with patch.object(visual_proxy, '_fallback_fetch') as mock_fallback:
                mock_fallback.return_value = (False, "Connection refused")
                
                result = await visual_proxy.fetch_page(url)
        
        assert result.success is False
        assert result.source == "error"
        assert "Connection refused" in result.metadata.get("error", "")
    
    def test_error_page_generation(self, visual_proxy):
        """Test generación de página de error"""
        error_html = visual_proxy._error_page(
            "https://error-test.com",
            "Connection timeout"
        )
        
        assert "error-test.com" in error_html
        assert "Connection timeout" in error_html
        assert "Intentar de nuevo" in error_html


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Integration
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Tests de integración del módulo completo"""
    
    @pytest.mark.asyncio
    async def test_full_flow_with_cache(self, visual_proxy):
        """Test flujo completo: Firecrawl → Cache → Cache hit"""
        url = "https://full-flow.com"
        
        # Primera llamada: Firecrawl
        with patch.object(visual_proxy.firecrawl, 'scrape') as mock_scrape:
            mock_scrape.return_value = ScrapeResult(
                success=True,
                html="<html><body>Initial</body></html>",
                credits_used=1
            )
            
            result1 = await visual_proxy.fetch_page(url)
        
        assert result1.source == "firecrawl"
        
        # Segunda llamada: Debe venir del cache
        result2 = await visual_proxy.fetch_page(url)
        
        assert result2.source == "cache"
        assert "editor-client.js" in result2.html
    
    @pytest.mark.asyncio
    async def test_proxy_without_firecrawl_key(self):
        """Test proxy sin API key de Firecrawl usa solo fallback"""
        proxy = FirecrawlVisualProxy(firecrawl_api_key=None)
        
        with patch.object(proxy, '_fallback_fetch') as mock_fallback:
            mock_fallback.return_value = (True, "<html><body>Fallback</body></html>")
            
            result = await proxy.fetch_page("https://no-key.com")
        
        assert result.success is True
        assert result.source == "fallback"


# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
