"""
app/core/logging.py

Structured JSON logging via structlog.
Every log line is machine-parseable — critical for production debugging.
Each log entry automatically includes: timestamp, level, venue_id,
request_id, and any custom context you bind per-request.
"""

import logging
import sys

import structlog
from structlog.types import EventDict

from app.core.config import settings


def add_app_context(logger, method_name, event_dict: EventDict) -> EventDict:
    """Processor: inject app-level metadata into every log entry."""
    event_dict["app"] = settings.APP_NAME
    event_dict["env"] = settings.APP_ENV
    return event_dict


def setup_logging() -> None:
    """
    Call once at application startup (in app/core/events.py).
    After this, use: logger = structlog.get_logger()
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.is_production:
        # JSON in production — parseable by log aggregators (Datadog, Loki)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Colourful console output in development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging so third-party libs (SQLAlchemy, httpx)
    # go through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    )
