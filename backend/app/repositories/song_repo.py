"""app/repositories/song_repo.py"""
import uuid
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.song import Song
from app.repositories.base import BaseRepository


class SongRepository(BaseRepository[Song]):
    def __init__(self, db: AsyncSession):
        super().__init__(Song, db)

    async def search(self, venue_id: uuid.UUID, query: str, limit: int = 20) -> list[Song]:
        """Full-text search in venue's approved catalogue. Upgrade to Meilisearch at scale."""
        q = f"%{query.lower()}%"
        result = await self.db.execute(
            select(Song).where(
                and_(
                    Song.venue_id == venue_id,
                    Song.is_enabled == True,
                    Song.is_embeddable == True,
                    or_(Song.title.ilike(q), Song.artist.ilike(q)),
                )
            ).limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_for_venue(self, venue_id: uuid.UUID) -> list[Song]:
        result = await self.db.execute(
            select(Song).where(and_(Song.venue_id == venue_id, Song.is_enabled == True))
        )
        return list(result.scalars().all())

    async def get_unembeddable(self, venue_id: uuid.UUID) -> list[Song]:
        """Songs flagged as no longer embeddable — shown in venue dashboard for replacement."""
        result = await self.db.execute(
            select(Song).where(and_(Song.venue_id == venue_id, Song.is_embeddable == False))
        )
        return list(result.scalars().all())
