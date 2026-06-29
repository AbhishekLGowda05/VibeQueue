"""
app/models/session.py — Table session (one session per table per evening)
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class TableSession(BaseModel):
    __tablename__ = "table_sessions"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    table_number: Mapped[str] = mapped_column(String(20), nullable=False)
    table_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_billed: Mapped[bool] = mapped_column(Boolean, default=False)
    opened_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    venue: Mapped["Venue"] = relationship("Venue", back_populates="sessions")
    queue_entries: Mapped[list["QueueEntry"]] = relationship("QueueEntry", back_populates="session")
    boosts: Mapped[list["Boost"]] = relationship("Boost", back_populates="session")
