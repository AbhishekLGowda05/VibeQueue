"""app/repositories/playback_repo.py"""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.playback_command import PlaybackCommand
from app.models.playback_event import PlaybackEvent
from app.repositories.base import BaseRepository
from app.core.config import settings


class PlaybackRepository(BaseRepository[PlaybackCommand]):
    def __init__(self, db: AsyncSession):
        super().__init__(PlaybackCommand, db)

    async def get_stalled_commands(self) -> list[PlaybackCommand]:
        """Commands still pending after PLAYBACK_WATCHDOG_SECONDS — these need alerts."""
        threshold = datetime.now(timezone.utc) - timedelta(
            seconds=settings.PLAYBACK_WATCHDOG_SECONDS
        )
        result = await self.db.execute(
            select(PlaybackCommand).where(
                and_(
                    PlaybackCommand.status == "pending",
                    PlaybackCommand.created_at < threshold,
                )
            )
        )
        return list(result.scalars().all())

    async def create_event(self, **kwargs) -> PlaybackEvent:
        """Record a playback event (PLAYING, ENDED, ERROR) from the venue laptop."""
        event = PlaybackEvent(**kwargs)
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event
