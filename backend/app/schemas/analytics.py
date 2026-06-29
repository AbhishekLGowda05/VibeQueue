"""app/schemas/analytics.py"""
import uuid
from datetime import date
from pydantic import BaseModel


class WeeklyReport(BaseModel):
    venue_id: uuid.UUID
    venue_name: str
    week_start: date
    week_end: date
    total_songs_requested: int
    total_boosts_purchased: int
    total_revenue_paise: int
    total_revenue_display: str
    vibequeue_share_paise: int
    venue_share_paise: int
    boost_conversion_rate: float
    top_genres: list[str]
    peak_hour: int | None
    avg_table_dwell_minutes: float | None
