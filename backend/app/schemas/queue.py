"""app/schemas/queue.py — Pydantic schemas for queue operations"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class SongRequestCreate(BaseModel):
    song_id: uuid.UUID
    youtube_video_id: str


class SongRequestResponse(BaseModel):
    id: uuid.UUID
    position: int
    song_id: uuid.UUID
    youtube_video_id: str
    status: str
    boost_total_paise: int
    score: float
    expires_at: datetime
    estimated_wait_minutes: float | None = None

    model_config = {"from_attributes": True}


class QueueState(BaseModel):
    """Full queue snapshot sent to clients on connect and after every change."""
    venue_id: uuid.UUID
    active_queue: list[SongRequestResponse]
    waiting_pool_count: int
    now_playing: SongRequestResponse | None = None


class WaitingPoolEntry(BaseModel):
    id: uuid.UUID
    position: int
    youtube_video_id: str
    status: str
    message: str = "Your song is in the waiting list — it will enter the queue as songs play."

    model_config = {"from_attributes": True}
