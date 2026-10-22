"""
app/core/events.py

Application startup and shutdown lifecycle hooks.
Registered in app/main.py via lifespan context manager.
"""

from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.redis import close_redis_connections, ping_redis

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Everything before yield  = startup
    Everything after yield   = shutdown
    """
    # ── Startup ──────────────────────────────────────────────────────
    setup_logging()
    logger.info("vibequeue.startup", env=settings.APP_ENV)

    # Refuse to start in production with the dev placeholder JWT secret
    if settings.is_production and "change-in-production" in settings.JWT_SECRET_KEY:
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY is still the dev placeholder — "
            "generate a real secret before starting in production"
        )

    # Sentry (only in non-dev)
    if settings.SENTRY_DSN and not settings.is_development:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            environment=settings.APP_ENV,
        )
        logger.info("vibequeue.sentry.enabled")

    # Redis health check
    redis_ok = await ping_redis()
    if not redis_ok:
        logger.error("vibequeue.redis.unreachable")
        raise RuntimeError("Cannot connect to Redis — refusing to start")
    logger.info("vibequeue.redis.ok")

    logger.info("vibequeue.ready", port=settings.APP_PORT)

    yield  # ← Application is running

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("vibequeue.shutdown")
    await close_redis_connections()
    logger.info("vibequeue.shutdown.complete")
