"""tests/integration/api/v1/test_billing.py"""
import pytest
from httpx import AsyncClient


class TestBilling:
    async def test_billing_review_shows_confirmed_and_pending(self, client: AsyncClient):
        """Review shows confirmed (played) and pending (in queue) boosts."""
        pass

    async def test_remove_pending_boost(self, client: AsyncClient):
        """Guest can remove a pending boost before confirmation."""
        pass

    async def test_cannot_remove_confirmed_boost(self, client: AsyncClient):
        """Confirmed (played) boosts cannot be removed — charge is final."""
        pass

    async def test_gst_calculation(self, client: AsyncClient):
        """Total = subtotal + 18% GST. Verify the maths."""
        # ₹25 boost: subtotal=2500, gst=450, total=2950
        pass
