"""
app/api/v1/dependencies/auth.py

FastAPI dependencies for authentication and role-based access control.
Inject these into route functions to protect endpoints.

Usage:
    @router.get("/")
    async def my_route(current_user: User = Depends(get_current_venue_owner)):
        ...
"""
import uuid
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.exceptions.auth import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.repositories.venue_repo import VenueRepository
from sqlalchemy import select

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the JWT from Authorization header. Returns the User."""
    if not credentials:
        raise UnauthorizedError("Missing Authorization header")
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token payload")
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


async def get_current_venue_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    """Requires venue_owner or superadmin role."""
    if current_user.role not in ("venue_owner", "superadmin"):
        raise ForbiddenError("Venue owner access required")
    return current_user


async def get_current_staff(
    current_user: User = Depends(get_current_user),
) -> User:
    """Requires any venue role (owner or staff)."""
    if current_user.role not in ("venue_owner", "venue_staff", "superadmin"):
        raise ForbiddenError("Venue staff access required")
    return current_user


async def get_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Requires superadmin role — VibeQueue internal use only."""
    if current_user.role != "superadmin":
        raise ForbiddenError("Superadmin access required")
    return current_user
