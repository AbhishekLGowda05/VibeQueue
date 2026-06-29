"""
app/services/boost_service.py

Boost validation helpers used by the queue engine.
The actual boost creation logic lives in QueueEngine.apply_boost —
this module holds stateless validation utilities called from there.
"""

VALID_BOOST_AMOUNTS_PAISE = {1500, 2500, 3500}  # ₹15, ₹25, ₹35


def is_valid_boost_amount(amount_paise: int) -> bool:
    """Only the three fixed tier amounts are accepted — no custom amounts."""
    return amount_paise in VALID_BOOST_AMOUNTS_PAISE


def would_exceed_cap(current_spend_paise: int, new_amount_paise: int, cap_paise: int) -> bool:
    """Returns True if adding this boost would put the table over the spend cap."""
    return (current_spend_paise + new_amount_paise) > cap_paise


def calculate_vibequeue_share(amount_paise: int, gst_rate: float = 0.18) -> int:
    """VibeQueue's 40% share of a boost, calculated on the pre-GST amount."""
    pre_gst = amount_paise / (1 + gst_rate)
    return int(pre_gst * 0.40)


def calculate_venue_share(amount_paise: int, gst_rate: float = 0.18) -> int:
    """Venue's 60% share of a boost, calculated on the pre-GST amount."""
    pre_gst = amount_paise / (1 + gst_rate)
    return int(pre_gst * 0.60)
