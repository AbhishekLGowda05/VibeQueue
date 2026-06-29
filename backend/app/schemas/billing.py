"""app/schemas/billing.py — Pre-billing review schemas"""
import uuid
from pydantic import BaseModel


class BillingLineItem(BaseModel):
    boost_id: uuid.UUID
    queue_entry_id: uuid.UUID
    song_title: str
    artist: str
    amount_paise: int
    amount_display: str
    status: str          # 'confirmed' (played) | 'pending' (still in queue)
    is_removable: bool   # True only for pending items


class BillingReview(BaseModel):
    """Shown on guest's phone before final bill confirmation."""
    session_id: uuid.UUID
    table_number: str
    items: list[BillingLineItem]
    subtotal_paise: int
    gst_paise: int
    total_paise: int
    subtotal_display: str
    gst_display: str
    total_display: str


class RemoveBoostRequest(BaseModel):
    boost_id: uuid.UUID


class ConfirmBillingRequest(BaseModel):
    session_id: uuid.UUID
