"""Strict date parsing helpers for protocol-dated series."""

from __future__ import annotations

from datetime import date, datetime
import re


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
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValueError("date strings must use exact YYYY-MM-DD format")
    return date.fromisoformat(value)
