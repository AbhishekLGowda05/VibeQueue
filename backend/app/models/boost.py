"""
app/models/boost.py — Individual boost transactions (pending until song plays)
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Boost(BaseModel):
    __tablename__ = "boosts"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("table_sessions.id"), nullable=False, index=True)
    queue_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queue_entries.id"), nullable=False)

    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    # Status: 'pending' → 'confirmed' (song played) | 'cancelled' (song removed/expired)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["TableSession"] = relationship("TableSession", back_populates="boosts")
    queue_entry: Mapped["QueueEntry"] = relationship("QueueEntry", back_populates="boosts")
