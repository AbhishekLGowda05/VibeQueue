"""
app/models/user.py — Venue owner / staff accounts
"""
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
import uuid


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="venue_staff")
    # role: 'venue_owner' | 'venue_staff' | 'superadmin'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    venue: Mapped["Venue"] = relationship("Venue", back_populates="users")
