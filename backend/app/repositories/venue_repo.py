"""app/repositories/venue_repo.py"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.venue import Venue
from app.repositories.base import BaseRepository


class VenueRepository(BaseRepository[Venue]):
    def __init__(self, db: AsyncSession):
        super().__init__(Venue, db)

    async def get_by_slug(self, slug: str) -> Venue | None:
        result = await self.db.execute(select(Venue).where(Venue.slug == slug))
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[Venue]:
        result = await self.db.execute(select(Venue).where(Venue.is_active == True))
        return list(result.scalars().all())
