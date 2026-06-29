"""
app/services/queue_engine.py

The central brain of VibeQueue.
Responsible for:
  - Accepting new song requests
  - Accepting boost transactions
  - Re-scoring and re-sorting the queue after every change
  - Writing the sorted queue back to Redis (live state) + PostgreSQL (permanent)
  - Broadcasting queue updates to all connected WebSocket clients
  - Triggering playback commands when a song reaches position 1

Flow for every state-changing operation:
  1. Validate the request (cooldown, spend cap, song in catalogue, etc.)
  2. Write to PostgreSQL (source of truth)
  3. Recalculate all scores
  4. Write sorted queue to Redis (live state for instant reads)
  5. Publish update event to Redis Pub/Sub (WebSocket broadcaster picks it up)
  6. Return the new queue state
"""

import uuid
from datetime import datetime, timedelta, timezone

import structlog

from app.core.config import settings
from app.core.redis import RedisKeys, redis_queue_client
from app.exceptions.queue import (
    CooldownActiveError,
    QueueSongNotFoundError,
    SpendCapExceededError,
    WaitingPoolBoostError,
)
from app.models.boost import Boost
from app.models.queue import QueueEntry
from app.repositories.boost_repo import BoostRepository
from app.repositories.queue_repo import QueueRepository
from app.repositories.session_repo import SessionRepository
from app.utils.scoring import sort_queue_entries

logger = structlog.get_logger()


class QueueEngine:
    """
    Instantiated per-request with injected repositories.
    All methods are async — they must not block the event loop.
    """

    def __init__(
        self,
        queue_repo: QueueRepository,
        boost_repo: BoostRepository,
        session_repo: SessionRepository,
    ):
        self.queue_repo = queue_repo
        self.boost_repo = boost_repo
        self.session_repo = session_repo

    async def add_song_request(
        self,
        venue_id: uuid.UUID,
        session_id: uuid.UUID,
        song_id: uuid.UUID,
        youtube_video_id: str,
    ) -> QueueEntry:
        """
        Process a free song request from a guest.

        Checks:
          - Table cooldown (one request per N minutes per table)
          - Song not already in active queue from this table
        Then:
          - Creates queue entry in PostgreSQL
          - Positions it (active queue if <8 songs, waiting pool if full)
          - Recalculates and broadcasts updated queue
        """
        session = await self.session_repo.get_by_id(session_id)

        # ── Cooldown check ────────────────────────────────────────────
        cooldown_key = RedisKeys.rate_limit(str(venue_id), str(session_id))
        if await redis_queue_client.exists(cooldown_key):
            ttl = await redis_queue_client.ttl(cooldown_key)
            raise CooldownActiveError(retry_after_seconds=ttl)

        # ── Determine position ────────────────────────────────────────
        active_count = await self.queue_repo.count_active_for_venue(venue_id)
        position = active_count + 1  # Goes to active queue or waiting pool

        expiry = datetime.now(timezone.utc) + timedelta(
            seconds=settings.QUEUE_SONG_EXPIRY_SECONDS
        )

        entry = await self.queue_repo.create(
            venue_id=venue_id,
            session_id=session_id,
            song_id=song_id,
            youtube_video_id=youtube_video_id,
            position=position,
            expires_at=expiry,
            boost_total_paise=0,
        )

        # ── Set cooldown in Redis ─────────────────────────────────────
        await redis_queue_client.setex(
            cooldown_key,
            settings.DEFAULT_REQUEST_COOLDOWN_SECONDS,
            "1",
        )

        await self._recalculate_and_broadcast(venue_id)

        logger.info(
            "queue.song_added",
            venue_id=str(venue_id),
            session_id=str(session_id),
            song_id=str(song_id),
            position=position,
        )

        return entry

    async def apply_boost(
        self,
        venue_id: uuid.UUID,
        session_id: uuid.UUID,
        queue_entry_id: uuid.UUID,
        amount_paise: int,
    ) -> Boost:
        """
        Apply a paid boost to a queue entry.

        Checks:
          - Entry exists and belongs to this venue
          - Entry is in active queue (not waiting pool) — no boosts in waiting pool
          - Spend cap not exceeded for this table session
        Then:
          - Creates pending boost record
          - Updates entry's boost_total_paise
          - Recalculates scores and re-sorts queue
          - Broadcasts updated queue
        """
        entry = await self.queue_repo.get_by_id(queue_entry_id)
        if not entry or entry.venue_id != venue_id:
            raise QueueSongNotFoundError()

        if entry.position > 8:
            raise WaitingPoolBoostError()

        # ── Spend cap check ───────────────────────────────────────────
        spend_key = RedisKeys.spend_total(str(venue_id), str(session_id))
        current_spend = int(await redis_queue_client.get(spend_key) or 0)
        venue_cap = settings.DEFAULT_SPEND_CAP_PAISE  # TODO: load from venue config

        if current_spend + amount_paise > venue_cap:
            raise SpendCapExceededError(
                current_spend_paise=current_spend,
                cap_paise=venue_cap,
            )

        # ── Create boost record ───────────────────────────────────────
        boost = await self.boost_repo.create(
            venue_id=venue_id,
            session_id=session_id,
            queue_entry_id=queue_entry_id,
            amount_paise=amount_paise,
            status="pending",
        )

        # ── Update entry's running boost total ────────────────────────
        await self.queue_repo.update(
            entry,
            boost_total_paise=entry.boost_total_paise + amount_paise,
        )

        # ── Update spend total in Redis ───────────────────────────────
        await redis_queue_client.incrby(spend_key, amount_paise)
        await redis_queue_client.expire(
            spend_key, settings.TABLE_CODE_EXPIRY_SECONDS
        )

        await self._recalculate_and_broadcast(venue_id)

        logger.info(
            "queue.boost_applied",
            venue_id=str(venue_id),
            session_id=str(session_id),
            queue_entry_id=str(queue_entry_id),
            amount_paise=amount_paise,
        )

        return boost

    async def confirm_song_played(
        self, venue_id: uuid.UUID, queue_entry_id: uuid.UUID
    ) -> None:
        """
        Called when a PLAYBACK_EVENT 'ENDED' or a Mode B 'Mark as Played' arrives.
        - Marks the queue entry as played
        - Confirms all pending boosts for this entry (makes charges real)
        - Triggers next song in queue
        """
        entry = await self.queue_repo.get_by_id(queue_entry_id)
        if not entry:
            return

        await self.queue_repo.mark_as_played(queue_entry_id)
        await self.boost_repo.confirm_all_for_entry(queue_entry_id)

        logger.info(
            "queue.song_confirmed_played",
            venue_id=str(venue_id),
            queue_entry_id=str(queue_entry_id),
        )

        await self._recalculate_and_broadcast(venue_id)

    async def _recalculate_and_broadcast(self, venue_id: uuid.UUID) -> None:
        """
        Internal: re-score all active entries, assign new positions,
        write to Redis, and publish a WebSocket broadcast event.
        This runs after EVERY queue-changing operation.
        """
        all_active = await self.queue_repo.get_active_queue(venue_id)
        waiting = await self.queue_repo.get_waiting_pool(venue_id)

        sorted_active = sort_queue_entries(all_active)
        sorted_waiting = sort_queue_entries(waiting)

        # Assign positions and persist new scores
        for i, entry in enumerate(sorted_active, start=1):
            await self.queue_repo.update(entry, position=i, score=entry.score)
        for i, entry in enumerate(sorted_waiting, start=9):
            await self.queue_repo.update(entry, position=i, score=entry.score)

        # Publish to Redis channel — WebSocket broadcaster picks this up
        channel = RedisKeys.websocket_channel(str(venue_id))
        await redis_queue_client.publish(channel, "queue_updated")
