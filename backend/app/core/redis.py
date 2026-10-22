"""
app/core/redis.py

Two Redis connection pools:
  - redis_client      : general purpose (sessions, rate-limiting, presence)
  - redis_queue_client: live in-memory queue state (separate DB index)

Redis key naming convention:
  vq:{venue_id}:queue          -> sorted set  — live queue scores
  vq:{venue_id}:session:{code} -> hash        — table session data
  vq:{venue_id}:ratelimit:{table_id} -> string — request cooldown
  vq:{venue_id}:playback       -> hash        — current playback state
  vq:{venue_id}:spend:{table_id} -> string   — running spend total (paise)
  vq:catalogue:validation      -> string      — last validation timestamp
"""

import redis.asyncio as aioredis

from app.core.config import settings


# ── General Redis pool ────────────────────────────────────────────────────────
redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    db=0,
    encoding="utf-8",
    decode_responses=True,
    max_connections=20,
)

# ── Live queue state pool (separate DB) ───────────────────────────────────────
redis_queue_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    db=settings.REDIS_QUEUE_DB,
    encoding="utf-8",
    decode_responses=True,
    max_connections=20,
)


# ── Key builders — always use these, never hand-craft keys ───────────────────
class RedisKeys:
    """
    Centralised key factory.
    If you change a key format, you change it here only.
    """

    @staticmethod
    def live_queue(venue_id: str) -> str:
        return f"vq:{venue_id}:queue"

    @staticmethod
    def table_session(venue_id: str, table_code: str) -> str:
        return f"vq:{venue_id}:session:{table_code}"

    @staticmethod
    def rate_limit(venue_id: str, table_id: str) -> str:
        return f"vq:{venue_id}:ratelimit:{table_id}"

    @staticmethod
    def playback_state(venue_id: str) -> str:
        return f"vq:{venue_id}:playback"

    @staticmethod
    def spend_total(venue_id: str, table_id: str) -> str:
        return f"vq:{venue_id}:spend:{table_id}"

    @staticmethod
    def websocket_channel(venue_id: str) -> str:
        return f"vq:{venue_id}:ws"

    @staticmethod
    def playback_command_channel(venue_id: str) -> str:
        return f"vq:{venue_id}:playback_cmd"


# ── Lua scripts — executed atomically inside Redis ───────────────────────────
SPEND_CAP_SCRIPT = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local increment = tonumber(ARGV[1])
local cap = tonumber(ARGV[2])
local ttl = tonumber(ARGV[3])
if current + increment > cap then
    return -1
end
redis.call('INCRBY', KEYS[1], increment)
redis.call('EXPIRE', KEYS[1], ttl)
return current + increment
"""


# ── Health check helper ───────────────────────────────────────────────────────
async def ping_redis() -> bool:
    try:
        return await redis_client.ping()
    except Exception:
        return False


# ── Graceful shutdown ─────────────────────────────────────────────────────────
async def close_redis_connections() -> None:
    await redis_client.aclose()
    await redis_queue_client.aclose()
