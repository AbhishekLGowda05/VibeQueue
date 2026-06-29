"""
app/api/v1/middleware/error_handler.py

Global exception handler — catches all unhandled errors and returns
a consistent JSON shape. Prevents stack traces leaking to clients.
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception",
            path=str(request.url),
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Our team has been notified.",
            },
        )
