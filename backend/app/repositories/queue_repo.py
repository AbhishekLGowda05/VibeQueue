"""
app/repositories/queue_repo.py

All database operations for queue entries.
The queue engine (service layer) calls these methods — never writes SQL directly.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.queue import QueueEntry
from app.repositories.base import BaseRepository


class QueueRepository(BaseRepository[QueueEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(QueueEntry, db)

    async def get_active_queue(self, venue_id: uuid.UUID) -> list[QueueEntry]:
        """Songs in positions 1–8 (the visible queue), ordered by position."""
        result = await self.db.execute(
            select(QueueEntry)
            .where(
                and_(
                    QueueEntry.venue_id == venue_id,
                    QueueEntry.status == "active",
                    QueueEntry.position <= 8,
                )
            )
            .order_by(QueueEntry.position)
        )
        return list(result.scalars().all())

    async def get_waiting_pool(self, venue_id: uuid.UUID) -> list[QueueEntry]:
        """Songs beyond position 8, awaiting entry to active queue."""
        result = await self.db.execute(
            select(QueueEntry)
            .where(
                and_(
                    QueueEntry.venue_id == venue_id,
                    QueueEntry.status == "active",
                    QueueEntry.position > 8,
                )
            )
            .order_by(QueueEntry.position)
        )
        return list(result.scalars().all())

    async def get_next_to_play(self, venue_id: uuid.UUID) -> QueueEntry | None:
        """The song at position 1 — next to play."""
        result = await self.db.execute(
            select(QueueEntry)
            .where(
                and_(
                    QueueEntry.venue_id == venue_id,
                    QueueEntry.status == "active",
                    QueueEntry.position == 1,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_session(
        self, session_id: uuid.UUID, status: str = None
    ) -> list[QueueEntry]:
        """All entries for a table session (for pre-billing review)."""
        conditions = [QueueEntry.session_id == session_id]
        if status:
            conditions.append(QueueEntry.status == status)
        result = await self.db.execute(
            select(QueueEntry).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def mark_as_playing(self, entry_id: uuid.UUID) -> None:
        await self.db.execute(
            update(QueueEntry)
            .where(QueueEntry.id == entry_id)
            .values(status="playing")
        )

    async def mark_as_played(self, entry_id: uuid.UUID) -> None:
        await self.db.execute(
            update(QueueEntry)
            .where(QueueEntry.id == entry_id)
            .values(status="played", played_at=datetime.now(timezone.utc))
        )

    async def count_active_for_venue(self, venue_id: uuid.UUID) -> int:
        """Total songs currently in active queue (1–8). Used to enforce ceiling."""
        result = await self.db.execute(
            select(QueueEntry)
            .where(
                and_(
                    QueueEntry.venue_id == venue_id,
                    QueueEntry.status == "active",
                    QueueEntry.position <= 8,
                )
            )
        )
        return len(result.scalars().all())

    async def get_expired_entries(self, before: datetime) -> list[QueueEntry]:
        """Find queue entries past their expiry — for the nightly cleanup job."""
        result = await self.db.execute(
            select(QueueEntry)
            .where(
                and_(
                    QueueEntry.status == "active",
                    QueueEntry.expires_at < before,
                )
            )
        )
        return list(result.scalars().all())
