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

    high_value = float(high)
    low_value = float(low)
    if not math.isfinite(high_value) or not math.isfinite(low_value):
        raise ValueError("Parkinson requires finite high/low")
    if high_value <= 0 or low_value <= 0:
        raise ValueError("Parkinson requires positive high/low")
    if high_value < low_value:
        raise ValueError("Parkinson requires High >= Low")
    return (math.log(high_value / low_value) ** 2) / (4.0 * math.log(2.0))


def garman_klass_daily(
    open_px: float, high: float, low: float, close: float
) -> float:
    """Daily Garman-Klass variance contribution."""

    open_value = float(open_px)
    high_value = float(high)
    low_value = float(low)
    close_value = float(close)
    values = [open_value, high_value, low_value, close_value]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Garman-Klass requires finite OHLC")
    if min(values) <= 0:
        raise ValueError("Garman-Klass requires positive OHLC")
    if high_value < max(open_value, close_value):
        raise ValueError("Garman-Klass requires High >= max(Open, Close)")
    if low_value > min(open_value, close_value):
        raise ValueError("Garman-Klass requires Low <= min(Open, Close)")
    if high_value < low_value:
        raise ValueError("Garman-Klass requires High >= Low")
    estimate = 0.5 * (math.log(high_value / low_value) ** 2) - (
        2.0 * math.log(2.0) - 1.0
    ) * (math.log(close_value / open_value) ** 2)
    if estimate < -1e-15:
        raise ValueError("Garman-Klass variance contribution cannot be negative")
    return max(0.0, estimate)


def realized_range_variance_30c(
    origin: date,
    daily_pairs: Sequence[tuple[date, float]],
) -> float | None:
    """Aggregate range contributions over every expected 30c XNYS session."""

    selected = select_forward_30c(origin, daily_pairs)
    if selected is None:
        return None
    if any(value < 0 for value in selected):
        raise ValueError("range-variance contributions must be non-negative")
    return annualize_hvar_30c(sum(selected))


def realized_range_variance_21t(
    origin: date,
    daily_pairs: Sequence[tuple[date, float]],
) -> float | None:
    """Aggregate over the exact next 21 expected XNYS sessions."""

    selected = select_forward_21t(origin, daily_pairs)
    if selected is None:
        return None
    if any(value < 0 for value in selected):
        raise ValueError("range-variance contributions must be non-negative")
    return annualize_hvar_21t(sum(selected))
