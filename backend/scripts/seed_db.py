"""
scripts/seed_db.py

Creates the two pilot venues in the database.
Run once after initial migration:
    python scripts/seed_db.py

Creates:
  - Venue 1: koramangala-social (Mode B, default)
  - Venue 2: indiranagar-hammered (Mode A, YouTube IFrame)
  - One venue_owner account per venue
"""

import asyncio
import sys
sys.path.insert(0, ".")

async def main():
    from app.core.database import AsyncSessionLocal, engine, Base
    from app.core.security import hash_password
    from app.models.venue import Venue
    from app.models.user import User

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Pilot Venue 1
        venue1 = Venue(
            name="Social Koramangala",
            slug="koramangala-social",
            city="Bengaluru",
            mode="B",
            is_active=True,
            queue_size_limit=8,
            spend_cap_paise=15000,
            request_cooldown_seconds=180,
        )
        db.add(venue1)
        await db.flush()

        owner1 = User(
            email="owner@koramangala-social.com",
            hashed_password=hash_password("changeme123"),
            role="venue_owner",
            venue_id=venue1.id,
            full_name="Venue Owner 1",
        )
        db.add(owner1)

        # Pilot Venue 2
        venue2 = Venue(
            name="Hammered Indiranagar",
            slug="indiranagar-hammered",
            city="Bengaluru",
            mode="A",
            is_active=True,
            queue_size_limit=8,
            spend_cap_paise=15000,
            request_cooldown_seconds=180,
        )
        db.add(venue2)
        await db.flush()

        owner2 = User(
            email="owner@indiranagar-hammered.com",
            hashed_password=hash_password("changeme123"),
            role="venue_owner",
            venue_id=venue2.id,
            full_name="Venue Owner 2",
        )
        db.add(owner2)
        await db.commit()

        print(f"✅ Created venue: {venue1.slug} (id: {venue1.id})")
        print(f"✅ Created venue: {venue2.slug} (id: {venue2.id})")
        print("⚠️  Change default passwords before going live!")

if __name__ == "__main__":
    asyncio.run(main())
