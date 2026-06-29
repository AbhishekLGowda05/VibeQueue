"""
app/api/v1/routes/analytics.py

Analytics and reporting endpoints for venue owners.

GET /analytics/{venue_id}/weekly    — weekly revenue and engagement report
GET /analytics/{venue_id}/tonight   — live tonight's stats (for venue dashboard)
GET /analytics/{venue_id}/songs     — top requested songs this week
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_venue_owner
from app.core.database import get_db
from app.models.boost import Boost
from app.models.queue import QueueEntry
from app.models.user import User

router = APIRouter()


@router.get("/{venue_id}/tonight")
async def tonight_stats(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_venue_owner),
):
    """
    Live stats shown at the bottom of the venue dashboard.
    Updates frequently — called every 30 seconds by the dashboard.
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    # Total confirmed boost revenue tonight
    result = await db.execute(
        select(func.sum(Boost.amount_paise)).where(
            and_(
                Boost.venue_id == venue_id,
                Boost.status == "confirmed",
                Boost.created_at >= today_start,
            )
        )
    )
    total_paise = result.scalar() or 0

    # Total songs requested tonight
    songs_result = await db.execute(
        select(func.count(QueueEntry.id)).where(
            and_(
                QueueEntry.venue_id == venue_id,
                QueueEntry.created_at >= today_start,
            )
        )
    )
    total_songs = songs_result.scalar() or 0

    # Total boosts purchased tonight
    boosts_result = await db.execute(
        select(func.count(Boost.id)).where(
            and_(
                Boost.venue_id == venue_id,
                Boost.created_at >= today_start,
            )
        )
    )
    total_boosts = boosts_result.scalar() or 0

    conversion_rate = (total_boosts / total_songs * 100) if total_songs > 0 else 0

    return {
        "venue_id": str(venue_id),
        "tonight": {
            "total_songs_requested": total_songs,
            "total_boosts_purchased": total_boosts,
            "boost_conversion_rate": round(conversion_rate, 1),
            "total_revenue_paise": total_paise,
            "total_revenue_display": f"₹{total_paise // 100}",
            "vibequeue_share_paise": int(total_paise * 0.40),
            "venue_share_paise": int(total_paise * 0.60),
        }
    }


@router.get("/{venue_id}/weekly")
async def weekly_report(
    venue_id: uuid.UUID,
    week_offset: int = Query(0, ge=0, le=52, description="0 = this week, 1 = last week"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_venue_owner),
):
    """
    Weekly revenue and engagement summary.
    Used to generate the WhatsApp report sent to owners every Sunday.
    """
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(weeks=week_offset)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=7)

    songs_result = await db.execute(
        select(func.count(QueueEntry.id)).where(
            and_(
                QueueEntry.venue_id == venue_id,
                QueueEntry.created_at >= week_start,
                QueueEntry.created_at < week_end,
            )
        )
    )
    total_songs = songs_result.scalar() or 0

    revenue_result = await db.execute(
        select(func.sum(Boost.amount_paise)).where(
            and_(
                Boost.venue_id == venue_id,
                Boost.status == "confirmed",
                Boost.created_at >= week_start,
                Boost.created_at < week_end,
            )
        )
    )
    total_revenue = revenue_result.scalar() or 0

    boosts_result = await db.execute(
        select(func.count(Boost.id)).where(
            and_(
                Boost.venue_id == venue_id,
                Boost.status == "confirmed",
                Boost.created_at >= week_start,
                Boost.created_at < week_end,
            )
        )
    )
    total_boosts = boosts_result.scalar() or 0

    conversion_rate = (total_boosts / total_songs * 100) if total_songs > 0 else 0

    return {
        "venue_id": str(venue_id),
        "week_start": week_start.date().isoformat(),
        "week_end": week_end.date().isoformat(),
        "total_songs_requested": total_songs,
        "total_boosts_purchased": total_boosts,
        "boost_conversion_rate": round(conversion_rate, 1),
        "total_revenue_paise": total_revenue,
        "total_revenue_display": f"₹{total_revenue // 100}",
        "vibequeue_share_paise": int(total_revenue * 0.40),
        "venue_share_paise": int(total_revenue * 0.60),
        "venue_share_display": f"₹{int(total_revenue * 0.60) // 100}",
    }
