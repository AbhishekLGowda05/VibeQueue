"""app/schemas/playback.py"""
import uuid
from pydantic import BaseModel


class PlaybackEventCreate(BaseModel):
    """Sent from the YouTube IFrame Player on the venue laptop."""
    venue_id: uuid.UUID
    queue_entry_id: uuid.UUID
    youtube_video_id: str
    event_type: str   # 'PLAYING' | 'ENDED' | 'ERROR' | 'PAUSED'
    error_code: str | None = None


class PlaybackCommandResponse(BaseModel):
    """Sent to the venue laptop — tells it what to play next."""
    id: uuid.UUID
    youtube_video_id: str
    action: str
    song_title: str
    requesting_table: str

    model_config = {"from_attributes": True}
