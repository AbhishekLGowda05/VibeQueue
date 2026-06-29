"""app/schemas/session.py"""
import uuid
from datetime import datetime
from pydantic import BaseModel


class TableSessionCreate(BaseModel):
    table_number: str
    venue_id: uuid.UUID


class TableSessionResponse(BaseModel):
    id: uuid.UUID
    table_number: str
    table_code: str
    expires_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class GuestJoinRequest(BaseModel):
    table_code: str


class GuestJoinResponse(BaseModel):
    session_id: uuid.UUID
    table_number: str
    access_token: str
    expires_at: datetime
    spend_cap_paise: int
    spend_cap_display: str
    venue_name: str
