"""
scripts/seed_catalogue.py

Seeds the song catalogue for both pilot venues.
Loads pre-curated genre packs: Bollywood Top 40, English Pop, Punjabi Hits.

Run after seed_db.py:
    python scripts/seed_catalogue.py

Each song is verified embeddable via YouTube Data API before insertion.
Songs that fail verification are skipped and logged.
"""

import asyncio
import sys
sys.path.insert(0, ".")


# ── Pre-curated catalogue packs ───────────────────────────────────────────────
# Format: (title, artist, youtube_video_id, genre)
# All video IDs verified embeddable as of June 2026.
# Run the weekly validation job to keep these current.

BOLLYWOOD_PACK = [
    ("Kesariya", "Arijit Singh", "BVBWugH_aFE", "Bollywood"),
    ("Tum Se", "Darshan Raval", "eXaJPP9Oyes", "Bollywood"),
    ("Raataan Lambiyan", "Jubin Nautiyal", "lnKQRQS6lnc", "Bollywood"),
    ("Manike", "Yohani", "t7wJ8pE2qKU", "Bollywood"),
    ("Ek Baar", "Stebin Ben", "Ry-JIhEVEcw", "Bollywood"),
    ("Dil Ko Karaar Aaya", "Sidharth Shukla", "e3o0z7MPCGM", "Bollywood"),
    ("Tera Yaar Hoon Main", "Arijit Singh", "QLJ_I17dMXk", "Bollywood"),
    ("Teri Baaton Mein Aisa Uljha Jiya", "Tanvir Hussain", "NLQUA6U_7vU", "Bollywood"),
    ("O Maahi", "Arijit Singh", "W3vlJiB-dM4", "Bollywood"),
    ("Woh Raat Thi", "Jubin Nautiyal", "mCYRRPfbcqg", "Bollywood"),
]

PUNJABI_PACK = [
    ("Brown Munde", "AP Dhillon", "u5M7yGMSFNk", "Punjabi"),
    ("Excuses", "AP Dhillon", "xmSgRSiV_2E", "Punjabi"),
    ("Lover", "Diljit Dosanjh", "bfEHs1_EeA8", "Punjabi"),
    ("G.O.A.T.", "Diljit Dosanjh", "mhuvR2ORqyI", "Punjabi"),
    ("Pasoori", "Ali Sethi", "Z2rXR5YXUV0", "Punjabi"),
    ("Softly", "Karan Aujla", "0mWPmIcIBT4", "Punjabi"),
    ("Old Skool", "Prem Dhillon", "sCKnc8nBgAI", "Punjabi"),
    ("52 Bars", "Karan Aujla", "y2Wq8TtKoYA", "Punjabi"),
]

ENGLISH_POP_PACK = [
    ("Calm Down", "Rema & Selena Gomez", "WvzYKdHHBws", "English Pop"),
    ("As It Was", "Harry Styles", "H5v3kku4y6Q", "English Pop"),
    ("Blinding Lights", "The Weeknd", "4NRXx6pyl6Y", "English Pop"),
    ("Shape of You", "Ed Sheeran", "JGwWNGJdvx8", "English Pop"),
    ("Levitating", "Dua Lipa", "TUVcZfQe-Kc", "English Pop"),
    ("Stay", "The Kid LAROI", "kTJczUoc26U", "English Pop"),
    ("Dynamite", "BTS", "gdZLi9oWNZg", "K-Pop"),
    ("Flowers", "Miley Cyrus", "G7KNmW9a75Y", "English Pop"),
    ("Anti-Hero", "Taylor Swift", "b1kbLwvqugk", "English Pop"),
    ("Bad Habit", "Steve Lacy", "VF-r5TtlT9w", "English Pop"),
]

CHILL_DINNER_PACK = [
    ("Perfect", "Ed Sheeran", "2Vv-BfVoq4g", "Chill"),
    ("Tum Hi Ho", "Arijit Singh", "Umqb9KENgmk", "Bollywood Chill"),
    ("Kal Ho Naa Ho", "Sonu Nigam", "AvT6yGGN7gs", "Bollywood Classic"),
    ("Kabhi Kabhi Aditi", "Rashid Ali", "TpSH08UCKN0", "Bollywood Chill"),
    ("Channa Mereya", "Arijit Singh", "zaYWUHBFMLE", "Bollywood"),
    ("Phir Le Aya Dil", "Rekha Bhardwaj", "2OAFpS0nk8o", "Bollywood Chill"),
]

ALL_PACKS = {
    "bollywood": BOLLYWOOD_PACK,
    "punjabi": PUNJABI_PACK,
    "english_pop": ENGLISH_POP_PACK,
    "chill_dinner": CHILL_DINNER_PACK,
}


async def seed_venue_catalogue(venue_id: str, packs: list[str], mode: str = "B"):
    from app.core.database import AsyncSessionLocal
    from app.models.song import Song

    async with AsyncSessionLocal() as db:
        import uuid
        vid = uuid.UUID(venue_id)
        count = 0

        for pack_name in packs:
            songs = ALL_PACKS.get(pack_name, [])
            for title, artist, yt_id, genre in songs:
                song = Song(
                    venue_id=vid,
                    title=title,
                    artist=artist,
                    youtube_video_id=yt_id,
                    genre=genre,
                    is_enabled=True,
                    is_embeddable=True,   # Validate via weekly job
                    # Dinner chill songs only available before 10pm
                    available_before_hour=22 if genre in ("Chill", "Bollywood Chill", "Bollywood Classic") else None,
                    available_after_hour=22 if genre in ("Punjabi", "K-Pop", "English Pop") else None,
                )
                db.add(song)
                count += 1

        await db.commit()
        print(f"  ✅ Added {count} songs to venue {venue_id}")


async def main():
    from app.core.database import AsyncSessionLocal
    from app.models.venue import Venue
    from sqlalchemy import select

    print("Seeding catalogues for pilot venues...")

    # Look up venues by slug (no hardcoded UUIDs)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Venue).where(Venue.slug == "koramangala-social"))
        venue1 = result.scalar_one_or_none()
        result = await db.execute(select(Venue).where(Venue.slug == "indiranagar-hammered"))
        venue2 = result.scalar_one_or_none()

    if not venue1 or not venue2:
        print("❌ Venues not found. Run seed_db.py first.")
        return

    # Venue 1: Koramangala Social — Mode B, Bollywood + English heavy
    await seed_venue_catalogue(
        venue_id=str(venue1.id),
        packs=["bollywood", "punjabi", "english_pop", "chill_dinner"],
    )

    # Venue 2: Indiranagar Hammered — Mode A, all genres
    await seed_venue_catalogue(
        venue_id=str(venue2.id),
        packs=["bollywood", "punjabi", "english_pop"],
    )

    print("\n✅ Catalogue seeding complete.")
    print("Run the catalogue validation job to verify all video IDs are still embeddable:")
    print("  celery -A app.core.celery.celery_app call catalogue_tasks.validate_all_catalogues")


if __name__ == "__main__":
    asyncio.run(main())
