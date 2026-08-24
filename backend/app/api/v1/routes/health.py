"""
app/api/v1/routes/health.py

Health check endpoint. Called by load balancers and monitoring systems.
Returns 200 if the app, database, and Redis are all reachable.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import ping_redis

router = APIRouter()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Returns: {"status": "ok", "database": "ok", "redis": "ok"}
    Any component failure returns 503.
    """
    db_ok = False
    redis_ok = False

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        redis_ok = await ping_redis()
    except Exception:
        pass

    all_ok = db_ok and redis_ok
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "status": "ok" if all_ok else "degraded",
            "database": "ok" if db_ok else "unreachable",
            "redis": "ok" if redis_ok else "unreachable",
        },
    )
