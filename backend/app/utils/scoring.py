"""
app/utils/scoring.py

The queue scoring formula — the heart of the priority system.
Centralised here so the same logic runs in the API, queue engine,
and tests. Never duplicate this formula anywhere else.

Formula:
  score = boost_total_paise + time_decay_factor

  time_decay_factor = DECAY_BASE / minutes_since_request
  (max DECAY_BASE at time=0, decays toward 0 as time passes)

This means:
  - Boosted songs float to the top
  - Unbooosted songs still rise naturally over time (preventing starvation)
  - Very old unplayed songs eventually fade (90-min expiry handles the rest)
"""

from datetime import datetime, timezone


# The time decay base — controls how much age matters relative to boosts.
# At DECAY_BASE = 1000 paise (₹10): a 30-minute-old unbooosted song
# has a score of ~33 (1000/30), which a ₹15 boost (1500 paise) immediately beats.
DECAY_BASE: int = 1000  # paise equivalent for decay calculation


def calculate_score(
    boost_total_paise: int,
    requested_at: datetime,
    now: datetime = None,
) -> float:
    """
    Calculate the current priority score for a queue entry.

    Args:
        boost_total_paise: Sum of all confirmed boosts on this entry (in paise)
        requested_at:      When the song was first requested (timezone-aware)
        now:               Current time (defaults to UTC now; injectable for tests)

    Returns:
        float score — higher is higher priority
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Ensure timezone awareness
    if requested_at.tzinfo is None:
        requested_at = requested_at.replace(tzinfo=timezone.utc)

    elapsed_seconds = (now - requested_at).total_seconds()
    elapsed_minutes = max(elapsed_seconds / 60, 0.01)   # Avoid division by zero

    time_decay = DECAY_BASE / elapsed_minutes
    return float(boost_total_paise) + time_decay


def sort_queue_entries(entries: list, now: datetime = None) -> list:
    """
    Sort a list of queue entry dicts/objects by score descending.
    Tie-breaker: oldest requested_at goes first (deterministic, no randomness).

    Args:
        entries: List of objects with boost_total_paise, requested_at, score attributes
        now:     Injectable for testing

    Returns:
        Sorted list (position 1 = index 0)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    for entry in entries:
        entry.score = calculate_score(
            boost_total_paise=entry.boost_total_paise,
            requested_at=entry.created_at,
            now=now,
        )

    return sorted(
        entries,
        key=lambda e: (-e.score, e.created_at),  # High score first, then oldest first
    )
