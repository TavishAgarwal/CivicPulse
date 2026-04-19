"""
CivicPulse — FastAPI Application Entry Point

Main application with CORS, rate limiting, route registration, and lifespan management.
Validates settings, tests DB/Redis connections at startup.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis as redis_lib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("civicpulse.api")

# Rate limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_anonymous],
    storage_uri=settings.redis_url,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle management."""
    # ── Startup ──
    logger.info("Starting CivicPulse API v%s (%s)", settings.app_version, settings.civicpulse_env)

    # Test database connection
    from database import test_db_connection
    db_ok = await test_db_connection()
    if not db_ok:
        logger.error("Database connection failed — API starting in degraded mode")

    # Test Redis connection
    try:
        r = redis_lib.from_url(settings.redis_url)
        r.ping()
        logger.info("Redis connection verified")
    except Exception as e:
        logger.warning("Redis not available: %s — caching disabled", e)

    logger.info("CivicPulse API ready")
    yield

    # ── Shutdown ──
    logger.info("Shutting down CivicPulse API")


app = FastAPI(
    title="CivicPulse API",
    description="AI-powered hyperlocal community distress prediction and volunteer dispatch",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.civicpulse_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions — never return raw tracebacks to client.
    """
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ── Register Routes ──
from routes.health import router as health_router
from routes.auth import router as auth_router
from routes.heatmap import router as heatmap_router
from routes.wards import router as wards_router
from routes.signals import router as signals_router
from routes.volunteers import router as volunteers_router
from routes.dispatch import router as dispatch_router
from routes.reports import router as reports_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(heatmap_router)
app.include_router(wards_router)
app.include_router(signals_router)
app.include_router(volunteers_router)
app.include_router(dispatch_router)
app.include_router(reports_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root redirect to docs."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
