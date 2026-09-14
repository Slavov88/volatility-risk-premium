"""NBER regime labels given an already supplied monthly chronology.

A daily forecast origin inherits the NBER status of its calendar month.
Downloading or constructing the chronology is out of scope for this module.
"""

from __future__ import annotations

from datetime import date
from typing import Sequence

from vrp.dates import as_date


def recession_months_from_chronology(
    chronology_dates: Sequence[date | str],
    recession_flags: Sequence[object],
) -> set[str]:
    """Return ``YYYY-MM`` keys for months flagged as recession in a supplied table."""

    if len(chronology_dates) != len(recession_flags):
        raise ValueError("chronology dates and recession flags must have the same length")
    months: set[str] = set()
    for raw_day, flag in zip(chronology_dates, recession_flags, strict=True):
        if flag:
            months.add(as_date(raw_day).strftime("%Y-%m"))
    return months


def label_nber_regimes(
    origins: Sequence[date | str],
    recession_months: set[str],
) -> list[tuple[date, str]]:
    """Label each origin ``recession`` or ``expansion`` from supplied ``YYYY-MM`` keys."""

    labeled: list[tuple[date, str]] = []
    for raw in origins:
        origin = as_date(raw)
        key = origin.strftime("%Y-%m")
        labeled.append((origin, "recession" if key in recession_months else "expansion"))
    return labeled
