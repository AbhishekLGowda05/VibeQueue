"""app/schemas/song.py"""
import uuid
from pydantic import BaseModel


class SongSearch(BaseModel):
    id: uuid.UUID
    title: str
    artist: str
    youtube_video_id: str
    genre: str | None = None
    duration_seconds: int | None = None

    model_config = {"from_attributes": True}


class SongCatalogueUpdate(BaseModel):
    youtube_video_id: str
    title: str
    artist: str
    genre: str | None = None
    is_enabled: bool = True
    available_after_hour: int | None = None
    available_before_hour: int | None = None
