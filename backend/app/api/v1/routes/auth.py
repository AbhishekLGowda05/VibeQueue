"""
app/api/v1/routes/auth.py

Authentication endpoints for venue owners and staff.
Guests do not use this — they authenticate via table code (sessions route).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_password, decode_token
from app.exceptions.auth import UnauthorizedError
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Venue owner / staff login.
    Returns access token (60 min) + refresh token (30 days).
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role,
        extra={"venue_id": str(user.venue_id) if user.venue_id else None},
    )
    refresh_token = create_refresh_token(subject=str(user.id), role=user.role)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise UnauthorizedError("Not a refresh token")
    except Exception:
        raise UnauthorizedError("Invalid or expired refresh token")

    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(data["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found")

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role,
        extra={"venue_id": str(user.venue_id) if user.venue_id else None},
    )
    new_refresh = create_refresh_token(subject=str(user.id), role=user.role)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout")
async def logout():
    """
    Client-side logout — client discards the tokens.
    Token blacklisting is a post-pilot enhancement (add Redis set of revoked JTIs).
    """
    return {"message": "Logged out successfully"}
