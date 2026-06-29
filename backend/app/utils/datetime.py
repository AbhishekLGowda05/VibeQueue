"""app/utils/datetime.py — Timezone-aware datetime helpers"""
from datetime import datetime, timezone
import pytz

IST = pytz.timezone("Asia/Kolkata")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_ist() -> datetime:
    return datetime.now(IST)


def to_ist(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def ist_hour() -> int:
    """Current hour in IST (0–23). Used for time-of-day song pool filtering."""
    return now_ist().hour
