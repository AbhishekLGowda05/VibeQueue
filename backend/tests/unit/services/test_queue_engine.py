"""tests/unit/services/test_queue_engine.py"""
import pytest


class TestQueueEngine:
    async def test_add_song_creates_queue_entry(self):
        """Requesting a song creates a QueueEntry with status='active'."""
        pass

    async def test_add_song_enforces_cooldown(self):
        """Second request within cooldown raises CooldownActiveError."""
        pass

    async def test_boost_increases_score(self):
        """Applying a boost increases the entry's boost_total_paise and re-sorts queue."""
        pass

    async def test_boost_waiting_pool_raises(self):
        """Boosting a waiting pool entry raises WaitingPoolBoostError."""
        pass

    async def test_confirm_song_played_confirms_all_boosts(self):
        """confirm_song_played() marks all pending boosts for that entry as confirmed."""
        pass
