"""
app/main.py

FastAPI application factory.
This file wires together: CORS, middleware, routers, lifespan, error handlers.
Keep it thin — logic lives in services and routes, not here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.api.v1.middleware.error_handler import register_exception_handlers
from app.core.config import settings
from app.core.events import lifespan


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="VibeQueue — Venue Music Queue API",
        docs_url="/docs" if settings.is_development else None,   # Hide Swagger in prod
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────
    app.include_router(api_v1_router, prefix="/api/v1")

    # ── Exception Handlers ───────────────────────────────────────────
    register_exception_handlers(app)

    return app


app = create_application()
