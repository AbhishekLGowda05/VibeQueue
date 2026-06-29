"""app/exceptions/playback.py"""
from fastapi import HTTPException, status

class PlaybackCommandNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLAYBACK_COMMAND_NOT_FOUND", "message": "Playback command not found."},
        )
