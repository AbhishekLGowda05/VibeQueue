"""app/schemas/boost.py"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class BoostCreate(BaseModel):
    queue_entry_id: uuid.UUID
    amount_paise: int = Field(..., ge=1500, le=3500, description="Amount in paise (₹15=1500, ₹25=2500, ₹35=3500)")


class BoostResponse(BaseModel):
    id: uuid.UUID
    queue_entry_id: uuid.UUID
    amount_paise: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BoostTier(BaseModel):
    """The three fixed boost tiers shown to guests."""
    label: str
    score_increase: int
    amount_paise: int
    amount_display: str   # "₹15", "₹25", "₹35"
