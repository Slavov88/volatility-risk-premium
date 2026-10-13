"""Deterministic XNYS exchange-session helpers.

All target completeness rules are expressed against the official exchange
session calendar, never against weekdays or the rows that happen to survive
cleaning. The calendar is instantiated over the full research sample rather
than relying on exchange_calendars' moving default date bounds.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import exchange_calendars as xcals

from vrp.dates import as_date

_CALENDAR_START = "1989-01-01"
_CALENDAR_END = "2030-12-31"


@lru_cache(maxsize=1)
def xnys_calendar():
    """Return the cached NYSE/XNYS calendar covering the full study window."""

    return xcals.get_calendar(
        "XNYS",
        start=_CALENDAR_START,
        end=_CALENDAR_END,
    )


def exchange_sessions(start: date, end: date) -> tuple[date, ...]:
    """Return every XNYS session in the inclusive calendar-date interval."""

    start_day = as_date(start)
    end_day = as_date(end)
    if start_day > end_day:
        return ()
    sessions = xnys_calendar().sessions_in_range(
        start_day.isoformat(), end_day.isoformat()
    )
    return tuple(timestamp.date() for timestamp in sessions)


def is_exchange_session(day: date) -> bool:
    """Whether day is an XNYS trading session."""

    normalized = as_date(day)
    return exchange_sessions(normalized, normalized) == (normalized,)


def forward_30c_sessions(origin: date, calendar_days: int = 30) -> tuple[date, ...]:
    """Expected return-ending sessions satisfying origin < d <= origin + H."""

    origin_day = as_date(origin)
    return exchange_sessions(
        origin_day + timedelta(days=1),
        origin_day + timedelta(days=calendar_days),
    )


def trailing_30c_sessions(origin: date, calendar_days: int = 30) -> tuple[date, ...]:
    """Expected sessions satisfying origin-H < d <= origin."""

    origin_day = as_date(origin)
    return exchange_sessions(
        origin_day - timedelta(days=calendar_days) + timedelta(days=1),
        origin_day,
    )


def next_exchange_sessions(origin: date, count: int) -> tuple[date, ...]:
    """Return exactly the next count XNYS sessions strictly after origin."""

    if count <= 0:
        raise ValueError("count must be positive")
    origin_day = as_date(origin)
    span = max(45, count * 3)
    while span <= 3660:
        sessions = exchange_sessions(
            origin_day + timedelta(days=1),
            origin_day + timedelta(days=span),
        )
        if len(sessions) >= count:
            return sessions[:count]
        span *= 2
    raise RuntimeError("unable to resolve enough future XNYS sessions")


def trailing_exchange_sessions(origin: date, count: int) -> tuple[date, ...]:
    """Return the last count XNYS sessions ending on or before origin."""

    if count <= 0:
        raise ValueError("count must be positive")
    origin_day = as_date(origin)
    span = max(45, count * 3)
    while span <= 3660:
        sessions = exchange_sessions(
            origin_day - timedelta(days=span),
            origin_day,
        )
        if len(sessions) >= count:
            return sessions[-count:]
        span *= 2
    raise RuntimeError("unable to resolve enough trailing XNYS sessions")
