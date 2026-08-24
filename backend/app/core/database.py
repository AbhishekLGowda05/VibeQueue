"""
app/core/database.py

Async SQLAlchemy engine and session factory.
All DB operations in VibeQueue are async — never block the event loop.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ── Engine ────────────────────────────────────────────────────────────────────
# Disable asyncpg prepared statement cache when using PgBouncer (transaction pooler)
_connect_args = {}
if "pooler.supabase.com" in settings.DATABASE_URL:
    _connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,          # Reconnect on stale connections
    echo=settings.is_development, # Log SQL in dev, never in prod
    connect_args=_connect_args,
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,      # Prevent lazy-load errors after commit
    autocommit=False,
    autoflush=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this.
    Defined here to avoid circular imports.
    """
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — yields a db session per request.
    The session is committed on success and rolled back on any exception.

    Usage:
        @router.get("/")
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
