"""app/utils/validators.py — Input validation helpers"""
import re


def is_valid_youtube_video_id(video_id: str) -> bool:
    """YouTube video IDs are exactly 11 alphanumeric characters (plus - and _)."""
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))


def is_valid_phone_number(phone: str) -> bool:
    """Basic Indian phone number validation (10 digits, optionally prefixed with +91)."""
    cleaned = phone.replace("+91", "").replace(" ", "").replace("-", "")
    return bool(re.match(r'^\d{10}$', cleaned))


def sanitize_table_number(table_number: str) -> str:
    """Normalize table number to uppercase string."""
    return table_number.strip().upper()
