"""
app/api/v1/dependencies/session.py

Validates a guest's session token and returns the active TableSession.
Used in all guest-facing routes (queue, boosts, billing review).
"""
import uuid
from fastapi import Depends
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.exceptions.session import InvalidTableCodeError, SessionExpiredError
from app.models.session import TableSession
from app.repositories.session_repo import SessionRepository
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


async def get_guest_session(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> TableSession:
    """
    Validates the guest JWT and returns the active TableSession.
    Guest tokens contain: sub=session_id, role='guest', venue_id.
    """
    if not credentials:
        raise InvalidTableCodeError()
    try:
        payload = decode_token(credentials.credentials)
        session_id = payload.get("sub")
        role = payload.get("role")
        if role != "guest" or not session_id:
            raise InvalidTableCodeError()
    except JWTError:
        raise SessionExpiredError()

    repo = SessionRepository(db)
    session = await repo.get_by_id(uuid.UUID(session_id))
    if not session or not session.is_active:
        raise SessionExpiredError()

    from datetime import datetime, timezone
    if session.expires_at < datetime.now(timezone.utc):
        raise SessionExpiredError()

    return session
