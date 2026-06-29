"""app/exceptions/queue.py — Domain exceptions for queue operations"""
from fastapi import HTTPException, status


class CooldownActiveError(HTTPException):
    def __init__(self, retry_after_seconds: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "COOLDOWN_ACTIVE",
                "message": f"Please wait {retry_after_seconds}s before requesting another song.",
                "retry_after": retry_after_seconds,
            },
        )

class SpendCapExceededError(HTTPException):
    def __init__(self, current_spend_paise: int, cap_paise: int):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "SPEND_CAP_EXCEEDED",
                "message": f"Table spend limit reached (₹{cap_paise//100}).",
                "current_spend_paise": current_spend_paise,
                "cap_paise": cap_paise,
            },
        )

class QueueSongNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "QUEUE_ENTRY_NOT_FOUND", "message": "Song not found in queue."},
        )

class WaitingPoolBoostError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "WAITING_POOL_BOOST_NOT_ALLOWED",
                "message": "Boost is available once your song enters the live queue.",
            },
        )

class QueueFullError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "QUEUE_FULL", "message": "The queue is currently full."},
        )
