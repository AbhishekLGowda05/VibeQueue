"""
app/models/song.py — Venue song catalogue
Each row is one approved song for one venue.
"""
import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Song(BaseModel):
    __tablename__ = "songs"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    youtube_video_id: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    artist: Mapped[str] = mapped_column(String(200), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_embeddable: Mapped[bool] = mapped_column(Boolean, default=True)
    # available_after_hour: null means always available, 22 means after 10pm
    available_after_hour: Mapped[int] = mapped_column(Integer, nullable=True)
    available_before_hour: Mapped[int] = mapped_column(Integer, nullable=True)

    venue: Mapped["Venue"] = relationship("Venue", back_populates="songs")
