"""tests/unit/repositories/test_queue_repo.py"""
import pytest


class TestQueueRepository:
    async def test_get_active_queue_returns_only_active_entries(self):
        pass

    async def test_get_waiting_pool_returns_only_entries_beyond_8(self):
        pass

    async def test_mark_as_played_updates_status_and_timestamp(self):
        pass
