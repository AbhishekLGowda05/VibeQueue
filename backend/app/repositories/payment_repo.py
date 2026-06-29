"""app/repositories/payment_repo.py"""
import uuid
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)

    async def get_by_razorpay_order(self, order_id: str) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.razorpay_order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_session(self, session_id: uuid.UUID) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_unsettled(self, venue_id: uuid.UUID) -> list[Payment]:
        """Payments collected but not yet settled with VibeQueue."""
        result = await self.db.execute(
            select(Payment).where(
                and_(
                    Payment.venue_id == venue_id,
                    Payment.status == "paid",
                    Payment.settlement_status == "pending",
                )
            )
        )
        return list(result.scalars().all())
