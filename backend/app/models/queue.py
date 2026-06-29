"""
app/models/queue.py — Songs in the queue (active + waiting pool)
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class QueueEntry(BaseModel):
    __tablename__ = "queue_entries"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("table_sessions.id"), nullable=False)
    song_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("songs.id"), nullable=False)
    youtube_video_id: Mapped[str] = mapped_column(String(20), nullable=False)

    # Status lifecycle: 'active' → 'playing' → 'played' | 'skipped' | 'expired' | 'cancelled'
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)

    # Position: 1–8 = active queue, 9+ = waiting pool
    position: Mapped[int] = mapped_column(Integer, nullable=True)

    # Scoring
    boost_total_paise: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["TableSession"] = relationship("TableSession", back_populates="queue_entries")
    boosts: Mapped[list["Boost"]] = relationship("Boost", back_populates="queue_entry")
