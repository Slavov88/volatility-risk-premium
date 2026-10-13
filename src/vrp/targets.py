"""Exchange-calendar-safe forward realized-variance targets.

Primary horizon: exact forward 30 calendar days, annualized by 365/30.
Mandatory robustness: the exact next 21 XNYS sessions, annualized by 252/21.
A target is complete only when every expected return-ending exchange session
is present. Missing sessions are never replaced by later observations.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Sequence

from vrp.calendar import (
    forward_30c_sessions,
    is_exchange_session,
    next_exchange_sessions,
)
from vrp.config import CONVENTIONS
from vrp.dates import as_date


def forecast_origin_end() -> date:
    return date.fromisoformat(CONVENTIONS.sample_end)


def sample_start() -> date:
    return date.fromisoformat(CONVENTIONS.sample_start)


def assert_forecast_origin_allowed(origin: date) -> None:
    """Enforce the locked forecast-origin sample and exchange calendar."""

    origin_day = as_date(origin)
    if origin_day > forecast_origin_end():
        raise ValueError(
            f"forecast origin {origin_day.isoformat()} is after locked cutoff "
            f"{CONVENTIONS.sample_end}"
        )
    if origin_day < sample_start():
        raise ValueError(
            f"forecast origin {origin_day.isoformat()} is before sample start "
            f"{CONVENTIONS.sample_start}"
        )
    if not is_exchange_session(origin_day):
        raise ValueError(
            f"forecast origin {origin_day.isoformat()} is not an XNYS session"
        )


def primary_horizon_end(origin: date) -> date:
    """Calendar date t + 30 days for origin t."""

    return as_date(origin) + timedelta(days=CONVENTIONS.primary_calendar_days)


def annualize_hvar_30c(hvar: float) -> float:
    """Annualize a 30-calendar-day sum of daily variance contributions."""

    value = float(hvar)
    if not math.isfinite(value) or value < 0:
        raise ValueError("30c holding-period variance must be finite and non-negative")
    return (
        CONVENTIONS.calendar_days_per_year / CONVENTIONS.primary_calendar_days
    ) * value


def annualize_hvar_21t(hvar: float) -> float:
    """Annualize a 21-trading-day sum of daily variance contributions."""

    value = float(hvar)
    if not math.isfinite(value) or value < 0:
        raise ValueError("21t holding-period variance must be finite and non-negative")
    return (
        CONVENTIONS.trading_days_per_year / CONVENTIONS.robustness_trading_days
    ) * value


def _dated_value_map(
    dated_values: Sequence[tuple[date, float]],
) -> dict[date, float]:
    mapping: dict[date, float] = {}
    for raw_day, raw_value in dated_values:
        day = as_date(raw_day)
        if day in mapping:
            raise ValueError(f"duplicate dated value for {day.isoformat()}")
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError("dated target inputs must be finite")
        mapping[day] = value
    return mapping


def select_forward_30c(
    origin: date,
    dated_values: Sequence[tuple[date, float]],
) -> list[float] | None:
    """Select the exact expected XNYS-session values in the 30c window.

    The function intentionally has no partial-window mode. A confirmatory
    target is either complete on the deterministic exchange calendar or
    missing.
    """

    origin_day = as_date(origin)
    assert_forecast_origin_allowed(origin_day)
    expected = forward_30c_sessions(
        origin_day, CONVENTIONS.primary_calendar_days
    )
    values = _dated_value_map(dated_values)
    if any(day not in values for day in expected):
        return None
    return [values[day] for day in expected]


def select_forward_21t(
    origin: date,
    dated_values: Sequence[tuple[date, float]],
) -> list[float] | None:
    """Select the exact next 21 expected XNYS-session values."""

    origin_day = as_date(origin)
    assert_forecast_origin_allowed(origin_day)
    expected = next_exchange_sessions(
        origin_day, CONVENTIONS.robustness_trading_days
    )
    values = _dated_value_map(dated_values)
    if any(day not in values for day in expected):
        return None
    return [values[day] for day in expected]


def realized_variance_30c(
    origin: date,
    return_pairs: Sequence[tuple[date, float]],
) -> float | None:
    """Annualized close-to-close RVAR over the exact forward 30 calendar days."""

    selected = select_forward_30c(origin, return_pairs)
    if selected is None:
        return None
    return annualize_hvar_30c(sum(value * value for value in selected))


def realized_variance_21t(
    origin: date,
    return_pairs: Sequence[tuple[date, float]],
) -> float | None:
    """Annualized close-to-close RVAR over the exact next 21 XNYS sessions."""

    selected = select_forward_21t(origin, return_pairs)
    if selected is None:
        return None
    return annualize_hvar_21t(sum(value * value for value in selected))


def realized_volatility(rvar: float) -> float:
    """RVOL = sqrt(RVAR)."""

    value = float(rvar)
    if not math.isfinite(value) or value < 0:
        raise ValueError("realized variance must be finite and non-negative")
    return math.sqrt(value)
