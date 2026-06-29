"""app/utils/formatters.py — Display formatting helpers"""


def paise_to_rupees_display(paise: int) -> str:
    """₹1500 paise → '₹15'"""
    return f"₹{paise // 100}"


def paise_to_rupees_decimal(paise: int) -> float:
    """1500 paise → 15.00"""
    return paise / 100


def format_duration(seconds: int) -> str:
    """225 seconds → '3:45'"""
    if not seconds:
        return "--:--"
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def format_conversion_rate(requested: int, boosted: int) -> str:
    """Format boost conversion rate for reports."""
    if requested == 0:
        return "0%"
    rate = (boosted / requested) * 100
    return f"{rate:.1f}%"
