# public-api/routers/installations.py

"""
Sistema de Instalaciones
Gestiona WordPress plugins, proxies, snippets manuales, etc.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import hashlib

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager

router = APIRouter()

# ============================================
# MODELS
# ============================================

class InstallationMethod(str):
    WORDPRESS_PLUGIN = "wordpress_plugin"
    MANUAL_SNIPPET = "manual_snippet"
    PROXY_MIDDLEWARE = "proxy_middleware"
    SHOPIFY_APP = "shopify_app"
    CUSTOM_API = "custom_api"

class CreateInstallationRequest(BaseModel):
    site_url: HttpUrl
    site_name: Optional[str] = None
    platform: str  # wordpress, shopify, custom, etc
    installation_method: str

class InstallationResponse(BaseModel):
    installation_id: str
    site_url: str
    site_name: Optional[str]
    platform: str
    installation_method: str
    status: str
    installation_token: str
    api_token: str
    created_at: datetime
    
    # Instrucciones específicas según método
    instructions: Optional[Dict[str, Any]] = None
    tracking_code: Optional[str] = None

class InstallationListResponse(BaseModel):
    id: str
    site_url: str
    site_name: Optional[str]
    platform: str
    status: str
    active_experiments: int
    last_activity: Optional[datetime]
    created_at: datetime

# ============================================
# CREAR INSTALACIÓN
# ============================================

@router.post("/", response_model=InstallationResponse, status_code=status.HTTP_201_CREATED)
async def create_installation(
    request: CreateInstallationRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Registrar nueva instalación
    
    Genera tokens y devuelve instrucciones según el método elegido.
    """
    try:
        # Generar tokens únicos
        installation_token = f"inst_{uuid.uuid4().hex[:16]}"
        api_token = f"mab_{uuid.uuid4().hex[:32]}"
        
        # Crear instalación
        async with db.pool.acquire() as conn:
            installation_id = await conn.fetchval(
                """
                INSERT INTO platform_installations (
                    user_id, platform, installation_method, site_url, site_name,
                    installation_token, api_token, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
                RETURNING id
                """,
                user_id, request.platform, request.installation_method,
                str(request.site_url), request.site_name,
                installation_token, api_token
            )
            
            # Log
            await conn.execute(
                """
                INSERT INTO installation_logs (installation_id, event_type, message)
                VALUES ($1, 'created', 'Installation registered')
                """,
                installation_id
            )
        
        # Generar instrucciones según método
        instructions = None
        tracking_code = None
        
        if request.installation_method == InstallationMethod.MANUAL_SNIPPET:
            tracking_code = generate_tracking_snippet(installation_token)
            instructions = {
                "type": "manual",
                "steps": [
                    "Copy the tracking code below",
                    "Paste it in your website's <head> section",
                    "Save and publish your changes",
                    "Come back and click 'Verify Installation'"
                ]
            }
        
        elif request.installation_method == InstallationMethod.WORDPRESS_PLUGIN:
            instructions = {
                "type": "wordpress",
                "plugin_url": "https://wordpress.org/plugins/samplit-optimizer/",
                "steps": [
                    "Install 'Samplit Optimizer' plugin from WordPress.org",
                    "Activate the plugin",
                    "Go to Samplit menu in WordPress admin",
                    f"Enter your email and connect",
                    "Done! Your site is now optimizing automatically"
                ]
            }
        
        elif request.installation_method == InstallationMethod.PROXY_MIDDLEWARE:
            instructions = generate_proxy_instructions(
                str(request.site_url), 
                installation_token,
                request.platform
            )
        
        return InstallationResponse(
            installation_id=str(installation_id),
            site_url=str(request.site_url),
            site_name=request.site_name,
            platform=request.platform,
            installation_method=request.installation_method,
            status="pending",
            installation_token=installation_token,
            api_token=api_token,
            created_at=datetime.utcnow(),
            instructions=instructions,
            tracking_code=tracking_code
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create installation: {str(e)}"
        )

# ============================================
# LISTAR INSTALACIONES
# ============================================

@router.get("/", response_model=List[InstallationListResponse])
async def list_installations(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Listar todas las instalaciones del usuario"""
    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    pi.id, pi.site_url, pi.site_name, pi.platform, 
                    pi.status, pi.last_activity, pi.created_at,
                    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active') as active_experiments
                FROM platform_installations pi
                LEFT JOIN experiments e ON e.user_id = pi.user_id 
                    AND e.url LIKE pi.site_url || '%'
                WHERE pi.user_id = $1 AND pi.status != 'archived'
                GROUP BY pi.id
                ORDER BY pi.created_at DESC
                """,
                user_id
            )
        
        return [
            InstallationListResponse(
                id=str(row['id']),
                site_url=row['site_url'],
                site_name=row['site_name'],
                platform=row['platform'],
                status=row['status'],
                active_experiments=row['active_experiments'],
                last_activity=row['last_activity'],
                created_at=row['created_at']
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list installations: {str(e)}"
        )

# ============================================
# VERIFICAR INSTALACIÓN
# ============================================

@router.post("/{installation_id}/verify")
async def verify_installation(
    installation_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Verificar que la instalación está funcionando
    
    Intenta acceder al sitio y detectar el tracking code.
    """
    try:
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT * FROM platform_installations 
                WHERE id = $1 AND user_id = $2
                """,
                installation_id, user_id
            )
        
        if not installation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Installation not found"
            )
        
        # Intentar verificar (simplificado - en producción hacer HTTP request real)
        verified = await attempt_verification(
            installation['site_url'],
            installation['installation_token']
        )
        
        if verified:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE platform_installations 
                    SET status = 'active', verified_at = NOW(), last_activity = NOW()
                    WHERE id = $1
                    """,
                    installation_id
                )
                
                await conn.execute(
                    """
                    INSERT INTO installation_logs (installation_id, event_type, message)
                    VALUES ($1, 'verified', 'Installation verified successfully')
                    """,
                    installation_id
                )
            
            return {"verified": True, "status": "active"}
        else:
            return {
                "verified": False,
                "error": "Could not detect tracking code on your site. Please check the installation."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )

# ============================================
# OBTENER DETALLES
# ============================================

@router.get("/{installation_id}/details")
async def get_installation_details(
    installation_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Obtener detalles completos de la instalación"""
    try:
        async with db.pool.acquire() as conn:
            # Installation info
            installation = await conn.fetchrow(
                "SELECT * FROM platform_installations WHERE id = $1 AND user_id = $2",
                installation_id, user_id
            )
            
            if not installation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Installation not found"
                )
            
            # Stats
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT e.id) as total_experiments,
                    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active') as active_experiments,
                    COUNT(DISTINCT a.user_id) as total_visitors,
                    COUNT(DISTINCT a.id) FILTER (WHERE a.converted_at IS NOT NULL) as conversions
                FROM experiments e
                LEFT JOIN assignments a ON e.id = a.experiment_id
                WHERE e.user_id = $1 AND e.url LIKE $2
                """,
                user_id, installation['site_url'] + '%'
            )
            
            # Recent logs
            logs = await conn.fetch(
                """
                SELECT event_type, message, created_at
                FROM installation_logs
                WHERE installation_id = $1
                ORDER BY created_at DESC
                LIMIT 10
                """,
                installation_id
            )
        
        return {
            "installation": dict(installation),
            "stats": dict(stats) if stats else {},
            "recent_logs": [dict(log) for log in logs]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get details: {str(e)}"
        )

# ============================================
# ACTUALIZAR/ELIMINAR
# ============================================

@router.patch("/{installation_id}")
async def update_installation(
    installation_id: str,
    site_name: Optional[str] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Actualizar instalación"""
    try:
        updates = []
        params = [installation_id, user_id]
        param_count = 3
        
        if site_name:
            updates.append(f"site_name = ${param_count}")
            params.insert(-2, site_name)
            param_count += 1
        
        if status and status in ['active', 'inactive', 'paused']:
            updates.append(f"status = ${param_count}")
            params.insert(-2, status)
            param_count += 1
        
        if not updates:
            return {"status": "no_changes"}
        
        query = f"""
            UPDATE platform_installations 
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        
        async with db.pool.acquire() as conn:
            await conn.execute(query, *params)
        
        return {"status": "updated"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update: {str(e)}"
        )

@router.delete("/{installation_id}")
async def delete_installation(
    installation_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Eliminar instalación (soft delete)"""
    try:
        async with db.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE platform_installations 
                SET status = 'archived', updated_at = NOW()
                WHERE id = $1 AND user_id = $2
                """,
                installation_id, user_id
            )
        
        if result == "UPDATE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Installation not found"
            )
        
        return {"status": "archived"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete: {str(e)}"
        )

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_tracking_snippet(installation_token: str) -> str:
    """Generar código de tracking para instalación manual"""
    return f"""<!-- Samplit Tracking Code -->
<script>
  window.SAMPLIT_CONFIG = {{
    installationToken: '{installation_token}',
    apiEndpoint: 'https://api.samplit.com/v1'
  }};
</script>
<script src="https://cdn.samplit.com/tracker.js" async></script>
<!-- End Samplit Tracking Code -->"""

def generate_proxy_instructions(site_url: str, token: str, platform: str) -> Dict[str, Any]:
    """Generar instrucciones de proxy según plataforma"""
    
    proxy_url = f"https://proxy.samplit.com/{token}"
    
    if platform == "nginx":
        return {
            "type": "proxy",
            "platform": "nginx",
            "config": f"""location / {{
    proxy_pass {proxy_url};
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}}""",
            "steps": [
                f"Add config to /etc/nginx/sites-available/{site_url}",
                "Test: sudo nginx -t",
                "Reload: sudo systemctl reload nginx",
                "Verify installation"
            ]
        }
    
    elif platform == "apache":
        return {
            "type": "proxy",
            "platform": "apache",
            "config": f"""<IfModule mod_proxy.c>
    ProxyPreserveHost On
    ProxyPass / {proxy_url}/
    ProxyPassReverse / {proxy_url}/
</IfModule>""",
            "steps": [
                "Enable modules: sudo a2enmod proxy proxy_http",
                "Add config to Apache site",
                "Restart: sudo systemctl restart apache2",
                "Verify installation"
            ]
        }
    
    else:
        return {
            "type": "proxy",
            "platform": "generic",
            "proxy_url": proxy_url,
            "steps": [
                f"Configure your server to proxy to: {proxy_url}",
                "Ensure headers are forwarded",
                "Verify installation"
            ]
        }

async def attempt_verification(site_url: str, installation_token: str) -> bool:
    """
    Intentar verificar la instalación
    
    En producción: hacer HTTP request al sitio y buscar el token.
    Por ahora: simulado.
    """
    # TODO: Implementar verificación real con aiohttp
    # Por ahora retornamos True para testing
    import random
    return random.choice([True, False])  # 50% éxito para testing
