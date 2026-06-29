"""app/services/youtube_service.py — YouTube Data API helpers"""
import structlog
from app.services.catalogue_service import get_youtube_client

logger = structlog.get_logger()


def get_video_metadata(video_id: str) -> dict | None:
    """
    Fetch title, channel, duration, and embeddability for a single video.
    Used when a venue owner adds a new song to their catalogue.
    Costs 1 quota unit.
    """
    youtube = get_youtube_client()
    response = youtube.videos().list(
        part="snippet,status,contentDetails",
        id=video_id,
    ).execute()

    items = response.get("items", [])
    if not items:
        return None

    item = items[0]
    snippet = item.get("snippet", {})
    status = item.get("status", {})
    content = item.get("contentDetails", {})

    # Parse ISO 8601 duration (PT3M45S → 225 seconds)
    duration_str = content.get("duration", "PT0S")
    duration_seconds = _parse_duration(duration_str)

    return {
        "video_id": video_id,
        "title": snippet.get("title", "Unknown"),
        "channel": snippet.get("channelTitle", "Unknown"),
        "duration_seconds": duration_seconds,
        "is_embeddable": status.get("embeddable", False),
        "privacy_status": status.get("privacyStatus", "unknown"),
        "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
    }


def _parse_duration(duration: str) -> int:
    """Convert ISO 8601 duration string to seconds. PT3M45S → 225"""
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds
