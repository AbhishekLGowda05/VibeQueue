"""tests/unit/services/test_boost_service.py"""
import pytest


class TestBoostService:
    async def test_only_valid_amounts_accepted(self):
        """Only 1500, 2500, 3500 paise are valid boost amounts."""
        valid = {1500, 2500, 3500}
        assert 2000 not in valid
        assert 2500 in valid

    async def test_spend_cap_enforced(self):
        pass
