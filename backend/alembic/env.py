"""alembic/env.py — Alembic migration environment"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.core.database import Base

# Import all models so Alembic auto-detects them
from app.models import (  # noqa: F401
    venue, user, song, session, queue, boost, payment,
    playback_command, playback_event, audit_log
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sync_url() -> str:
    """Convert async URL to sync for Alembic (psycopg2, not asyncpg).
    psycopg2 works cleanly with PgBouncer — no prepared-statement issues."""
    return settings.DATABASE_URL.replace("+asyncpg", "")


def run_migrations_offline():
    """Run migrations in 'offline' mode — generates SQL without a live connection."""
    context.configure(
        url=_get_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode — connects to the database."""
    connectable = create_engine(
        _get_sync_url(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
