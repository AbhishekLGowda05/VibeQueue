"""
app/services/billing_service.py

Handles the pre-billing review flow and final bill confirmation.
This is the most trust-critical service in VibeQueue.

The three rules that make billing disputes structurally impossible:
  1. A charge is only CONFIRMED after a PLAYED playback event fires.
  2. Guests review ALL charges before any payment order is created.
  3. Pending (unplayed) charges can be removed by the guest at review time.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.boost_repo import BoostRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.payment_repo import PaymentRepository
from app.schemas.billing import BillingReview, BillingLineItem
import structlog

logger = structlog.get_logger()

GST_RATE = 0.18   # 18%
PAISE_PER_RUPEE = 100


class BillingService:
    def __init__(
        self,
        boost_repo: BoostRepository,
        session_repo: SessionRepository,
        payment_repo: PaymentRepository,
        db: AsyncSession,
    ):
        self.boost_repo = boost_repo
        self.session_repo = session_repo
        self.payment_repo = payment_repo
        self.db = db

    async def get_review(self, session_id: uuid.UUID) -> BillingReview:
        """
        Build the pre-billing review for a table session.
        Shows: confirmed boosts (charged) + pending boosts (removable).
        """
        session = await self.session_repo.get_by_id(session_id)
        boosts = await self.boost_repo.get_by_session(session_id)

        items = []
        subtotal = 0

        for boost in boosts:
            if boost.status == "cancelled":
                continue   # Already cancelled — don't show

            is_removable = boost.status == "pending"
            if boost.status == "confirmed":
                subtotal += boost.amount_paise

            items.append(BillingLineItem(
                boost_id=boost.id,
                queue_entry_id=boost.queue_entry_id,
                song_title="",    # Joined from song table in full implementation
                artist="",
                amount_paise=boost.amount_paise,
                amount_display=f"₹{boost.amount_paise // PAISE_PER_RUPEE}",
                status=boost.status,
                is_removable=is_removable,
            ))

        gst = int(subtotal * GST_RATE)
        total = subtotal + gst

        return BillingReview(
            session_id=session_id,
            table_number=session.table_number,
            items=items,
            subtotal_paise=subtotal,
            gst_paise=gst,
            total_paise=total,
            subtotal_display=f"₹{subtotal // PAISE_PER_RUPEE}",
            gst_display=f"₹{gst // PAISE_PER_RUPEE}",
            total_display=f"₹{total // PAISE_PER_RUPEE}",
        )

    async def remove_boost(self, boost_id: uuid.UUID) -> None:
        """Guest removes a pending charge before confirmation. Only pending allowed."""
        boost = await self.boost_repo.get_by_id(boost_id)
        if not boost or boost.status != "pending":
            return   # Silently ignore — can't remove confirmed charges
        await self.boost_repo.update(boost, status="cancelled")
        logger.info("billing.boost_removed", boost_id=str(boost_id))

    async def calculate_total(self, session_id: uuid.UUID) -> dict:
        """Calculate final totals after guest has reviewed and removed any items."""
        confirmed_total = await self.boost_repo.sum_confirmed_paise(session_id)
        gst = int(confirmed_total * GST_RATE)
        return {
            "subtotal_paise": confirmed_total,
            "gst_paise": gst,
            "total_paise": confirmed_total + gst,
        }
