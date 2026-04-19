"""
CivicPulse — Health Check Route
GET /health — system health status, no auth required.
"""

import logging

import redis as redis_lib
from fastapi import APIRouter

from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check():
    """System health check with dependency status."""
    # DB check
    db_ok = False
    try:
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
        await conn.execute("SELECT 1")
        await conn.close()
        db_ok = True
    except Exception as e:
        logger.warning("DB health check failed: %s", e)

    # Redis check
    redis_ok = False
    try:
        r = redis_lib.from_url(settings.redis_url)
        r.ping()
        redis_ok = True
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)

    # Kafka check
    kafka_ok = False
    try:
        from kafka import KafkaConsumer
        consumer = KafkaConsumer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            request_timeout_ms=5000,
        )
        consumer.close()
        kafka_ok = True
    except Exception as e:
        logger.warning("Kafka health check failed: %s", e)

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.app_version,
        "environment": settings.civicpulse_env,
        "db_connected": db_ok,
        "redis_connected": redis_ok,
        "kafka_connected": kafka_ok,
        "integrations": {
            "whatsapp": bool(settings.whatsapp_api_token),
            "sms": bool(settings.twilio_account_sid),
            "push": bool(settings.firebase_server_key),
            "mapbox": bool(settings.mapbox_api_key),
        },
    }
