"""Strict NBER regime-label helpers.

A daily forecast origin inherits the NBER status of its calendar month.
Chronology flags are parsed explicitly; arbitrary Python truthiness is never
used because, for example, the string "0" is truthy.
"""

from __future__ import annotations

from datetime import date
from numbers import Integral
from typing import Sequence

from vrp.dates import as_date


def _parse_recession_flag(flag: object) -> bool:
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, Integral):
        if int(flag) in {0, 1}:
            return bool(int(flag))
        raise ValueError("integer recession flags must be 0 or 1")
    if isinstance(flag, str):
        normalized = flag.strip()
        if normalized == "1":
            return True
        if normalized == "0":
            return False
        raise ValueError("string recession flags must be '0' or '1'")
    raise ValueError(
        "recession flags must be bool, integer 0/1, or string '0'/'1'"
    )


def recession_months_from_chronology(
    chronology_dates: Sequence[date | str],
    recession_flags: Sequence[object],
) -> set[str]:
    """Return YYYY-MM keys for months explicitly flagged as recession."""

    if len(chronology_dates) != len(recession_flags):
        raise ValueError(
            "chronology dates and recession flags must have the same length"
        )
    months: set[str] = set()
    seen: set[str] = set()
    for raw_day, raw_flag in zip(
        chronology_dates, recession_flags, strict=True
    ):
        month = as_date(raw_day).strftime("%Y-%m")
        if month in seen:
            raise ValueError(f"duplicate chronology month {month}")
        seen.add(month)
        if _parse_recession_flag(raw_flag):
            months.add(month)
    return months


def label_nber_regimes(
    origins: Sequence[date | str],
    recession_months: set[str],
) -> list[tuple[date, str]]:
    """Label each origin recession or expansion from supplied YYYY-MM keys."""

    labeled: list[tuple[date, str]] = []
    for raw in origins:
        origin = as_date(raw)
        key = origin.strftime("%Y-%m")
        labeled.append(
            (origin, "recession" if key in recession_months else "expansion")
        )
    return labeled
