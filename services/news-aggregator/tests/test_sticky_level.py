"""
Sticky-level state machine tests. NOTE: DEFCON 1 = highest severity.
'Level rising in severity' means numeric value DECREASES (5 → 4 → ... → 1).
"""
from datetime import datetime, timedelta, timezone
import pytest
from db.sticky_level import (
    is_more_severe,
    compute_displayed_level,
    StickyState,
    StickyResult,
)


def test_is_more_severe():
    # Lower numeric = more severe
    assert is_more_severe(1, 2) is True
    assert is_more_severe(3, 4) is True
    assert is_more_severe(5, 4) is False
    assert is_more_severe(3, 3) is False


def test_cold_start_no_state():
    # Both NULL: displayed = raw, set new floor
    state = StickyState(min_level_until_at=None, min_level_floor=None)
    result = compute_displayed_level(raw_level=3, state=state, now=datetime(2026, 5, 6, 12, tzinfo=timezone.utc))
    assert result.displayed_level == 3
    assert result.new_floor == 3
    assert result.new_until_at is None


def test_severity_rises_immediately():
    # raw_level (2) is MORE severe than floor (4) → update floor immediately, no cooldown
    now = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    state = StickyState(min_level_until_at=None, min_level_floor=4)
    result = compute_displayed_level(raw_level=2, state=state, now=now)
    assert result.displayed_level == 2
    assert result.new_floor == 2
    assert result.new_until_at is None


def test_severity_drops_starts_cooldown():
    # raw (4) is LESS severe than floor (2) and no cooldown set → start cooldown
    now = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    state = StickyState(min_level_until_at=None, min_level_floor=2)
    result = compute_displayed_level(raw_level=4, state=state, now=now)
    assert result.displayed_level == 2  # held at floor
    assert result.new_floor == 2
    assert result.new_until_at == now + timedelta(hours=3)


def test_during_cooldown_holds_floor():
    # Cooldown active, raw still less severe → keep displaying floor
    now = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    state = StickyState(
        min_level_until_at=now + timedelta(hours=2),
        min_level_floor=2,
    )
    result = compute_displayed_level(raw_level=4, state=state, now=now)
    assert result.displayed_level == 2
    assert result.new_floor == 2
    assert result.new_until_at == state.min_level_until_at  # unchanged


def test_cooldown_expires_decrements_floor():
    # Cooldown expired, raw still less severe → step floor by 1 toward raw
    now = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    state = StickyState(
        min_level_until_at=now - timedelta(seconds=1),
        min_level_floor=2,
    )
    result = compute_displayed_level(raw_level=4, state=state, now=now)
    assert result.displayed_level == 3  # stepped 2 → 3
    assert result.new_floor == 3
    # new floor (3) is still more severe than raw (4) → another cooldown chained
    assert result.new_until_at == now + timedelta(hours=3)


def test_cooldown_expires_floor_meets_raw():
    # After step, new floor matches raw → no more cooldown
    now = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    state = StickyState(
        min_level_until_at=now - timedelta(seconds=1),
        min_level_floor=3,
    )
    result = compute_displayed_level(raw_level=4, state=state, now=now)
    assert result.displayed_level == 4
    assert result.new_floor == 4
    assert result.new_until_at is None


def test_severity_rises_during_cooldown_clears_it():
    # Cooldown active but raw becomes MORE severe than floor → clear cooldown, take raw
    now = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    state = StickyState(
        min_level_until_at=now + timedelta(hours=2),
        min_level_floor=3,
    )
    result = compute_displayed_level(raw_level=1, state=state, now=now)
    assert result.displayed_level == 1
    assert result.new_floor == 1
    assert result.new_until_at is None


def test_raw_equals_floor_clears_cooldown():
    # raw == floor → no cooldown needed, clear if any
    now = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    state = StickyState(
        min_level_until_at=now + timedelta(hours=2),
        min_level_floor=3,
    )
    result = compute_displayed_level(raw_level=3, state=state, now=now)
    assert result.displayed_level == 3
    assert result.new_floor == 3
    assert result.new_until_at is None
