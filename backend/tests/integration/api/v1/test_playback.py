"""tests/integration/api/v1/test_playback.py"""
import pytest
from httpx import AsyncClient


class TestPlaybackEvents:
    async def test_ended_event_confirms_boosts(self, client: AsyncClient):
        """ENDED event marks all pending boosts for that queue entry as confirmed."""
        pass

    async def test_error_event_does_not_confirm_boosts(self, client: AsyncClient):
        """ERROR event does NOT confirm any boosts — song did not play."""
        pass

    async def test_ended_event_triggers_next_song(self, client: AsyncClient):
        """After ENDED, the queue advances and a new playback command is issued."""
        pass
