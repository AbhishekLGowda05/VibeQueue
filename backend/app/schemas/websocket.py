"""app/schemas/websocket.py — WebSocket message shapes"""
from typing import Any, Literal
from pydantic import BaseModel


class WSMessage(BaseModel):
    type: Literal[
        "queue_update",
        "playback_started",
        "playback_ended",
        "playback_error",
        "venue_paused",
        "venue_resumed",
        "song_removed",
        "boost_applied",
        "session_expired",
    ]
    data: dict[str, Any]
