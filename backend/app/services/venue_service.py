"""app/services/venue_service.py"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.venue_repo import VenueRepository


class VenueService:
    def __init__(self, repo: VenueRepository, db: AsyncSession):
        self.repo = repo
        self.db = db

    async def get_spend_cap(self, venue_id: uuid.UUID) -> int:
        """Returns venue's configured spend cap in paise."""
        venue = await self.repo.get_by_id(venue_id)
        return venue.spend_cap_paise if venue else 15000
