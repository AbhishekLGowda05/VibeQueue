"""app/repositories/audit_repo.py"""
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(AuditLog, db)

    async def log(
        self,
        action: str,
        venue_id: uuid.UUID = None,
        session_id: uuid.UUID = None,
        actor_id: str = "system",
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
    ) -> AuditLog:
        """Append-only audit record. Call this after every significant action."""
        return await self.create(
            action=action,
            venue_id=venue_id,
            session_id=session_id,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=json.dumps(details) if details else None,
        )
