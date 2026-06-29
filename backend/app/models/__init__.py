"""
app/models/__init__.py

Import all models here so:
1. Alembic auto-detects them for migrations
2. SQLAlchemy registers all relationships correctly
"""
from app.models.base import BaseModel
from app.models.venue import Venue
from app.models.user import User
from app.models.song import Song
from app.models.session import TableSession
from app.models.queue import QueueEntry
from app.models.boost import Boost
from app.models.payment import Payment
from app.models.playback_command import PlaybackCommand
from app.models.playback_event import PlaybackEvent
from app.models.audit_log import AuditLog

__all__ = [
    "BaseModel", "Venue", "User", "Song", "TableSession",
    "QueueEntry", "Boost", "Payment", "PlaybackCommand",
    "PlaybackEvent", "AuditLog",
]
