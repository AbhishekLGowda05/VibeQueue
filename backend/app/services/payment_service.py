"""
app/services/payment_service.py

Creates Razorpay orders and verifies payment webhooks.
CRITICAL: Never trust the frontend for payment confirmation.
Always verify the Razorpay signature server-side before marking paid.
"""
import uuid
import razorpay
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import verify_razorpay_signature
from app.exceptions.payment import PaymentVerificationError
from app.repositories.payment_repo import PaymentRepository

logger = structlog.get_logger()

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

VIBEQUEUE_SHARE = 0.40   # VibeQueue takes 40%
VENUE_SHARE = 0.60


class PaymentService:
    def __init__(self, payment_repo: PaymentRepository, db: AsyncSession):
        self.payment_repo = payment_repo
        self.db = db

    async def create_order(
        self,
        venue_id: uuid.UUID,
        session_id: uuid.UUID,
        total_paise: int,
        gst_paise: int,
    ) -> dict:
        """Create a Razorpay order for the table's music charges."""
        order = razorpay_client.order.create({
            "amount": total_paise,
            "currency": "INR",
            "receipt": str(session_id)[:40],
            "notes": {
                "venue_id": str(venue_id),
                "session_id": str(session_id),
                "type": "vibequeue_music_charges",
            }
        })
        await self.payment_repo.create(
            venue_id=venue_id,
            session_id=session_id,
            razorpay_order_id=order["id"],
            total_amount_paise=total_paise,
            gst_amount_paise=gst_paise,
            status="created",
            vibequeue_share_paise=int((total_paise - gst_paise) * VIBEQUEUE_SHARE),
            venue_share_paise=int((total_paise - gst_paise) * VENUE_SHARE),
        )
        logger.info("payment.order_created", order_id=order["id"], amount=total_paise)
        return {
            "razorpay_order_id": order["id"],
            "amount_paise": total_paise,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        }

    async def verify_and_confirm(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> None:
        """
        Called from the Razorpay webhook (NOT from frontend).
        Verifies signature, marks payment as paid.
        """
        is_valid = verify_razorpay_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        )
        if not is_valid:
            logger.error("payment.signature_invalid", order_id=razorpay_order_id)
            raise PaymentVerificationError()

        payment = await self.payment_repo.get_by_razorpay_order(razorpay_order_id)
        if payment:
            from datetime import datetime, timezone
            await self.payment_repo.update(
                payment,
                status="paid",
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                paid_at=datetime.now(timezone.utc),
            )
        logger.info("payment.confirmed", order_id=razorpay_order_id)
