"""
app/workers/tasks/cleanup_tasks.py

Nightly cleanup at 2am IST.
- Expire table sessions that are past their expiry time
- Cancel pending boosts for expired queue entries (no charge to guest)
- Remove stale playback commands
- Archive old audit logs to cold storage (future)
"""

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="app.workers.tasks.cleanup_tasks.cleanup_expired_records", bind=True)
def cleanup_expired_records(self):
    logger.info("cleanup.started")
    # 1. Find all queue entries past expires_at with status='active'
    # 2. Set status='expired', cancel all pending boosts for those entries
    # 3. Find all table sessions past expires_at with is_active=True
    # 4. Set is_active=False
    # 5. Clear stale Redis keys for expired venues/sessions
