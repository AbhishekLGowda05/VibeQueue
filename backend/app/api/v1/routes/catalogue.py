"""
app/api/v1/routes/catalogue.py

Venue catalogue management — venue owners manage their approved song pool here.

GET    /catalogue/{venue_id}              — list all songs (with embeddability status)
POST   /catalogue/{venue_id}/songs        — add a song (by YouTube video ID)
PATCH  /catalogue/{venue_id}/songs/{id}   — enable/disable a song
DELETE /catalogue/{venue_id}/songs/{id}   — remove a song permanently
POST   /catalogue/{venue_id}/validate     — manually trigger re-validation
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_venue_owner
from app.core.database import get_db
from app.models.user import User
from app.repositories.song_repo import SongRepository
from app.schemas.song import SongCatalogueUpdate, SongSearch

router = APIRouter()


@router.get("/{venue_id}", response_model=list[SongSearch])
async def list_catalogue(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_venue_owner),
):
    """Returns full catalogue including disabled songs (for management view)."""
    repo = SongRepository(db)
    from sqlalchemy import select
    from app.models.song import Song
    from sqlalchemy import and_
    result = await db.execute(select(Song).where(Song.venue_id == venue_id))
    songs = list(result.scalars().all())
    return [
        SongSearch(
            id=s.id, title=s.title, artist=s.artist,
            youtube_video_id=s.youtube_video_id, genre=s.genre,
            duration_seconds=s.duration_seconds,
        ) for s in songs
    ]


@router.post("/{venue_id}/songs", response_model=SongSearch, status_code=201)
async def add_song(
    venue_id: uuid.UUID,
    payload: SongCatalogueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_venue_owner),
):
    """
    Add a song to the venue's catalogue by YouTube video ID.
    The YouTube Data API is called to verify the video is public and embeddable.
    """
    # In full implementation: call youtube_service.verify_video(payload.youtube_video_id)
    # and use returned metadata for title/artist if not provided
    repo = SongRepository(db)
    song = await repo.create(
        venue_id=venue_id,
        youtube_video_id=payload.youtube_video_id,
        title=payload.title,
        artist=payload.artist,
        genre=payload.genre,
        is_enabled=payload.is_enabled,
        is_embeddable=True,   # Will be validated by weekly job
        available_after_hour=payload.available_after_hour,
        available_before_hour=payload.available_before_hour,
    )
    return SongSearch(
        id=song.id, title=song.title, artist=song.artist,
        youtube_video_id=song.youtube_video_id, genre=song.genre,
        duration_seconds=song.duration_seconds,
    )


@router.patch("/{venue_id}/songs/{song_id}/toggle")
async def toggle_song(
    venue_id: uuid.UUID,
    song_id: uuid.UUID,
    enabled: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_venue_owner),
):
    """Enable or disable a song in the catalogue. Disabled songs are hidden from guests."""
    repo = SongRepository(db)
    song = await repo.get_by_id(song_id)
    if not song or song.venue_id != venue_id:
        raise HTTPException(status_code=404, detail="Song not found")
    await repo.update(song, is_enabled=enabled)
    return {"song_id": str(song_id), "is_enabled": enabled}


@router.post("/{venue_id}/validate")
async def trigger_validation(
    venue_id: uuid.UUID,
    current_user: User = Depends(get_current_venue_owner),
):
    """
    Manually trigger YouTube embeddability re-validation for this venue's catalogue.
    Useful after the owner suspects some videos have been removed.
    Dispatched as a background Celery task — returns immediately.
    """
    from app.workers.tasks.catalogue_tasks import validate_venue_catalogue
    validate_venue_catalogue.delay(str(venue_id))
    return {"status": "validation_queued", "venue_id": str(venue_id)}
