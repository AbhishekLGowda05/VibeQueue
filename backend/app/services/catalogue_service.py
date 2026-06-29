"""app/services/catalogue_service.py — Catalogue validation against YouTube Data API"""
import structlog
from googleapiclient.discovery import build
from app.core.config import settings

logger = structlog.get_logger()

_youtube = None


def get_youtube_client():
    global _youtube
    if _youtube is None:
        _youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
    return _youtube


def check_videos_embeddable(video_ids: list[str]) -> dict[str, bool]:
    """
    Batch-check up to 50 video IDs for embeddability.
    Returns {video_id: is_embeddable} dict.
    Costs 1 quota unit per API call (up to 50 IDs per call).
    """
    if not video_ids:
        return {}

    youtube = get_youtube_client()
    results = {}

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        response = youtube.videos().list(
            part="status",
            id=",".join(batch),
        ).execute()

        found_ids = set()
        for item in response.get("items", []):
            vid_id = item["id"]
            status = item.get("status", {})
            embeddable = (
                status.get("embeddable", False)
                and status.get("privacyStatus") == "public"
            )
            results[vid_id] = embeddable
            found_ids.add(vid_id)

        # Videos not returned by the API have been deleted or made private
        for vid_id in batch:
            if vid_id not in found_ids:
                results[vid_id] = False
                logger.warning("catalogue.video_missing", video_id=vid_id)

    return results
