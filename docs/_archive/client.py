# integration/firecrawl/client.py

"""
Firecrawl Client Wrapper
Maneja autenticación, rate limiting, y retry logic.
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
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
        client = FirecrawlClient(api_key="fc-...")
        result = await client.scrape("https://ejemplo.com")
        
    Endpoints soportados:
        - /scrape: Scrapear una URL
        - /crawl: Crawl recursivo (no usado en Visual Editor)
        - /map: Mapear sitio (no usado en Visual Editor)
    """
    
    BASE_URL = "https://api.firecrawl.dev/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializar cliente.
        
        Args:
            api_key: API key de Firecrawl. Si no se provee,
                     se intentará obtener de settings.
        """
        # Importar settings aquí para evitar circular imports
        if api_key is None:
            try:
                from config.settings import settings
                api_key = getattr(settings, 'FIRECRAWL_API_KEY', None)
            except ImportError:
                pass
        
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Verificar si el cliente tiene API key configurada"""
        return bool(self.api_key)
    
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
        formats: Optional[List[str]] = None,
        wait_for: int = 0,
        include_screenshot: bool = False,
        mobile: bool = False,
        remove_base64_images: bool = True,
        proxy_type: str = "auto"
    ) -> ScrapeResult:
        """
        Scrape una URL con Firecrawl.
        
        Args:
            url: URL a scrapear
            formats: Lista de formatos deseados ["html", "markdown", "links", "screenshot"]
                    Default: ["html"]
            wait_for: Milisegundos adicionales de espera para JavaScript
            include_screenshot: Capturar screenshot de la página
            mobile: Emular dispositivo móvil
            remove_base64_images: Eliminar imágenes base64 del output (reduce tamaño)
            proxy_type: Tipo de proxy - "basic", "stealth" (5 créditos), o "auto"
        
        Returns:
            ScrapeResult con el contenido o error
            
        Example:
            result = await client.scrape(
                "https://tienda.com",
                formats=["html"],
                wait_for=1000
            )
            if result.success:
                print(result.html[:100])
        """
        if not self.is_configured:
            return ScrapeResult(
                success=False,
                error="Firecrawl API key not configured"
            )
        
        if formats is None:
            formats = ["html"]
        
        try:
            client = await self._get_client()
            
            payload = {
                "url": url,
                "formats": formats.copy(),
                "waitFor": wait_for,
                "mobile": mobile,
                "removeBase64Images": remove_base64_images,
                "timeout": 25000,  # 25s timeout interno
                "proxy": proxy_type
            }
            
            if include_screenshot and "screenshot" not in payload["formats"]:
                payload["formats"].append("screenshot")
            
            logger.debug(f"Firecrawl scrape: {url}")
            
            # Realizar request
            response = await client.post("/scrape", json=payload)
            
            return self._handle_response(response, url)
                
        except httpx.TimeoutException:
            logger.error(f"Firecrawl timeout for {url}")
            return ScrapeResult(success=False, error="Request timeout (30s)")
            
        except httpx.ConnectError as e:
            logger.error(f"Firecrawl connection error: {e}")
            return ScrapeResult(success=False, error="Could not connect to Firecrawl API")
            
        except Exception as e:
            logger.error(f"Firecrawl unexpected error: {e}", exc_info=True)
            return ScrapeResult(success=False, error=str(e))
    
    def _handle_response(self, response: httpx.Response, url: str) -> ScrapeResult:
        """Procesar respuesta de Firecrawl"""
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                result_data = data.get("data", {})
                return ScrapeResult(
                    success=True,
                    html=result_data.get("html"),
                    markdown=result_data.get("markdown"),
                    screenshot=result_data.get("screenshot"),
                    metadata=result_data.get("metadata"),
                    credits_used=data.get("creditsUsed", 1)
                )
            else:
                return ScrapeResult(
                    success=False,
                    error=data.get("error", "Unknown Firecrawl error")
                )
        
        elif response.status_code == 402:
            logger.warning("Firecrawl: No credits available")
            return ScrapeResult(
                success=False,
                error="No Firecrawl credits available. Please check your account."
            )
        
        elif response.status_code == 429:
            logger.warning("Firecrawl: Rate limit exceeded")
            return ScrapeResult(
                success=False,
                error="Rate limit exceeded. Please try again later."
            )
        
        elif response.status_code == 401:
            logger.error("Firecrawl: Invalid API key")
            return ScrapeResult(
                success=False,
                error="Invalid Firecrawl API key"
            )
        
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('error', response.text[:100])}"
            except:
                error_msg += f": {response.text[:100]}"
            
            logger.error(f"Firecrawl error for {url}: {error_msg}")
            return ScrapeResult(success=False, error=error_msg)
    
    async def check_credits(self) -> Optional[int]:
        """
        Verificar créditos disponibles.
        
        Returns:
            Número de créditos o None si error
        """
        if not self.is_configured:
            return None
            
        try:
            client = await self._get_client()
            response = await client.get("/credit-usage")
            
            if response.status_code == 200:
                data = response.json()
                return data.get("remaining", 0)
            return None
            
        except Exception as e:
            logger.error(f"Failed to check Firecrawl credits: {e}")
            return None
    
    async def close(self):
        """Cerrar cliente HTTP y liberar recursos"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
