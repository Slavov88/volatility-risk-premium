"""Forward realized-variance targets locked by Protocol 1.0.1.

Primary horizon: exact forward 30 calendar days, annualized by ``365/30``.
Mandatory robustness: the next 21 trading-day returns, annualized by ``252/21``.
The first target return must end strictly after the origin. Incomplete
end-of-sample calendar windows are missing and are never shortened.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Sequence

from vrp.config import CONVENTIONS
from vrp.dates import as_date


def forecast_origin_end() -> date:
    return date.fromisoformat(CONVENTIONS.sample_end)


def sample_start() -> date:
    return date.fromisoformat(CONVENTIONS.sample_start)


def assert_forecast_origin_allowed(origin: date) -> None:
    """Enforce the locked forecast-origin sample, not target-support availability."""

    origin = as_date(origin)
    if origin > forecast_origin_end():
        raise ValueError(
            f"forecast origin {origin.isoformat()} is after locked cutoff "
            f"{CONVENTIONS.sample_end}"
        )
    if origin < sample_start():
        raise ValueError(
            f"forecast origin {origin.isoformat()} is before sample start "
            f"{CONVENTIONS.sample_start}"
        )


def primary_horizon_end(origin: date) -> date:
    """Calendar date ``t + 30`` days for origin ``t``."""

    return as_date(origin) + timedelta(days=CONVENTIONS.primary_calendar_days)


def annualize_hvar_30c(hvar: float) -> float:
    """Annualize a 30-calendar-day sum of daily variance contributions."""

    return (
        CONVENTIONS.calendar_days_per_year / CONVENTIONS.primary_calendar_days
    ) * hvar


def annualize_hvar_21t(hvar: float) -> float:
    """Annualize a 21-trading-day sum of daily variance contributions."""

    return (
        CONVENTIONS.trading_days_per_year / CONVENTIONS.robustness_trading_days
    ) * hvar


def select_forward_30c(
    origin: date,
    dated_values: Sequence[tuple[date, float]],
    *,
    require_complete_calendar: bool = True,
    last_available: date | None = None,
) -> list[float] | None:
    """Values whose dates ``d`` satisfy ``origin < d <= origin + 30c``.

    When ``require_complete_calendar`` is true, return ``None`` unless the
    full calendar interval has been observed. The window is never shortened.
    """

    origin = as_date(origin)
    horizon_end = primary_horizon_end(origin)
    selected = [value for day, value in dated_values if origin < as_date(day) <= horizon_end]
    if require_complete_calendar:
        observed_end = last_available
        if observed_end is None and dated_values:
            observed_end = max(as_date(day) for day, _ in dated_values)
        if observed_end is None or as_date(observed_end) < horizon_end:
            return None
    if not selected:
        return None
    return selected


def select_forward_21t(
    origin: date,
    dated_values: Sequence[tuple[date, float]],
) -> list[float] | None:
    """The next 21 post-origin observations in date order, or ``None`` if short."""

    origin = as_date(origin)
    after = [(as_date(day), value) for day, value in dated_values if as_date(day) > origin]
    after.sort(key=lambda item: item[0])
    need = CONVENTIONS.robustness_trading_days
    if len(after) < need:
        return None
    return [value for _, value in after[:need]]


def realized_variance_30c(
    origin: date,
    return_pairs: Sequence[tuple[date, float]],
    *,
    require_complete_calendar: bool = True,
    last_available: date | None = None,
) -> float | None:
    """Annualized close-to-close ``RVAR`` over the exact forward 30 calendar days."""

    selected = select_forward_30c(
        origin,
        return_pairs,
        require_complete_calendar=require_complete_calendar,
        last_available=last_available,
    )
    if selected is None:
        return None
    hvar = sum(value * value for value in selected)
    return annualize_hvar_30c(hvar)


def realized_variance_21t(
    origin: date,
    return_pairs: Sequence[tuple[date, float]],
) -> float | None:
    """Annualized close-to-close ``RVAR`` over the next 21 trading-day returns."""

    selected = select_forward_21t(origin, return_pairs)
    if selected is None:
        return None
    hvar = sum(value * value for value in selected)
    return annualize_hvar_21t(hvar)


def realized_volatility(rvar: float) -> float:
    """``RVOL = sqrt(RVAR)``."""

    return math.sqrt(rvar)
