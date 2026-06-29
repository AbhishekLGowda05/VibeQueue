"""app/schemas/venue.py"""
import uuid
from pydantic import BaseModel


class VenuePublic(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    mode: str
    queue_size_limit: int
    spend_cap_paise: int
    spend_cap_display: str

    model_config = {"from_attributes": True}


class VenueConfig(BaseModel):
    """Sent to venue dashboard on load."""
    id: uuid.UUID
    name: str
    slug: str
    mode: str
    queue_size_limit: int
    spend_cap_paise: int
    request_cooldown_seconds: int
    is_active: bool

    model_config = {"from_attributes": True}
