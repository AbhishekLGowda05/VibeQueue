"""
app/models/payment.py — Final payment records (after pre-billing review)
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class Payment(BaseModel):
    __tablename__ = "payments"

    venue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("table_sessions.id"), nullable=False, index=True)

    razorpay_order_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    razorpay_payment_id: Mapped[str] = mapped_column(String(100), nullable=True)
    razorpay_signature: Mapped[str] = mapped_column(Text, nullable=True)

    total_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    gst_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    # Status: 'created' | 'paid' | 'failed' | 'cash_collected'
    status: Mapped[str] = mapped_column(String(20), default="created", index=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Settlement tracking (VibeQueue's 40% vs venue's 60%)
    vibequeue_share_paise: Mapped[int] = mapped_column(Integer, nullable=True)
    venue_share_paise: Mapped[int] = mapped_column(Integer, nullable=True)
    settlement_status: Mapped[str] = mapped_column(String(20), default="pending")
