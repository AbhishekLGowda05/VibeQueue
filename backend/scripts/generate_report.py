"""
scripts/generate_report.py

Manually generate a weekly revenue report for a specific venue.
Used to send ad-hoc reports or to debug the analytics calculations.

Usage:
    python scripts/generate_report.py --venue-id <uuid>
    python scripts/generate_report.py --venue-id <uuid> --week-offset 1  (last week)
"""

import asyncio
import sys
sys.path.insert(0, ".")


async def main(venue_id: str, week_offset: int = 0):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import and_, func, select
    from app.core.database import AsyncSessionLocal
    from app.models.boost import Boost
    from app.models.queue import QueueEntry
    from app.models.venue import Venue

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(weeks=week_offset)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=7)

    import uuid
    vid = uuid.UUID(venue_id)

    async with AsyncSessionLocal() as db:
        venue = await db.get(Venue, vid)
        if not venue:
            print(f"❌ Venue {venue_id} not found")
            return

        songs_result = await db.execute(
            select(func.count(QueueEntry.id)).where(
                and_(QueueEntry.venue_id == vid,
                     QueueEntry.created_at >= week_start,
                     QueueEntry.created_at < week_end)
            )
        )
        total_songs = songs_result.scalar() or 0

        revenue_result = await db.execute(
            select(func.sum(Boost.amount_paise)).where(
                and_(Boost.venue_id == vid, Boost.status == "confirmed",
                     Boost.created_at >= week_start, Boost.created_at < week_end)
            )
        )
        total_revenue = revenue_result.scalar() or 0

        boosts_result = await db.execute(
            select(func.count(Boost.id)).where(
                and_(Boost.venue_id == vid, Boost.status == "confirmed",
                     Boost.created_at >= week_start, Boost.created_at < week_end)
            )
        )
        total_boosts = boosts_result.scalar() or 0

        conversion = f"{(total_boosts / total_songs * 100):.1f}%" if total_songs > 0 else "N/A"

        print(f"\n{'='*50}")
        print(f"VibeQueue Weekly Report — {venue.name}")
        print(f"Week: {week_start.date()} → {week_end.date()}")
        print(f"{'='*50}")
        print(f"Songs requested:      {total_songs}")
        print(f"Boosts purchased:     {total_boosts}")
        print(f"Boost conversion:     {conversion}")
        print(f"Total revenue:        ₹{total_revenue // 100}")
        print(f"  → Venue share (60%): ₹{int(total_revenue * 0.60) // 100}")
        print(f"  → VQ share (40%):    ₹{int(total_revenue * 0.40) // 100}")
        print(f"{'='*50}")

        # WhatsApp message template
        print(f"\nWhatsApp message for owner:")
        print(f"---")
        print(f"VibeQueue this week at {venue.name}: {total_songs} songs requested, "
              f"{total_boosts} boosts purchased, ₹{total_revenue // 100} in music revenue "
              f"(₹{int(total_revenue * 0.60) // 100} your share, already transferred). "
              f"Full report in your dashboard.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--venue-id", required=True)
    parser.add_argument("--week-offset", type=int, default=0)
    args = parser.parse_args()
    asyncio.run(main(args.venue_id, args.week_offset))
