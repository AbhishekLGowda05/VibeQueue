"""
app/api/v1/routes/venues.py

Venue management — create, configure, and retrieve venues.
All write operations require venue_owner or superadmin role.
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_staff, get_current_venue_owner
from app.core.database import get_db
from app.models.user import User
from app.models.venue import Venue
from app.repositories.venue_repo import VenueRepository
from app.schemas.venue import VenueConfig, VenuePublic

router = APIRouter()


@router.get("/{slug}", response_model=VenuePublic)
async def get_venue_public(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Public endpoint — returns venue info for the guest join screen.
    Called when guest opens the QR code URL.
    """
    repo = VenueRepository(db)
    venue = await repo.get_by_slug(slug)
    if not venue or not venue.is_active:
        from app.exceptions.venue import VenueNotFoundError
        raise VenueNotFoundError()
    return VenuePublic(
        id=venue.id,
        name=venue.name,
        slug=venue.slug,
        mode=venue.mode,
        queue_size_limit=venue.queue_size_limit,
        spend_cap_paise=venue.spend_cap_paise,
        spend_cap_display=f"₹{venue.spend_cap_paise // 100}",
    )


@router.get("/{venue_id}/config", response_model=VenueConfig)
async def get_venue_config(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """Staff/owner endpoint — returns full config for the venue dashboard."""
    repo = VenueRepository(db)
    venue = await repo.get_by_id(venue_id)
    if not venue:
        from app.exceptions.venue import VenueNotFoundError
        raise VenueNotFoundError()
    return venue


@router.patch("/{venue_id}/mode")
async def toggle_mode(
    venue_id: uuid.UUID,
    mode: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_venue_owner),
):
    """
    Toggle between Mode A (YouTube automated) and Mode B (manual staff play).
    Venue owners can switch at any time — one toggle.
    """
    if mode not in ("A", "B"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Mode must be 'A' or 'B'")
    repo = VenueRepository(db)
    venue = await repo.get_by_id(venue_id)
    updated = await repo.update(venue, mode=mode)
    return {"venue_id": str(venue_id), "mode": updated.mode}


@router.patch("/{venue_id}/pause")
async def pause_venue(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """
    Emergency pause — stops all guest interaction instantly.
    One tap on the venue dashboard. Broadcasts pause event via WebSocket.
    """
    from app.core.redis import RedisKeys, redis_queue_client
    import json
    channel = RedisKeys.websocket_channel(str(venue_id))
    await redis_queue_client.publish(channel, json.dumps({"type": "venue_paused"}))
    return {"status": "paused"}


@router.patch("/{venue_id}/resume")
async def resume_venue(
    venue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """Resume after a pause."""
    from app.core.redis import RedisKeys, redis_queue_client
    import json
    channel = RedisKeys.websocket_channel(str(venue_id))
    await redis_queue_client.publish(channel, json.dumps({"type": "venue_resumed"}))
    return {"status": "resumed"}
