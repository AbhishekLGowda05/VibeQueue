"""
app/models/venue.py — Venue configuration and ownership
"""
import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Venue(BaseModel):
    __tablename__ = "venues"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Bengaluru")
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    whatsapp_number: Mapped[str] = mapped_column(String(20), nullable=True)

    # ── Business Logic Config ─────────────────────────────────────────
    queue_size_limit: Mapped[int] = mapped_column(Integer, default=8)
    spend_cap_paise: Mapped[int] = mapped_column(Integer, default=15000)   # ₹150
    request_cooldown_seconds: Mapped[int] = mapped_column(Integer, default=180)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)        # Flipped at setup
    mode: Mapped[str] = mapped_column(String(10), default="B")             # 'A' or 'B'

    # ── Relationships ─────────────────────────────────────────────────
    songs: Mapped[list["Song"]] = relationship("Song", back_populates="venue")
    sessions: Mapped[list["TableSession"]] = relationship("TableSession", back_populates="venue")
    users: Mapped[list["User"]] = relationship("User", back_populates="venue")
