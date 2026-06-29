"""
scripts/create_venue.py

Interactive CLI script to create a new venue.
Run when onboarding a new venue during setup session.

Usage:
    python scripts/create_venue.py
"""

import asyncio
import sys
sys.path.insert(0, ".")


async def main():
    print("VibeQueue — Create New Venue")
    print("=" * 40)

    name = input("Venue name: ").strip()
    slug = input("Slug (e.g. social-koramangala): ").strip().lower().replace(" ", "-")
    city = input("City [Bengaluru]: ").strip() or "Bengaluru"
    mode = input("Mode (A=YouTube auto / B=Manual) [B]: ").strip().upper() or "B"
    spend_cap = input("Spend cap per table in ₹ [150]: ").strip() or "150"
    owner_email = input("Owner email: ").strip()
    owner_name = input("Owner name: ").strip()
    owner_password = input("Owner password (they will change this): ").strip()
    whatsapp = input("Owner WhatsApp number (with country code, e.g. 919876543210): ").strip()

    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.venue import Venue
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        venue = Venue(
            name=name,
            slug=slug,
            city=city,
            mode=mode,
            is_active=True,
            spend_cap_paise=int(spend_cap) * 100,
            queue_size_limit=8,
            request_cooldown_seconds=180,
            whatsapp_number=whatsapp,
        )
        db.add(venue)
        await db.flush()

        owner = User(
            email=owner_email,
            hashed_password=hash_password(owner_password),
            full_name=owner_name,
            role="venue_owner",
            venue_id=venue.id,
        )
        db.add(owner)
        await db.commit()

        print(f"\n✅ Venue created successfully!")
        print(f"   Venue ID: {venue.id}")
        print(f"   Slug:     {venue.slug}")
        print(f"   Mode:     {venue.mode}")
        print(f"   QR URL:   https://app.vibequeue.in/{venue.slug}")
        print(f"\n⚠️  Next steps:")
        print(f"   1. Run: python scripts/seed_catalogue.py (update venue_id to {venue.id})")
        print(f"   2. Run: python scripts/validate_youtube_ids.py")
        print(f"   3. Tell the owner to change their password at first login")


if __name__ == "__main__":
    asyncio.run(main())
