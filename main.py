# main.py

"""
Samplit Platform - Main Application - VERSIÓN COMPLETA

✅ Incluye instalación simplificada de 1 línea
✅ Incluye tracker API completo

Copyright (c) 2024 Samplit Technologies. All rights reserved.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from orchestration.services.service_factory import ServiceFactory
import logging
import time
from typing import Callable

from config.settings import get_settings
from data_access.database import DatabaseManager
from public_api.middleware.error_handler import ErrorHandlerMiddleware
from public_api.middleware.rate_limit import rate_limiter

# Import routers
from public_api.routers import (
    auth,
    experiments,
    analytics,
    installations,
    tracker,
    system,
    experiments_multi_element,
    audit,
    simulator,
    leads,
    public_dashboard,
    visual_editor,
    downloads,
    proxy,
    traffic_filters,
    demo,
    integrations,
    subscriptions,
    onboarding
)

# ════════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ════════════════════════════════════════════════════════════════════════════

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("samplit.main")

# ════════════════════════════════════════════════════════════════════════════
# LIFESPAN MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    # ════════════════════════════════════════════════════════════════════════
    # STARTUP
    # ════════════════════════════════════════════════════════════════════════
    
    logger.info("Starting Samplit Platform...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Version: {settings.APP_VERSION}")
    
    # Initialize database
    db = DatabaseManager()
    await db.initialize()
    app.state.db = db
    logger.info("Database initialized")
    
    # Auto-detect and create service (PostgreSQL or Redis)
    app.state.experiment_service = await ServiceFactory.create_experiment_service(db)
    
    logger.info("Samplit Platform ready!")
    
    yield
    
    # ════════════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ════════════════════════════════════════════════════════════════════════
    
    logger.info("Shutting down Samplit Platform...")
    
    # Shutdown metrics monitoring
    await ServiceFactory.shutdown()
    
    await db.close()
    logger.info("Samplit Platform stopped")

# ════════════════════════════════════════════════════════════════════════════
# CREATE APP
# ════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Samplit Platform API",
    description="Unified API for experimentation and tracking",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# ════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ════════════════════════════════════════════════════════════════════════════

# 1. Error Handling (must be first to catch everything)
app.add_middleware(ErrorHandlerMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Security Headers
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.render.com", "*.samplit.com"]
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.samplit.com", "samplit.com"]
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    """Add X-Process-Time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable):
    """Add security headers - Hide technology stack"""
    response = await call_next(request)
    
    # Generic headers - don't reveal FastAPI/Python
    response.headers["X-Powered-By"] = "Samplit"
    response.headers["Server"] = "Samplit"
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# ════════════════════════════════════════════════════════════════════════════
# EXCEPTION HANDLERS
# ════════════════════════════════════════════════════════════════════════════

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    
    # Log full error internally
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}", 
        exc_info=True
    )
    
    # Production: Generic error message
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Service Temporarily Unavailable",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": str(hash(time.time()))
            }
        )
    # Development: Show details
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(exc),
                "type": type(exc).__name__
            }
        )

# ════════════════════════════════════════════════════════════════════════════
# INCLUDE ROUTERS
# ════════════════════════════════════════════════════════════════════════════

# Auth (Supabase OAuth)
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

# Experiments
app.include_router(
    experiments.router,
    prefix=f"{settings.API_V1_PREFIX}/experiments",
    tags=["Experiments"]
)

# Analytics
app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_PREFIX}/analytics",
    tags=["Analytics"]
)

# Dashboard (Public Exposure)
app.include_router(
    public_dashboard.router,
    prefix=f"{settings.API_V1_PREFIX}/dashboard",
    tags=["Public Dashboard"]
)

# System metrics
app.include_router(
    system.router,
    prefix=f"{settings.API_V1_PREFIX}/system",
    tags=["System"]
)

# ✅ Installations (incluye instalación simple de 1 línea)
app.include_router(
    installations.router,
    prefix=f"{settings.API_V1_PREFIX}/installations",
    tags=["Installations"]
)

# ✅ Multi-element Factorial Experiments
app.include_router(
    experiments_multi_element.router,
    prefix=f"{settings.API_V1_PREFIX}/orchestration",
    tags=["Orchestration"]
)

# ✅ Audit System & Verification
app.include_router(
    audit.router,
    prefix=f"{settings.API_V1_PREFIX}/audit",
    tags=["Audit"]
)

app.include_router(
    demo.router,
    prefix=f"{settings.API_V1_PREFIX}/verify",
    tags=["Verification"]
)

# ✅ Public Dashboard & Reports
app.include_router(
    public_dashboard.router,
    prefix=f"{settings.API_V1_PREFIX}/reports",
    tags=["Reports"]
)

# ✅ Visual Editor & Canvas
app.include_router(
    visual_editor.router,
    prefix=f"{settings.API_V1_PREFIX}/canvas",
    tags=["Visual Editor"]
)

# ✅ Data Export & Downloads
app.include_router(
    downloads.router,
    prefix=f"{settings.API_V1_PREFIX}/export",
    tags=["Exports"]
)

# ✅ Edge Proxy & Tunneling
app.include_router(
    proxy.router,
    prefix=f"{settings.API_V1_PREFIX}/edge",
    tags=["Edge"]
)

# ✅ Traffic Rules & Filters
app.include_router(
    traffic_filters.router,
    prefix=f"{settings.API_V1_PREFIX}/traffic",
    tags=["Traffic Control"]
)

# Segmentation Control (Placeholder for future)
# app.include_router(...)

# ✅ Simulator (Public Demo)
app.include_router(
    simulator.router,
    prefix=f"{settings.API_V1_PREFIX}/simulate",
    tags=["Simulator"]
)

# Admin Endpoints (Protected)
app.include_router(
    leads.router,
    prefix=f"{settings.API_V1_PREFIX}/leads",
    tags=["Leads"]
)

# ✅ Platform Integrations (WordPress, Shopify)
app.include_router(
    integrations.router,
    prefix=f"{settings.API_V1_PREFIX}/integrations",
    tags=["Integrations"]
)

# ✅ Billing & Subscriptions
app.include_router(
    subscriptions.router,
    prefix=f"{settings.API_V1_PREFIX}/subscriptions",
    tags=["Subscriptions"]
)

# ✅ User Onboarding
app.include_router(
    onboarding.router,
    prefix=f"{settings.API_V1_PREFIX}/onboarding",
    tags=["Onboarding"]
)

# ════════════════════════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS (No Auth Required)
# ════════════════════════════════════════════════════════════════════════════

# ✅ Tracker API (usado por JavaScript tracker en sitios de usuarios)
# Incluye endpoint nuevo: /experiments/active
app.include_router(
    tracker.router,
    prefix=f"{settings.API_V1_PREFIX}/tracker",
    tags=["Tracker (Public)"]
)

# ✅ Static Files (Tracker JS, Dashboard Assets)
from fastapi.staticfiles import StaticFiles
import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory not found: {static_dir}")

# ════════════════════════════════════════════════════════════════════════════
# ROOT ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.get("/dashboard", include_in_schema=False)
async def dashboard_ui():
    """Serve the dashboard UI"""
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "marketing-dashboard.html"))

@app.get("/editor", include_in_schema=False)
async def visual_editor_ui():
    """Serve the Visual Editor UI"""
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "visual-editor.html"))

@app.get("/funnel-builder", include_in_schema=False)
async def funnel_builder_ui():
    """Serve the Funnel Builder UI"""
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "funnel-builder.html"))

@app.get("/simulator", include_in_schema=False)
async def simulator_landing_ui():
    """Serve the Simulator Landing Page"""
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "simulator-landing.html"))

# ════════════════════════════════════════════════════════════════════════════
# PUBLIC MARKETING PAGES
# ════════════════════════════════════════════════════════════════════════════

@app.get("/about", include_in_schema=False)
async def about_page():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "about.html"))

@app.get("/contact", include_in_schema=False)
async def contact_page():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "contact.html"))

@app.get("/privacy", include_in_schema=False)
async def privacy_page():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "privacy.html"))

@app.get("/terms", include_in_schema=False)
async def terms_page():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "terms.html"))

@app.get("/faq", include_in_schema=False)
async def faq_page():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "faq.html"))

@app.get("/")
async def root():
    """Root endpoint - public info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "features": {
            "ab_testing": True,
            "simple_installation": True,  # ✅ NUEVO
            "adaptive_optimization": True
        },
        "docs": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint
    
    Verifies database connectivity and system status
    """
    db: DatabaseManager = request.app.state.db
    
    try:
        db_healthy = await db.health_check()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": "Service unavailable"
            }
        )

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"pong": True, "timestamp": datetime.utcnow().isoformat()}

# ════════════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS (Protected)
# ════════════════════════════════════════════════════════════════════════════

@app.get(f"{settings.API_V1_PREFIX}/system/stats")
async def system_stats(request: Request):
    """
    System statistics
    
    Should be protected in production
    """
    if settings.ENVIRONMENT == "production":
        return {"error": "Endpoint disabled in production"}
    
    db: DatabaseManager = request.app.state.db
    stats = await db.get_database_stats()
    
    return {
        "system": "samplit",
        "version": settings.APP_VERSION,
        "database": stats
    }

# ════════════════════════════════════════════════════════════════════════════
# STARTUP MESSAGE
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    
    print("""
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║          SAMPLIT PLATFORM             ║
    ║   Intelligent A/B Testing Engine      ║
    ║                                       ║
    ║   ✅ 1-Line Installation              ║
    ║   ✅ Adaptive Strategy                ║
    ║   ✅ Auto-Optimization                ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
