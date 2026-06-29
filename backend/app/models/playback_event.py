"""
app/models/playback_event.py
Events received from the YouTube IFrame Player (PLAYING, ENDED, ERROR).
These are the billing triggers.
"""
import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class PlaybackEvent(BaseModel):
    __tablename__ = "playback_events"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    command_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("playback_commands.id"), nullable=True)
    queue_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queue_entries.id"), nullable=False)
    youtube_video_id: Mapped[str] = mapped_column(String(20), nullable=False)
    # event_type: 'PLAYING' | 'ENDED' | 'ERROR' | 'PAUSED' | 'BUFFERING'
    event_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    error_code: Mapped[str] = mapped_column(String(10), nullable=True)
