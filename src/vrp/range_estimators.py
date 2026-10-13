"""Parkinson and Garman-Klass daily variance estimators.

Close-to-close squared log returns remain primary. Range estimators are
mandatory robustness measures. Their horizon aggregation delegates to the
same exchange-session-complete selectors as the primary targets.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Sequence

from vrp.targets import (
    annualize_hvar_21t,
    annualize_hvar_30c,
    select_forward_21t,
    select_forward_30c,
)


def parkinson_daily(high: float, low: float) -> float:
    """Daily Parkinson variance contribution."""

    if not math.isfinite(float(high)) or not math.isfinite(float(low)):
        raise ValueError("Parkinson requires finite high/low")
    if high <= 0 or low <= 0:
        raise ValueError("Parkinson requires positive high/low")
    return (math.log(high / low) ** 2) / (4.0 * math.log(2.0))


def garman_klass_daily(
    open_px: float, high: float, low: float, close: float
) -> float:
    """Daily Garman-Klass variance contribution."""

    values = [float(open_px), float(high), float(low), float(close)]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Garman-Klass requires finite OHLC")
    if min(values) <= 0:
        raise ValueError("Garman-Klass requires positive OHLC")
    return 0.5 * (math.log(high / low) ** 2) - (
        2.0 * math.log(2.0) - 1.0
    ) * (math.log(close / open_px) ** 2)


def realized_range_variance_30c(
    origin: date,
    daily_pairs: Sequence[tuple[date, float]],
    *,
    require_complete_calendar: bool = True,
    last_available: date | None = None,
) -> float | None:
    """Aggregate range contributions over every expected 30c XNYS session."""

    selected = select_forward_30c(
        origin,
        daily_pairs,
        require_complete_calendar=require_complete_calendar,
        last_available=last_available,
    )
    if selected is None:
        return None
    return annualize_hvar_30c(sum(selected))


def realized_range_variance_21t(
    origin: date,
    daily_pairs: Sequence[tuple[date, float]],
) -> float | None:
    """Aggregate over the exact next 21 expected XNYS sessions."""

    selected = select_forward_21t(origin, daily_pairs)
    if selected is None:
        return None
    return annualize_hvar_21t(sum(selected))
