"""
app/api/v1/routes/payments.py

Payment endpoints.

POST /payments/create-order  — creates Razorpay order after guest confirms billing
POST /payments/verify        — webhook from Razorpay after payment succeeds
POST /payments/cash          — staff marks payment collected in cash (fallback)
"""
import hashlib
import hmac
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_staff
from app.api.v1.dependencies.session import get_guest_session
from app.core.config import settings
from app.core.database import get_db
from app.exceptions.payment import PaymentVerificationError
from app.models.session import TableSession
from app.models.user import User
from app.repositories.boost_repo import BoostRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.payment import PaymentOrderResponse, PaymentVerify
from app.services.billing_service import BillingService, GST_RATE
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("/create-order", response_model=PaymentOrderResponse)
async def create_payment_order(
    guest_session: TableSession = Depends(get_guest_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Called after guest reviews and confirms their billing summary.
    Creates a Razorpay order for the confirmed boost total + GST.
    Returns order details for the frontend to open the Razorpay checkout.
    """
    billing = BillingService(
        boost_repo=BoostRepository(db),
        session_repo=SessionRepository(db),
        payment_repo=PaymentRepository(db),
        db=db,
    )
    totals = await billing.calculate_total(guest_session.id)

    if totals["total_paise"] == 0:
        raise HTTPException(status_code=400, detail={"code": "ZERO_AMOUNT", "message": "No confirmed charges to pay."})

    payment_service = PaymentService(payment_repo=PaymentRepository(db), db=db)
    order = await payment_service.create_order(
        venue_id=guest_session.venue_id,
        session_id=guest_session.id,
        total_paise=totals["total_paise"],
        gst_paise=totals["gst_paise"],
    )
    return PaymentOrderResponse(**order)


@router.post("/verify")
async def verify_payment(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Razorpay webhook endpoint.
    NEVER trust frontend — always verify server-side signature here.
    Razorpay sends this after a successful payment.

    Important: This must be registered in Razorpay Dashboard →
    Settings → Webhooks → Add URL: https://api.vibequeue.in/api/v1/payments/verify
    Events to enable: payment.captured
    """
    body = await request.body()
    received_signature = request.headers.get("x-razorpay-signature", "")

    # Verify webhook signature
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, received_signature):
        raise PaymentVerificationError()

    import json
    data = json.loads(body)
    payment_entity = data.get("payload", {}).get("payment", {}).get("entity", {})

    payment_service = PaymentService(payment_repo=PaymentRepository(db), db=db)
    await payment_service.verify_and_confirm(
        razorpay_order_id=payment_entity.get("order_id"),
        razorpay_payment_id=payment_entity.get("id"),
        razorpay_signature=received_signature,
    )
    return {"status": "ok"}


@router.post("/cash/{session_id}")
async def mark_cash_payment(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    """
    Fallback: waiter marks that the guest paid music charges in cash.
    Records the payment without going through Razorpay.
    """
    payment_repo = PaymentRepository(db)
    payment = await payment_repo.get_by_session(session_id)
    if payment:
        await payment_repo.update(payment, status="cash_collected")
    return {"status": "cash_collected", "session_id": str(session_id)}
