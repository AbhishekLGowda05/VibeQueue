"""
app/api/v1/routes/songs.py

Song search endpoint — the only endpoint guests use to find songs.
Search is scoped to the venue's approved catalogue only.
"""
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.session import get_guest_session
from app.core.database import get_db
from app.models.session import TableSession
from app.repositories.song_repo import SongRepository
from app.schemas.song import SongSearch

router = APIRouter()


@router.get("/search", response_model=list[SongSearch])
async def search_songs(
    q: str = Query(..., min_length=2, max_length=100),
    guest_session: TableSession = Depends(get_guest_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Search the venue's approved song catalogue.
    Scoped to the authenticated guest's venue — cannot search across venues.
    Results are filtered to only enabled + embeddable songs.
    At scale: replace PostgreSQL ilike with Meilisearch for typo tolerance.
    """
    repo = SongRepository(db)
    songs = await repo.search(
        venue_id=guest_session.venue_id,
        query=q,
        limit=20,
    )
    return [
        SongSearch(
            id=s.id,
            title=s.title,
            artist=s.artist,
            youtube_video_id=s.youtube_video_id,
            genre=s.genre,
            duration_seconds=s.duration_seconds,
        )
        for s in songs
    ]


@router.get("/venue/{venue_id}", response_model=list[SongSearch])
async def get_all_venue_songs(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns full catalogue for a venue (for ambient display preload / browse mode).
    Public endpoint — no auth required since catalogue is public info.
    """
    repo = SongRepository(db)
    songs = await repo.get_all_for_venue(venue_id)
    return [
        SongSearch(
            id=s.id,
            title=s.title,
            artist=s.artist,
            youtube_video_id=s.youtube_video_id,
            genre=s.genre,
            duration_seconds=s.duration_seconds,
        )
        for s in songs
    ]
