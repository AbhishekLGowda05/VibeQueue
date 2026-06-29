"""
app/models/audit_log.py
Immutable record of important actions. Never updated, only appended.
Used for billing disputes, legal compliance, and debugging.
"""
import uuid
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=True)  # user_id or 'system'
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Examples: 'boost.created' | 'boost.confirmed' | 'boost.cancelled'
    #           'song.played' | 'queue.paused' | 'session.opened' | 'payment.confirmed'
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)   # JSON string
