"""tests/fixtures/sessions.py — Test data factories for table sessions"""
import uuid
from datetime import datetime, timedelta, timezone
from app.models.session import TableSession


def make_session(venue_id: uuid.UUID, table_number: str = "7", **kwargs) -> TableSession:
    defaults = dict(
        venue_id=venue_id,
        table_number=table_number,
        table_code="482176",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        is_active=True,
    )
    defaults.update(kwargs)
    return TableSession(**defaults)
