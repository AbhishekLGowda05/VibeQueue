"""app/api/v1/routes/billing.py

Pre-billing review and confirmation endpoints.
Called when the waiter is preparing the table's bill.

Flow:
  1. GET /billing/review/{session_id}  → guest reviews their charges
  2. DELETE /billing/boost/{boost_id}  → guest removes an unplayed song's charge
  3. POST /billing/confirm             → guest confirms, Razorpay order created
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.billing import BillingReview, RemoveBoostRequest

router = APIRouter()


@router.get("/review/{session_id}", response_model=BillingReview)
async def get_billing_review(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all confirmed + pending charges for a table session.
    Guests see this on their phone before the final bill is printed.
    """
    # Implementation: billing_service.get_review(session_id, db)
    pass


@router.delete("/boost/{boost_id}")
async def remove_pending_boost(
    boost_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Guest removes a pending (unplayed) boost before billing confirmation.
    Only pending boosts can be removed — confirmed (played) boosts are final.
    """
    # Implementation: billing_service.remove_boost(boost_id, db)
    pass


@router.post("/confirm")
async def confirm_billing(
    request: RemoveBoostRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Guest confirms the reviewed total. Creates a Razorpay payment order.
    Returns: {razorpay_order_id, amount_paise, razorpay_key_id}
    """
    # Implementation: billing_service.confirm(session_id, db)
    pass
