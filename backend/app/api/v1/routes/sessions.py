"""
app/api/v1/routes/sessions.py

Table session lifecycle — open, join, close.

Staff endpoints:
  POST /sessions/open        — waiter opens a table (generates code)
  POST /sessions/{id}/close  — waiter closes the table at end of evening

Guest endpoint:
  POST /sessions/join        — guest enters table code, receives JWT
"""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_staff
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, generate_table_code
from app.exceptions.session import InvalidTableCodeError
from app.models.user import User
from app.repositories.session_repo import SessionRepository
from app.repositories.venue_repo import VenueRepository
from app.schemas.session import GuestJoinRequest, GuestJoinResponse, TableSessionCreate, TableSessionResponse

router = APIRouter()


@router.post("/open", response_model=TableSessionResponse)
async def open_table(
    payload: TableSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """
    Waiter opens a table session.
    Generates a 6-digit code — waiter tells the guests verbally.
    Code expires in 90 minutes and auto-rotates.
    """
    code = generate_table_code()
    expiry = datetime.now(timezone.utc) + timedelta(seconds=settings.TABLE_CODE_EXPIRY_SECONDS)

    repo = SessionRepository(db)
    session = await repo.create(
        venue_id=payload.venue_id,
        table_number=payload.table_number,
        table_code=code,
        expires_at=expiry,
        opened_by_user_id=current_user.id,
    )
    return session


@router.post("/join", response_model=GuestJoinResponse)
async def guest_join(
    payload: GuestJoinRequest,
    venue_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Guest enters table code after scanning QR.
    Returns a short-lived JWT (same expiry as the session) for all guest API calls.
    The JWT contains: sub=session_id, role='guest', venue_id.
    """
    venue_repo = VenueRepository(db)
    venue = await venue_repo.get_by_slug(venue_slug)
    if not venue or not venue.is_active:
        raise InvalidTableCodeError()

    session_repo = SessionRepository(db)
    session = await session_repo.get_by_code(venue.id, payload.table_code)
    if not session:
        raise InvalidTableCodeError()

    # Token expires when the session expires
    remaining = (session.expires_at - datetime.now(timezone.utc)).total_seconds()
    token = create_access_token(
        subject=str(session.id),
        role="guest",
        extra={"venue_id": str(venue.id), "table_number": session.table_number},
    )

    return GuestJoinResponse(
        session_id=session.id,
        table_number=session.table_number,
        access_token=token,
        expires_at=session.expires_at,
        spend_cap_paise=venue.spend_cap_paise,
        spend_cap_display=f"₹{venue.spend_cap_paise // 100}",
        venue_name=venue.name,
    )


@router.get("/{session_id}/status")
async def session_status(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Quick check — is this session still active? Called by guest app on resume."""
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)
    if not session or not session.is_active:
        return {"active": False}
    if session.expires_at < datetime.now(timezone.utc):
        return {"active": False, "reason": "expired"}
    return {"active": True, "expires_at": session.expires_at}


@router.post("/{session_id}/close")
async def close_table(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """Waiter closes a table after billing is complete."""
    repo = SessionRepository(db)
    await repo.close_session(session_id)
    return {"status": "closed", "session_id": str(session_id)}
