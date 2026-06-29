"""
app/api/v1/dependencies/venue.py

Loads and validates a venue from slug or id path parameter.
"""
import uuid
from fastapi import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.venue import VenueInactiveError, VenueNotFoundError
from app.models.venue import Venue
from app.repositories.venue_repo import VenueRepository


async def get_venue_by_slug(
    slug: str = Path(...),
    db: AsyncSession = Depends(get_db),
) -> Venue:
    repo = VenueRepository(db)
    venue = await repo.get_by_slug(slug)
    if not venue:
        raise VenueNotFoundError()
    if not venue.is_active:
        raise VenueInactiveError()
    return venue


async def get_venue_by_id(
    venue_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> Venue:
    repo = VenueRepository(db)
    venue = await repo.get_by_id(venue_id)
    if not venue:
        raise VenueNotFoundError()
    return venue
