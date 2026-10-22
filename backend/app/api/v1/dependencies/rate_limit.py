"""
app/api/v1/dependencies/rate_limit.py

IP-level rate limiting using Redis.
Protects public endpoints (join session, search songs) from abuse.
Per-table cooldowns are enforced inside the QueueEngine, not here.
"""
from fastapi import Depends, Request
from app.core.redis import redis_client
from app.exceptions.queue import CooldownActiveError


async def rate_limit_guest(request: Request, limit: int = 30, window: int = 60):
    """
    Allow max `limit` requests per IP per `window` seconds.
    Default: 30 requests per minute — generous for normal use, blocks scrapers.
    """
    ip = request.client.host
    key = f"ratelimit:ip:{ip}:{request.url.path}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, window)
    if count > limit:
        raise CooldownActiveError(retry_after_seconds=window)


async def rate_limit_join(request: Request):
    """
    Tight rate limit for table code join attempts: 5 per minute per IP.
    A 6-digit code has 1M combinations — this makes brute-force impractical
    (~7,200 attempts/day vs 1M keyspace).
    """
    await rate_limit_guest(request, limit=5, window=60)
