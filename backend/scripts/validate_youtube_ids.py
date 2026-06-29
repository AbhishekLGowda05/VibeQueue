"""
scripts/validate_youtube_ids.py

One-shot manual validation of all YouTube video IDs in the catalogue.
Run this before the pilot goes live to confirm every song is embeddable.

Usage:
    python scripts/validate_youtube_ids.py
    python scripts/validate_youtube_ids.py --venue-id <uuid>  # single venue
"""

import asyncio
import sys
sys.path.insert(0, ".")


async def validate_all():
    from app.core.database import AsyncSessionLocal
    from app.models.song import Song
    from app.services.catalogue_service import check_videos_embeddable
    from sqlalchemy import select, update

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Song).where(Song.is_enabled == True))
        songs = list(result.scalars().all())

        print(f"Checking {len(songs)} songs across all venues...")

        video_ids = [s.youtube_video_id for s in songs]
        embeddability = check_videos_embeddable(video_ids)

        broken = []
        for song in songs:
            is_ok = embeddability.get(song.youtube_video_id, False)
            if not is_ok:
                broken.append(song)
                await db.execute(
                    update(Song).where(Song.id == song.id)
                    .values(is_embeddable=False)
                )
                print(f"  ❌ BROKEN: {song.title} — {song.artist} ({song.youtube_video_id})")
            else:
                await db.execute(
                    update(Song).where(Song.id == song.id)
                    .values(is_embeddable=True)
                )

        await db.commit()

        print(f"\n{'='*50}")
        print(f"Total songs checked: {len(songs)}")
        print(f"Embeddable (OK):     {len(songs) - len(broken)}")
        print(f"Broken (FLAGGED):    {len(broken)}")

        if broken:
            print("\n⚠️  Replace these before going live:")
            for s in broken:
                print(f"   {s.title} — {s.artist} | ID: {s.youtube_video_id}")


if __name__ == "__main__":
    asyncio.run(validate_all())
