"""Parkinson and Garman–Klass daily variance estimators.

Protocol 1.0.1 keeps close-to-close squared log returns as the primary
realized-variance estimator. These range estimators are mandatory robustness
measures. Horizon aggregation uses the same eligible dates as the
close-to-close targets and the same annualization factors.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Sequence

from vrp.targets import annualize_hvar_21t, annualize_hvar_30c, select_forward_21t, select_forward_30c


def parkinson_daily(high: float, low: float) -> float:
    """``v^P = [ln(H/L)]^2 / (4 ln 2)``."""

    if high <= 0 or low <= 0:
        raise ValueError("Parkinson requires positive high/low")
    return (math.log(high / low) ** 2) / (4.0 * math.log(2.0))


def garman_klass_daily(open_px: float, high: float, low: float, close: float) -> float:
    """``v^GK = 0.5 [ln(H/L)]^2 - (2 ln 2 - 1) [ln(C/O)]^2``."""

    if min(open_px, high, low, close) <= 0:
        raise ValueError("Garman-Klass requires positive OHLC")
    return 0.5 * (math.log(high / low) ** 2) - (2.0 * math.log(2.0) - 1.0) * (
        math.log(close / open_px) ** 2
    )


def realized_range_variance_30c(
    origin: date,
    daily_pairs: Sequence[tuple[date, float]],
    *,
    require_complete_calendar: bool = True,
    last_available: date | None = None,
) -> float | None:
    """Sum daily range-estimator values over the primary 30-calendar-day window."""

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
    """Sum daily range-estimator values over the next 21 trading sessions."""

    selected = select_forward_21t(origin, daily_pairs)
    if selected is None:
        return None
    return annualize_hvar_21t(sum(selected))
