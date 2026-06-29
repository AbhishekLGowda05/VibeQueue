"""
app/services/playback_service.py

Handles all playback coordination between the queue engine
and the YouTube IFrame Player running on the venue's laptop.

Responsibilities:
  - Issue playback commands (write to DB + Redis channel)
  - Process incoming playback events (PLAYING, ENDED, ERROR)
  - Trigger billing confirmation on ENDED
  - Trigger fallback alert on ERROR > threshold
"""
import uuid
from datetime import datetime, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis import RedisKeys, redis_queue_client
from app.repositories.playback_repo import PlaybackRepository
from app.repositories.queue_repo import QueueRepository
from app.services.queue_engine import QueueEngine

logger = structlog.get_logger()


class PlaybackService:
    def __init__(
        self,
        playback_repo: PlaybackRepository,
        queue_repo: QueueRepository,
        queue_engine: QueueEngine,
        db: AsyncSession,
    ):
        self.playback_repo = playback_repo
        self.queue_repo = queue_repo
        self.queue_engine = queue_engine
        self.db = db

    async def issue_play_command(
        self,
        venue_id: uuid.UUID,
        queue_entry_id: uuid.UUID,
        youtube_video_id: str,
    ) -> None:
        """
        Write a playback command to DB and publish to the Redis channel
        that the venue's YouTube Playback Page is listening on.
        The page receives this via WebSocket and tells the IFrame Player to play.
        """
        command = await self.playback_repo.create(
            venue_id=venue_id,
            queue_entry_id=queue_entry_id,
            youtube_video_id=youtube_video_id,
            action="play",
            status="pending",
        )
        channel = RedisKeys.playback_command_channel(str(venue_id))
        import json
        await redis_queue_client.publish(channel, json.dumps({
            "command_id": str(command.id),
            "action": "play",
            "youtube_video_id": youtube_video_id,
            "queue_entry_id": str(queue_entry_id),
        }))
        logger.info("playback.command_issued", venue_id=str(venue_id), video_id=youtube_video_id)

    async def handle_event(
        self,
        venue_id: uuid.UUID,
        queue_entry_id: uuid.UUID,
        youtube_video_id: str,
        event_type: str,
        error_code: str = None,
    ) -> None:
        """
        Process an event received from the YouTube IFrame Player.

        PLAYING → mark command as acknowledged
        ENDED   → confirm billing, trigger next song
        ERROR   → log, potentially trigger fallback after threshold
        """
        await self.playback_repo.create_event(
            venue_id=venue_id,
            queue_entry_id=queue_entry_id,
            youtube_video_id=youtube_video_id,
            event_type=event_type,
            error_code=error_code,
        )

        if event_type == "ENDED":
            await self.queue_engine.confirm_song_played(venue_id, queue_entry_id)
            logger.info("playback.song_ended_billing_confirmed",
                        venue_id=str(venue_id), entry_id=str(queue_entry_id))

        elif event_type == "ERROR":
            logger.warning("playback.error",
                          venue_id=str(venue_id), error_code=error_code)
            # Fallback check is handled by the hourly watchdog task

        elif event_type == "PLAYING":
            logger.info("playback.started",
                       venue_id=str(venue_id), video_id=youtube_video_id)
