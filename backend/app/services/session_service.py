"""app/services/session_service.py — Session business logic (thin, most logic is in repo)"""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import generate_table_code
from app.repositories.session_repo import SessionRepository


class SessionService:
    def __init__(self, repo: SessionRepository, db: AsyncSession):
        self.repo = repo
        self.db = db

    async def rotate_code(self, session_id: uuid.UUID) -> str:
        """Generate and apply a new table code for an existing session (90-min rotation)."""
        session = await self.repo.get_by_id(session_id)
        new_code = generate_table_code()
        new_expiry = datetime.now(timezone.utc) + timedelta(seconds=settings.TABLE_CODE_EXPIRY_SECONDS)
        await self.repo.update(session, table_code=new_code, expires_at=new_expiry)
        return new_code
