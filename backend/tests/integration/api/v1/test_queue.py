"""tests/integration/api/v1/test_queue.py"""
import pytest
from httpx import AsyncClient


class TestQueueRequest:
    async def test_request_song_happy_path(self, client: AsyncClient):
        """Guest with valid session can request a song in the catalogue."""
        pass

    async def test_request_song_enforces_cooldown(self, client: AsyncClient):
        """Second request within cooldown window returns 429."""
        pass

    async def test_request_song_not_in_catalogue_fails(self, client: AsyncClient):
        """Cannot request a song ID that does not exist in venue's catalogue."""
        pass

    async def test_queue_ceiling_at_8_songs(self, client: AsyncClient):
        """Songs beyond position 8 go to waiting pool, not active queue."""
        pass
