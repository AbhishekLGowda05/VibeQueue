"""
app/workers/tasks/playback_tasks.py

Playback watchdog — runs every hour.
Checks for playback commands stuck in 'pending' state for longer
than PLAYBACK_WATCHDOG_SECONDS. If found, fires a WhatsApp alert
to the VibeQueue support contact (founder's number during pilot).

This catches the "staff forgot to open the music tab" scenario
before guests notice the queue is stalled.
"""

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="app.workers.tasks.playback_tasks.check_stalled_playback", bind=True)
def check_stalled_playback(self):
    logger.info("playback.watchdog.running")
    # Find PlaybackCommands with status='pending' and created_at older than watchdog threshold
    # For each: update status='stalled', fire WhatsApp alert via send_whatsapp_message
