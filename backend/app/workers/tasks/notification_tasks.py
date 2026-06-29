"""
app/workers/tasks/notification_tasks.py

WhatsApp notifications to venue owners.
Uses Meta's WhatsApp Cloud API via HTTP (no external SDK needed).
All notification content is pre-approved template messages.

Templates needed (register in Meta Business Manager before pilot):
  - weekly_revenue_report: "VibeQueue this week at {venue}: {songs} songs, {boosts} boosts, ₹{revenue} earned."
  - catalogue_warning: "{n} songs in your catalogue may have become unavailable. Tap here to review."
  - playback_alert: "Playback issue detected at {venue}. Check that the music tab is open."
  - session_opened: "Table {table_number} opened at {venue}. Tonight's code: {code}."
"""

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="app.workers.tasks.notification_tasks.send_weekly_revenue_reports", bind=True)
def send_weekly_revenue_reports(self):
    """Runs every Sunday at 11pm. Sends each venue owner their week's numbers."""
    logger.info("notifications.weekly_report.started")


@shared_task(name="app.workers.tasks.notification_tasks.send_whatsapp_message", bind=True, max_retries=3)
def send_whatsapp_message(self, phone_number: str, template_name: str, template_params: dict):
    """Generic WhatsApp message sender. All other tasks call this."""
    logger.info("notifications.whatsapp.sending", phone=phone_number, template=template_name)
