"""Strict date parsing helpers for protocol-dated series."""

from __future__ import annotations

from datetime import date, datetime


def as_date(value: date | str) -> date:
    """Parse an exact ISO calendar date without silently truncating strings."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise TypeError(
            "date value must be datetime.date, datetime, or ISO date string"
        )
    if len(value) != 10:
        raise ValueError("date strings must use exact YYYY-MM-DD format")
    return date.fromisoformat(value)
