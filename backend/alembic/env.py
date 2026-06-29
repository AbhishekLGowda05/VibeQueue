"""alembic/env.py — Alembic migration environment"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

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


def run_migrations_online():
    connectable = create_async_engine(settings.DATABASE_URL)

    async def do_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda sync_conn: context.configure(
                    connection=sync_conn,
                    target_metadata=target_metadata,
                    compare_type=True,
                )
            )
            async with connection.begin():
                await connection.run_sync(lambda _: context.run_migrations())

    asyncio.run(do_migrations())


run_migrations_online()
