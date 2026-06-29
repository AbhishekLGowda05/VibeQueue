"""
app/api/v1/routes/queue.py

Queue read and write endpoints.

GET  /queue/{venue_id}          — current queue state (used on initial page load)
POST /queue/request             — guest submits a free song request
DELETE /queue/{entry_id}        — guest or staff removes a song from queue
POST /queue/{entry_id}/mark-played — Mode B: staff confirms song was played manually
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_staff
from app.api.v1.dependencies.session import get_guest_session
from app.core.database import get_db
from app.models.session import TableSession
from app.models.user import User
from app.repositories.boost_repo import BoostRepository
from app.repositories.queue_repo import QueueRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.queue import QueueState, SongRequestCreate, SongRequestResponse
from app.services.queue_engine import QueueEngine

router = APIRouter()


def get_queue_engine(db: AsyncSession = Depends(get_db)) -> QueueEngine:
    return QueueEngine(
        queue_repo=QueueRepository(db),
        boost_repo=BoostRepository(db),
        session_repo=SessionRepository(db),
    )


@router.get("/{venue_id}", response_model=QueueState)
async def get_queue(venue_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns current full queue state.
    Called once on page load — after that, WebSocket pushes updates.
    """
    repo = QueueRepository(db)
    active = await repo.get_active_queue(venue_id)
    waiting = await repo.get_waiting_pool(venue_id)
    now_playing = next((e for e in active if e.status == "playing"), None)

    return QueueState(
        venue_id=venue_id,
        active_queue=[SongRequestResponse(
            id=e.id,
            position=e.position,
            song_id=e.song_id,
            youtube_video_id=e.youtube_video_id,
            status=e.status,
            boost_total_paise=e.boost_total_paise,
            score=round(e.score, 2),
            expires_at=e.expires_at,
        ) for e in active],
        waiting_pool_count=len(waiting),
        now_playing=SongRequestResponse(
            id=now_playing.id,
            position=now_playing.position,
            song_id=now_playing.song_id,
            youtube_video_id=now_playing.youtube_video_id,
            status=now_playing.status,
            boost_total_paise=now_playing.boost_total_paise,
            score=round(now_playing.score, 2),
            expires_at=now_playing.expires_at,
        ) if now_playing else None,
    )


@router.post("/request", response_model=SongRequestResponse, status_code=201)
async def request_song(
    payload: SongRequestCreate,
    guest_session: TableSession = Depends(get_guest_session),
    engine: QueueEngine = Depends(get_queue_engine),
):
    """
    Guest submits a free song request.
    Enforces: cooldown, approved catalogue, queue limit.
    """
    entry = await engine.add_song_request(
        venue_id=guest_session.venue_id,
        session_id=guest_session.id,
        song_id=payload.song_id,
        youtube_video_id=payload.youtube_video_id,
    )
    return SongRequestResponse(
        id=entry.id,
        position=entry.position,
        song_id=entry.song_id,
        youtube_video_id=entry.youtube_video_id,
        status=entry.status,
        boost_total_paise=entry.boost_total_paise,
        score=round(entry.score, 2),
        expires_at=entry.expires_at,
    )


@router.delete("/{entry_id}")
async def remove_song(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """
    Staff removes a song from the queue (silent, no notification to guest).
    Cancels all pending boosts for this entry — no charge to the table.
    """
    queue_repo = QueueRepository(db)
    boost_repo = BoostRepository(db)

    entry = await queue_repo.get_by_id(entry_id)
    if entry:
        await boost_repo.cancel_all_for_entry(entry_id)
        await queue_repo.update(entry, status="cancelled")

    # Broadcast updated queue
    from app.core.redis import RedisKeys, redis_queue_client
    await redis_queue_client.publish(
        RedisKeys.websocket_channel(str(entry.venue_id)), "queue_updated"
    )
    return {"status": "removed", "entry_id": str(entry_id)}


@router.post("/{entry_id}/mark-played")
async def mark_played(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
    engine: QueueEngine = Depends(get_queue_engine),
):
    """
    Mode B only: staff taps this after playing the song on their own system.
    This is the billing trigger in Mode B — equivalent to the ENDED event in Mode A.
    """
    queue_repo = QueueRepository(db)
    entry = await queue_repo.get_by_id(entry_id)
    if not entry:
        from app.exceptions.queue import QueueSongNotFoundError
        raise QueueSongNotFoundError()

    await engine.confirm_song_played(entry.venue_id, entry_id)
    return {"status": "marked_played", "entry_id": str(entry_id)}
