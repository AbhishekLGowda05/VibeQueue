"""
app/api/v1/routes/websockets.py

WebSocket endpoints for real-time queue updates.

Two channels:
  /ws/venue/{venue_id}/queue     — Guest phones + Ambient Display subscribe here
  /ws/venue/{venue_id}/dashboard — Venue dashboard subscribes here (staff view)

Architecture:
  Client connects → FastAPI WebSocket handler opens
  Handler subscribes to Redis Pub/Sub channel for that venue
  When queue_engine publishes "queue_updated" → handler reads fresh state → sends to client
  Client receives updated queue without polling
"""

import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import AsyncSessionLocal
from app.core.redis import RedisKeys, redis_queue_client
from app.repositories.queue_repo import QueueRepository

router = APIRouter()
logger = structlog.get_logger()


@router.websocket("/venue/{venue_id}/queue")
async def queue_websocket(websocket: WebSocket, venue_id: str):
    """
    Real-time queue feed for guests and ambient display.
    Sends full queue state on connect, then pushes updates.
    """
    await websocket.accept()
    logger.info("ws.guest.connected", venue_id=venue_id)

    channel = RedisKeys.websocket_channel(venue_id)
    pubsub = redis_queue_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        # Send initial state immediately on connect
        await _send_queue_state(websocket, venue_id)

        # Listen for update events
        async for message in pubsub.listen():
            if message["type"] == "message":
                await _send_queue_state(websocket, venue_id)

    except WebSocketDisconnect:
        logger.info("ws.guest.disconnected", venue_id=venue_id)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


async def _send_queue_state(websocket: WebSocket, venue_id: str) -> None:
    """Fetch current queue from DB and send to the connected client."""
    async with AsyncSessionLocal() as db:
        repo = QueueRepository(db)
        import uuid
        active = await repo.get_active_queue(uuid.UUID(venue_id))
        payload = {
            "type": "queue_update",
            "active_queue": [
                {
                    "id": str(e.id),
                    "position": e.position,
                    "youtube_video_id": e.youtube_video_id,
                    "boost_total_paise": e.boost_total_paise,
                    "score": round(e.score, 2),
                    "status": e.status,
                }
                for e in active
            ],
        }
        await websocket.send_json(payload)
