"""
scripts/validate_catalogue.py

One-shot catalogue validation against YouTube Data API v3.
Checks all seeded songs for embeddability and disables any that fail.

Usage:
    cd backend && python scripts/validate_catalogue.py
"""
import sys
import os

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.services.catalogue_service import check_videos_embeddable


def main():
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(url)

    # Fetch all songs from the database
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, youtube_video_id, title, artist FROM songs ORDER BY title"
        ))
        songs = result.fetchall()

    if not songs:
        print("No songs in database.")
        return

    print(f"Validating {len(songs)} songs against YouTube Data API...\n")

    video_ids = [s[1] for s in songs]
    embeddable_map = check_videos_embeddable(video_ids)

    passed = []
    failed = []

    for song_id, video_id, title, artist in songs:
        is_ok = embeddable_map.get(video_id, False)
        if is_ok:
            passed.append((title, artist, video_id))
        else:
            failed.append((song_id, title, artist, video_id))

    # Report results
    print(f"PASSED: {len(passed)}/{len(songs)} songs are embeddable\n")

    if failed:
        print(f"FAILED: {len(failed)} songs are NOT embeddable or unavailable:")
        for song_id, title, artist, video_id in failed:
            print(f"  - {title} by {artist} ({video_id})")

        # Disable failed songs in the database
        print(f"\nDisabling {len(failed)} non-embeddable songs...")
        with engine.begin() as conn:
            for song_id, title, artist, video_id in failed:
                conn.execute(text(
                    "UPDATE songs SET is_embeddable = false, is_enabled = false "
                    "WHERE id = :id"
                ), {"id": str(song_id)})
                print(f"  DISABLED: {title} ({video_id})")
        print("Done.")
    else:
        print("All songs are embeddable. No changes needed.")

    engine.dispose()


if __name__ == "__main__":
    main()
