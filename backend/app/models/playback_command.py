"""
app/models/playback_command.py
Commands sent from queue engine → YouTube Playback Tab on venue laptop.
The laptop page polls/subscribes to these via WebSocket.
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class PlaybackCommand(BaseModel):
    __tablename__ = "playback_commands"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    queue_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queue_entries.id"), nullable=False)
    youtube_video_id: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # 'play' | 'stop' | 'pause'
    # Status: 'pending' | 'acknowledged' | 'playing' | 'completed' | 'failed' | 'stalled'
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
