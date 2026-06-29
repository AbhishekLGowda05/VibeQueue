"""
app/workers/tasks/catalogue_tasks.py

Runs every Monday at 3am IST (configured in app/core/celery.py).
For each song in every venue's catalogue, checks if the YouTube video
is still embeddable. Flags broken videos in the dashboard and
sends the venue owner a WhatsApp summary.

Why this matters: YouTube videos get removed, geo-blocked, or
age-restricted without notice. This job catches problems before
they become Saturday-night failures.
"""

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="app.workers.tasks.catalogue_tasks.validate_all_catalogues", bind=True, max_retries=3)
def validate_all_catalogues(self):
    """
    Entry point for the weekly cron job.
    Fetches all active venues and queues per-venue validation tasks.
    """
    logger.info("catalogue.validation.started")
    # Implementation: query all active venues, dispatch validate_venue_catalogue per venue
    # Using .delay() so each venue runs as an independent Celery task


@shared_task(name="app.workers.tasks.catalogue_tasks.validate_venue_catalogue", bind=True, max_retries=3)
def validate_venue_catalogue(self, venue_id: str):
    """
    For one venue: check every enabled song's YouTube video ID.
    Uses YouTube Data API videos.list endpoint (1 unit per 50 videos checked).
    Flags videos where: status.embeddable == false OR status.privacyStatus != 'public'.
    """
    logger.info("catalogue.venue.validation.started", venue_id=venue_id)
    # Implementation: batch YouTube Data API calls (50 IDs per request to save quota)
    # Update is_embeddable = False for failed videos
    # Dispatch send_catalogue_warning_notification if any videos flagged
