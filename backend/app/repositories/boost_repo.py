"""
app/repositories/boost_repo.py

All database operations for boost records.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boost import Boost
from app.repositories.base import BaseRepository


class BoostRepository(BaseRepository[Boost]):
    def __init__(self, db: AsyncSession):
        super().__init__(Boost, db)

    async def get_by_session(self, session_id: uuid.UUID) -> list[Boost]:
        """All boosts for a table session — used in billing review."""
        result = await self.db.execute(
            select(Boost).where(Boost.session_id == session_id)
        )
        return list(result.scalars().all())

    async def get_confirmed_by_session(self, session_id: uuid.UUID) -> list[Boost]:
        """Only confirmed (played) boosts — these are the billable charges."""
        result = await self.db.execute(
            select(Boost).where(
                and_(Boost.session_id == session_id, Boost.status == "confirmed")
            )
        )
        return list(result.scalars().all())

    async def get_pending_by_entry(self, queue_entry_id: uuid.UUID) -> list[Boost]:
        """Pending boosts for a queue entry — confirmed when song plays."""
        result = await self.db.execute(
            select(Boost).where(
                and_(
                    Boost.queue_entry_id == queue_entry_id,
                    Boost.status == "pending",
                )
            )
        )
        return list(result.scalars().all())

    async def confirm_all_for_entry(self, queue_entry_id: uuid.UUID) -> int:
        """
        Called when ENDED event fires.
        Marks all pending boosts for this queue entry as confirmed.
        Returns the count of boosts confirmed.
        """
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(Boost)
            .where(
                and_(
                    Boost.queue_entry_id == queue_entry_id,
                    Boost.status == "pending",
                )
            )
            .values(status="confirmed", confirmed_at=now)
        )
        return result.rowcount

    async def cancel_all_for_entry(self, queue_entry_id: uuid.UUID) -> int:
        """
        Called when a song is removed, skipped, or expires without playing.
        Cancels all pending boosts — no charge to the guest.
        """
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(Boost)
            .where(
                and_(
                    Boost.queue_entry_id == queue_entry_id,
                    Boost.status == "pending",
                )
            )
            .values(status="cancelled", cancelled_at=now)
        )
        return result.rowcount

    async def sum_confirmed_paise(self, session_id: uuid.UUID) -> int:
        """
        Total confirmed boost charges for a session in paise.
        This is what gets added to the table's food bill.
        """
        boosts = await self.get_confirmed_by_session(session_id)
        return sum(b.amount_paise for b in boosts)
