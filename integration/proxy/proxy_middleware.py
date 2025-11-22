# integration/proxy/proxy_middleware.py

"""
Proxy Middleware - Intercepta HTML e inyecta tracker

✅ FIXED:
- Class name corrected to ProxyMiddleware
- Proper session cleanup
- Connection pooling
- Error handling

Este middleware permite que el servidor del usuario haga proxy
a través de nosotros, interceptando el HTML para inyectar
el código de tracking automáticamente.
"""

import aiohttp
import logging
from typing import Optional
from bs4 import BeautifulSoup
import asyncio

logger = logging.getLogger(__name__)

class ProxyMiddleware:
    """
    ✅ FIXED: Class name changed from MABProxyMiddleware to ProxyMiddleware
    
    Proxy middleware para inyección automática de tracker
    """
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session with connection pooling
        
        ✅ FIXED: Proper session management with lock
        """
        async with self._session_lock:
            if self.session is None or self.session.closed:
                # Connection pooling for performance
                connector = aiohttp.TCPConnector(
                    limit=100,  # Max 100 connections
                    limit_per_host=30,  # Max 30 per host
                    ttl_dns_cache=300,  # DNS cache 5 min
                    keepalive_timeout=30
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=30,
                    connect=5,
                    sock_connect=5,
                    sock_read=10
                )
                
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                )
                
                logger.info("✅ Proxy session created")
            
            return self.session
    
    async def process_request(self, request, installation_token: str, original_url: str):
        """
        Process proxied request
        
        1. Fetch original page
        2. Inject tracker if HTML
        3. Return modified response
        """
        
        try:
            session = await self._get_session()
            
            # Forward headers (exclude Host)
            forward_headers = {
                key: value for key, value in request.headers.items()
                if key.lower() not in ['host', 'connection', 'accept-encoding']
            }
            
            # Make request to original site
            async with session.get(
                original_url,
                headers=forward_headers,
                allow_redirects=False
            ) as response:
                
                content_type = response.headers.get('Content-Type', '')
                
                # Only process HTML
                if 'text/html' in content_type:
                    html_content = await response.text()
                    
                    # Inject tracker
                    modified_html = self.inject_tracker(html_content, installation_token)
                    
                    # Build response
                    from fastapi.responses import HTMLResponse
                    return HTMLResponse(
                        content=modified_html,
                        status_code=response.status,
                        headers={
                            key: value for key, value in response.headers.items()
                            if key.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']
                        }
                    )
                else:
                    # Pass through non-HTML content
                    content = await response.read()
                    
                    from fastapi.responses import Response
                    return Response(
                        content=content,
                        status_code=response.status,
                        headers=dict(response.headers),
                        media_type=content_type
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Proxy request failed: {e}")
            from fastapi import HTTPException
            raise HTTPException(status_code=502, detail="Failed to fetch original page")
        
        except asyncio.TimeoutError:
            logger.error(f"Proxy request timeout: {original_url}")
            from fastapi import HTTPException
            raise HTTPException(status_code=504, detail="Gateway timeout")
        
        except Exception as e:
            logger.error(f"Unexpected proxy error: {e}", exc_info=True)
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="Proxy error")
    
    def inject_tracker(self, html: str, installation_token: str) -> str:
        """
        Inject tracker code into HTML
        
        Inserts script tag just before </head>
        """
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find </head>
            head = soup.find('head')
            
            if not head:
                # No head tag, create one
                head = soup.new_tag('head')
                if soup.html:
                    soup.html.insert(0, head)
                else:
                    return html  # Can't inject
            
            # Create tracker script
            tracker_script = soup.new_tag('script')
            tracker_script.string = f"""
(function() {{
    window.SAMPLIT_CONFIG = {{
        installationToken: '{installation_token}',
        apiEndpoint: '{self.api_url}/api/v1/tracker'
    }};
    
    var script = document.createElement('script');
    script.src = '{self.api_url}/static/tracker/tracker.js';
    script.async = true;
    document.head.appendChild(script);
}})();
            """
            
            # Insert before </head>
            head.append(tracker_script)
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Failed to inject tracker: {e}")
            return html  # Return original if injection fails
    
    async def close(self):
        """
        ✅ FIXED: Proper session cleanup
        
        This should be called during app shutdown
        """
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("✅ Proxy session closed")
            
            # Wait a bit for connections to close
            await asyncio.sleep(0.25)
