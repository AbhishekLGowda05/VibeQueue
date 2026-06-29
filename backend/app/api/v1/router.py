"""
app/api/v1/router.py

Aggregates all v1 route modules into one router.
Mounted in app/main.py under /api/v1
"""

from fastapi import APIRouter

from app.api.v1.routes import (
    analytics,
    auth,
    billing,
    boosts,
    catalogue,
    health,
    payments,
    playback,
    queue,
    sessions,
    songs,
    venues,
    websockets,
)

api_v1_router = APIRouter()

# ── System ───────────────────────────────────────────────────────────────────
api_v1_router.include_router(health.router, prefix="/health", tags=["System"])

# ── Auth ─────────────────────────────────────────────────────────────────────
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# ── Venues ───────────────────────────────────────────────────────────────────
api_v1_router.include_router(venues.router, prefix="/venues", tags=["Venues"])

# ── Catalogue (song pool management) ─────────────────────────────────────────
api_v1_router.include_router(catalogue.router, prefix="/catalogue", tags=["Catalogue"])

# ── Songs ────────────────────────────────────────────────────────────────────
api_v1_router.include_router(songs.router, prefix="/songs", tags=["Songs"])

# ── Sessions (table sessions) ─────────────────────────────────────────────────
api_v1_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])

# ── Queue ────────────────────────────────────────────────────────────────────
api_v1_router.include_router(queue.router, prefix="/queue", tags=["Queue"])

# ── Boosts ───────────────────────────────────────────────────────────────────
api_v1_router.include_router(boosts.router, prefix="/boosts", tags=["Boosts"])

# ── Billing ──────────────────────────────────────────────────────────────────
api_v1_router.include_router(billing.router, prefix="/billing", tags=["Billing"])

# ── Payments ─────────────────────────────────────────────────────────────────
api_v1_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

# ── Playback (venue-side events from YouTube IFrame) ─────────────────────────
api_v1_router.include_router(playback.router, prefix="/playback", tags=["Playback"])

# ── Analytics ────────────────────────────────────────────────────────────────
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# ── WebSockets ───────────────────────────────────────────────────────────────
api_v1_router.include_router(websockets.router, prefix="/ws", tags=["WebSockets"])
