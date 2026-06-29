"""
app/services/notification_service.py

WhatsApp notification sending via Meta Cloud API.
All messages go through pre-approved WhatsApp templates.
Templates must be registered in Meta Business Manager before use.
"""
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()

WHATSAPP_API_URL = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"


async def send_whatsapp_template(
    to_number: str,
    template_name: str,
    language_code: str = "en",
    components: list = None,
) -> bool:
    """
    Send a WhatsApp template message.
    Returns True on success, False on failure (non-blocking — notifications are best-effort).

    Pre-approved templates for VibeQueue:
      - weekly_revenue_report
      - catalogue_warning
      - playback_alert
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }
    if components:
        payload["template"]["components"] = components

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("notification.whatsapp.sent", template=template_name, to=to_number)
            return True
        except Exception as e:
            logger.error("notification.whatsapp.failed", error=str(e), template=template_name)
            return False


async def send_weekly_report(owner_phone: str, venue_name: str, stats: dict) -> bool:
    """Send the Sunday weekly report to a venue owner."""
    components = [{"type": "body", "parameters": [
        {"type": "text", "text": venue_name},
        {"type": "text", "text": str(stats.get("total_songs_requested", 0))},
        {"type": "text", "text": str(stats.get("total_boosts_purchased", 0))},
        {"type": "text", "text": stats.get("venue_share_display", "₹0")},
    ]}]
    return await send_whatsapp_template(owner_phone, "weekly_revenue_report", components=components)


async def send_catalogue_warning(owner_phone: str, venue_name: str, broken_count: int) -> bool:
    """Alert owner that some songs in their catalogue may have become unavailable."""
    components = [{"type": "body", "parameters": [
        {"type": "text", "text": str(broken_count)},
        {"type": "text", "text": venue_name},
    ]}]
    return await send_whatsapp_template(owner_phone, "catalogue_warning", components=components)


async def send_playback_alert(support_phone: str, venue_name: str) -> bool:
    """Alert VibeQueue support (founder's number during pilot) of a stalled playback."""
    components = [{"type": "body", "parameters": [
        {"type": "text", "text": venue_name},
    ]}]
    return await send_whatsapp_template(support_phone, "playback_alert", components=components)
