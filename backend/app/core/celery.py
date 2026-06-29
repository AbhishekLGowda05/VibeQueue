"""
app/core/celery.py

Celery application instance and configuration.
Import this module in task files: from app.core.celery import celery_app
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


celery_app = Celery(
    "vibequeue",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.catalogue_tasks",
        "app.workers.tasks.payment_tasks",
        "app.workers.tasks.notification_tasks",
        "app.workers.tasks.playback_tasks",
        "app.workers.tasks.analytics_tasks",
        "app.workers.tasks.cleanup_tasks",
    ],
)

celery_app.conf.update(
    # ── Serialisation ────────────────────────────────────────────────
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,

    # ── Reliability ──────────────────────────────────────────────────
    task_acks_late=True,              # Acknowledge only after task completes
    task_reject_on_worker_lost=True,  # Re-queue if worker dies mid-task
    task_track_started=True,

    # ── Retry defaults ───────────────────────────────────────────────
    task_max_retries=3,
    task_default_retry_delay=60,      # 60 seconds between retries

    # ── Result expiry ────────────────────────────────────────────────
    result_expires=3600,              # Clean up results after 1 hour

    # ── Routing — separate queues per concern ────────────────────────
    task_routes={
        "app.workers.tasks.catalogue_tasks.*": {"queue": "catalogue"},
        "app.workers.tasks.payment_tasks.*": {"queue": "payments"},
        "app.workers.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.workers.tasks.playback_tasks.*": {"queue": "playback"},
        "app.workers.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.workers.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },

    # ── Beat schedule (periodic tasks) ───────────────────────────────
    beat_schedule={
        # Every Monday at 3am IST — validate YouTube video IDs
        "weekly-catalogue-validation": {
            "task": "app.workers.tasks.catalogue_tasks.validate_all_catalogues",
            "schedule": crontab(hour=3, minute=0, day_of_week=1),
        },
        # Every night at 2am — delete expired sessions and queue entries
        "nightly-cleanup": {
            "task": "app.workers.tasks.cleanup_tasks.cleanup_expired_records",
            "schedule": crontab(hour=2, minute=0),
        },
        # Every Sunday at 11pm — send weekly revenue reports to venue owners
        "weekly-revenue-report": {
            "task": "app.workers.tasks.notification_tasks.send_weekly_revenue_reports",
            "schedule": crontab(hour=23, minute=0, day_of_week=0),
        },
        # Every hour — check for stalled playback commands (watchdog)
        "playback-watchdog": {
            "task": "app.workers.tasks.playback_tasks.check_stalled_playback",
            "schedule": crontab(minute=0),
        },
    },
)
