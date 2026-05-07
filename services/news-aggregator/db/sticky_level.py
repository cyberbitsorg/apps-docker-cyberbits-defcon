"""
Sticky-level state machine. DEFCON numbering is INVERTED: 1 = highest severity, 5 = lowest.

The state machine tracks a "floor" — the most severe level seen recently —
and only allows the displayed level to decrease in severity (numeric value
increase) one step per cooldown period. Severity rises take effect immediately.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg

COOLDOWN = timedelta(hours=6)


def is_more_severe(level_a: int, level_b: int) -> bool:
    """True if level_a represents higher threat than level_b. Lower numeric = more severe."""
    return level_a < level_b


@dataclass(frozen=True)
class StickyState:
    min_level_until_at: Optional[datetime]
    min_level_floor: Optional[int]


@dataclass(frozen=True)
class StickyResult:
    displayed_level: int
    new_floor: int
    new_until_at: Optional[datetime]


def compute_displayed_level(raw_level: int, state: StickyState, now: datetime) -> StickyResult:
    floor = state.min_level_floor

    # Cold start
    if floor is None:
        return StickyResult(displayed_level=raw_level, new_floor=raw_level, new_until_at=None)

    # Severity rising (or equal): update floor, clear cooldown
    if is_more_severe(raw_level, floor) or raw_level == floor:
        return StickyResult(
            displayed_level=raw_level,
            new_floor=raw_level,
            new_until_at=None,
        )

    # Here: raw is LESS severe than floor (numeric raw > floor)
    until = state.min_level_until_at

    # No cooldown yet → start one, hold at floor
    if until is None:
        return StickyResult(
            displayed_level=floor,
            new_floor=floor,
            new_until_at=now + COOLDOWN,
        )

    # Cooldown still active → hold
    if now < until:
        return StickyResult(
            displayed_level=floor,
            new_floor=floor,
            new_until_at=until,
        )

    # Cooldown expired → step floor by 1 toward raw (less severe)
    new_floor = floor + 1
    if is_more_severe(new_floor, raw_level) or new_floor == raw_level:
        # not yet at raw — chain another cooldown
        if new_floor == raw_level:
            new_until = None
        else:
            new_until = now + COOLDOWN
    else:
        # overshot — clamp to raw
        new_floor = raw_level
        new_until = None

    return StickyResult(
        displayed_level=new_floor,
        new_floor=new_floor,
        new_until_at=new_until,
    )


# --- DB I/O ---

async def read_sticky_state(pool: asyncpg.Pool) -> StickyState:
    row = await pool.fetchrow(
        "SELECT min_level_until_at, min_level_floor FROM last_refresh WHERE id = 1"
    )
    if row is None:
        return StickyState(min_level_until_at=None, min_level_floor=None)
    return StickyState(
        min_level_until_at=row["min_level_until_at"],
        min_level_floor=row["min_level_floor"],
    )


async def write_sticky_state(pool: asyncpg.Pool, result: StickyResult) -> None:
    await pool.execute(
        """
        UPDATE last_refresh
        SET min_level_until_at = $1, min_level_floor = $2
        WHERE id = 1
        """,
        result.new_until_at,
        result.new_floor,
    )
