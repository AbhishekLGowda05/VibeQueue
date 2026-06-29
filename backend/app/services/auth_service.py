"""app/services/auth_service.py"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import hash_password
from app.models.user import User
from app.repositories.base import BaseRepository
import uuid


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self,
        email: str,
        password: str,
        role: str,
        venue_id: uuid.UUID = None,
        full_name: str = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            venue_id=venue_id,
            full_name=full_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
