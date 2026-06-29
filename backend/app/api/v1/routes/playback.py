"""
app/api/v1/routes/playback.py

Playback event receiver — called by the YouTube IFrame Player
running on the venue's laptop (the VibeQueue Playback Tab).

POST /playback/event    — receives PLAYING, ENDED, ERROR events from the browser
GET  /playback/command  — venue laptop polls for the next play command
                          (also delivered via WebSocket, but polling is the fallback)
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_staff
from app.core.database import get_db
from app.models.user import User
from app.repositories.boost_repo import BoostRepository
from app.repositories.playback_repo import PlaybackRepository
from app.repositories.queue_repo import QueueRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.playback import PlaybackCommandResponse, PlaybackEventCreate
from app.services.playback_service import PlaybackService
from app.services.queue_engine import QueueEngine

router = APIRouter()


@router.post("/event")
async def receive_playback_event(
    payload: PlaybackEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """
    The YouTube Playback Tab on the venue laptop sends events here.

    PLAYING  → acknowledges command, marks song as 'playing'
    ENDED    → THE BILLING TRIGGER — confirms all pending boosts, triggers next song
    ERROR    → logs error, starts fallback timer
    PAUSED   → informational, no billing action
    BUFFERING → informational, monitored for threshold alerts
    """
    engine = QueueEngine(
        queue_repo=QueueRepository(db),
        boost_repo=BoostRepository(db),
        session_repo=SessionRepository(db),
    )
    playback_service = PlaybackService(
        playback_repo=PlaybackRepository(db),
        queue_repo=QueueRepository(db),
        queue_engine=engine,
        db=db,
    )
    await playback_service.handle_event(
        venue_id=payload.venue_id,
        queue_entry_id=payload.queue_entry_id,
        youtube_video_id=payload.youtube_video_id,
        event_type=payload.event_type,
        error_code=payload.error_code,
    )
    return {"status": "received", "event_type": payload.event_type}


@router.get("/next/{venue_id}", response_model=PlaybackCommandResponse | None)
async def get_next_command(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """
    Polling fallback for the venue laptop.
    Returns the next pending playback command if one exists.
    The primary delivery is via WebSocket (/ws/venue/{id}/dashboard).
    This endpoint is the safety net if WebSocket drops.
    """
    repo = PlaybackRepository(db)
    queue_repo = QueueRepository(db)

    next_song = await queue_repo.get_next_to_play(venue_id)
    if not next_song:
        return None

    return PlaybackCommandResponse(
        id=next_song.id,
        youtube_video_id=next_song.youtube_video_id,
        action="play",
        song_title="",    # Joined from song table in full implementation
        requesting_table="",
    )
