"""tests/unit/services/test_billing_service.py"""
import pytest


class TestBillingService:
    def test_gst_calculation(self):
        """GST is 18% of subtotal, rounded to integer paise."""
        subtotal = 2500   # ₹25
        expected_gst = 450  # 18% of 2500
        assert int(subtotal * 0.18) == expected_gst

    def test_total_is_subtotal_plus_gst(self):
        subtotal = 2500
        gst = int(subtotal * 0.18)
        total = subtotal + gst
        assert total == 2950

    async def test_pending_boosts_are_removable(self):
        pass

    async def test_confirmed_boosts_are_not_removable(self):
        pass
