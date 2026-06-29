"""
app/api/v1/middleware/logging.py

Request/response logging middleware.
Logs every request with: method, path, status_code, duration_ms, and request_id.
The request_id is injected into structlog context so every log line within
a request automatically carries the same ID — makes debugging trivial.
"""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "http.request",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error("http.request.error", error=str(exc), duration_ms=duration_ms)
            raise
        finally:
            structlog.contextvars.clear_contextvars()
