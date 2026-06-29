"""tests/fixtures/venues.py — Test data factories for venues"""
import uuid
from app.models.venue import Venue


def make_venue(**kwargs) -> Venue:
    defaults = dict(
        name="Test Bar Koramangala",
        slug=f"test-bar-{uuid.uuid4().hex[:6]}",
        city="Bengaluru",
        mode="B",
        is_active=True,
        queue_size_limit=8,
        spend_cap_paise=15000,
        request_cooldown_seconds=180,
    )
    defaults.update(kwargs)
    return Venue(**defaults)
