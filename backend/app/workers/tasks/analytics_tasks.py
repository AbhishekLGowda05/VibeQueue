"""
app/workers/tasks/analytics_tasks.py

Aggregate analytics computations run in the background.
Never block the API with heavy queries — queue them here instead.
- Daily: compute per-venue engagement metrics
- Weekly: compute boost conversion rates, dwell-time proxies
"""

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="app.workers.tasks.analytics_tasks.compute_daily_metrics", bind=True)
def compute_daily_metrics(self):
    logger.info("analytics.daily.started")
