"""Date parsing helpers for protocol-dated series."""

from __future__ import annotations

from datetime import date, datetime


def as_date(value: date | str) -> date:
    """Parse an ISO date, accepting ``datetime.date`` or ``YYYY-MM-DD`` strings."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])
