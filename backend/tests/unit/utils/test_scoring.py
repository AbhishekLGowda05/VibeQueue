"""
tests/unit/utils/test_scoring.py

Tests for the queue scoring formula.
This is the most important unit test in the project —
the scoring determines every queue position.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.scoring import calculate_score, sort_queue_entries


def make_time(minutes_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)


class TestCalculateScore:
    def test_unboosted_song_scores_decay_base_at_zero_minutes(self):
        """An unboosted song requested right now gets max time decay."""
        now = datetime.now(timezone.utc)
        requested_at = now - timedelta(seconds=1)   # ~0 minutes ago
        score = calculate_score(0, requested_at, now=now)
        assert score > 900   # ~1000 / 0.016 minutes = very high

    def test_boost_increases_score(self):
        """A ₹25 boost (2500 paise) significantly increases score."""
        requested_at = make_time(10)  # 10 minutes ago
        score_no_boost = calculate_score(0, requested_at)
        score_with_boost = calculate_score(2500, requested_at)
        assert score_with_boost > score_no_boost + 2000   # Boost dominates

    def test_older_unbooosted_song_scores_lower(self):
        """Time decay: older songs score lower than newer songs (same boost)."""
        score_new = calculate_score(0, make_time(5))
        score_old = calculate_score(0, make_time(30))
        assert score_new > score_old

    def test_boost_can_overcome_age_gap(self):
        """A boosted song should beat an older unboosted song."""
        old_unbooosted = calculate_score(0, make_time(30))   # 30 min old, no boost
        new_boosted = calculate_score(3500, make_time(2))    # ₹35 boost, 2 min old
        assert new_boosted > old_unbooosted


class TestSortQueueEntries:
    def test_higher_boost_goes_first(self):
        """Song with higher boost total should be at position 0 after sort."""

        class FakeEntry:
            def __init__(self, paise, minutes_ago):
                self.boost_total_paise = paise
                self.created_at = make_time(minutes_ago)
                self.score = 0.0

        entries = [
            FakeEntry(paise=1500, minutes_ago=5),  # ₹15 boost
            FakeEntry(paise=3500, minutes_ago=5),  # ₹35 boost — should win
            FakeEntry(paise=2500, minutes_ago=5),  # ₹25 boost
        ]
        sorted_entries = sort_queue_entries(entries)
        assert sorted_entries[0].boost_total_paise == 3500

    def test_tie_broken_by_older_timestamp(self):
        """When scores are equal, older request goes first.
        Score = boost + 1000/minutes. To get equal scores at different ages:
        Entry A: 2400 paise, 5 min → 2400 + 200 = 2600
        Entry B: 2500 paise, 10 min → 2500 + 100 = 2600
        """
        now = datetime.now(timezone.utc)

        class FakeEntry:
            def __init__(self, paise, minutes_ago):
                self.boost_total_paise = paise
                self.created_at = now - timedelta(minutes=minutes_ago)
                self.score = 0.0

        entries = [
            FakeEntry(paise=2400, minutes_ago=5),   # newer — should lose tie
            FakeEntry(paise=2500, minutes_ago=10),  # older — should win tie
        ]
        sorted_entries = sort_queue_entries(entries, now=now)
        assert sorted_entries[0].created_at < sorted_entries[1].created_at
