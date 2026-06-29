"""
app/workers/tasks/payment_tasks.py

Async payment processing tasks.
- verify_razorpay_payment: called from webhook, verifies signature, confirms payment
- settle_venue_share: weekly job that calculates and records what each venue owes VibeQueue
"""

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="app.workers.tasks.payment_tasks.verify_razorpay_payment", bind=True, max_retries=3)
def verify_razorpay_payment(self, payment_id: str, order_id: str, signature: str, session_id: str):
    logger.info("payment.verification.started", payment_id=payment_id)


@shared_task(name="app.workers.tasks.payment_tasks.settle_weekly_revenue", bind=True)
def settle_weekly_revenue(self):
    logger.info("payment.settlement.started")
