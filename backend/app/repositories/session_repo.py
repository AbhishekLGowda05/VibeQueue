"""app/repositories/session_repo.py"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import TableSession
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[TableSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(TableSession, db)

    async def get_by_code(self, venue_id: uuid.UUID, table_code: str) -> TableSession | None:
        result = await self.db.execute(
            select(TableSession).where(
                and_(
                    TableSession.venue_id == venue_id,
                    TableSession.table_code == table_code,
                    TableSession.is_active == True,
                    TableSession.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_venue(self, venue_id: uuid.UUID) -> list[TableSession]:
        result = await self.db.execute(
            select(TableSession).where(
                and_(TableSession.venue_id == venue_id, TableSession.is_active == True)
            )
        )
        return list(result.scalars().all())

    async def close_session(self, session_id: uuid.UUID) -> None:
        await self.db.execute(
            update(TableSession).where(TableSession.id == session_id)
            .values(is_active=False, is_billed=True)
        )
