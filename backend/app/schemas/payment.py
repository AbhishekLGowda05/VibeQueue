"""app/schemas/payment.py"""
import uuid
from datetime import datetime
from pydantic import BaseModel


class PaymentCreate(BaseModel):
    session_id: uuid.UUID
    total_amount_paise: int
    gst_amount_paise: int


class PaymentOrderResponse(BaseModel):
    razorpay_order_id: str
    amount_paise: int
    currency: str = "INR"
    razorpay_key_id: str


class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    id: uuid.UUID
    status: str
    total_amount_paise: int
    paid_at: datetime | None

    model_config = {"from_attributes": True}
