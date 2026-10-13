"""Pre-specified out-of-sample forecast-evaluation design.

Calendar completeness is checked against expected XNYS exchange sessions.
Predictors may use information dated at end-of-day origin t but never
information dated after t.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Literal, Mapping, Sequence

from vrp.calendar import (
    forward_30c_sessions,
    trailing_30c_sessions,
    trailing_exchange_sessions,
)
from vrp.config import CONVENTIONS
from vrp.dates import as_date
from vrp.targets import (
    annualize_hvar_21t,
    annualize_hvar_30c,
    assert_forecast_origin_allowed,
)

EstimationWindow = Literal["expanding", "rolling_5y"]
DatedValue = tuple[date | str, float]


@dataclass(frozen=True)
class OutOfSampleSplit:
    """Calendar-derived initial estimation dates and primary evaluation origins."""

    initial_estimation_dates: tuple[date, ...]
    evaluation_origins: tuple[date, ...]

    @property
    def initial_estimation_end(self) -> date | None:
        if not self.initial_estimation_dates:
            return None
        return self.initial_estimation_dates[-1]

    @property
    def evaluation_start(self) -> date | None:
        return self.evaluation_origins[0] if self.evaluation_origins else None


def _ordered_unique_dates(values: Sequence[date | str]) -> list[date]:
    days = [as_date(value) for value in values]
    if len(days) != len(set(days)):
        raise ValueError("dates must be unique")
    return sorted(days)


def _ordered_dated_values(values: Sequence[DatedValue]) -> list[tuple[date, float]]:
    converted = [(as_date(day), float(value)) for day, value in values]
    days = [day for day, _ in converted]
    if len(days) != len(set(days)):
        raise ValueError("dated values must have unique dates")
    if any(not math.isfinite(value) for _, value in converted):
        raise ValueError("dated values must be finite")
    return sorted(converted, key=lambda item: item[0])


def out_of_sample_split(trading_dates: Sequence[date | str]) -> OutOfSampleSplit:
    """Construct the locked train-through-2006/evaluate-from-2007 split.

    An evaluation origin is retained only if every expected XNYS session in
    its forward 30-calendar-day target is present in trading_dates.
    """

    sessions = _ordered_unique_dates(trading_dates)
    available = set(sessions)
    sample_start = date.fromisoformat(CONVENTIONS.sample_start)
    estimation_end = date(CONVENTIONS.oos_initial_estimation_end_year, 12, 31)
    evaluation_start = date(CONVENTIONS.oos_start_year, 1, 1)
    origin_end = date.fromisoformat(CONVENTIONS.sample_end)

    initial = tuple(
        day for day in sessions if sample_start <= day <= estimation_end
    )
    origins = []
    for origin in sessions:
        if not evaluation_start <= origin <= origin_end:
            continue
        expected = forward_30c_sessions(
            origin, CONVENTIONS.primary_calendar_days
        )
        if expected and all(day in available for day in expected):
            origins.append(origin)
    return OutOfSampleSplit(initial, tuple(origins))


def _subtract_years(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def estimation_window(
    origin: date | str,
    dated_returns: Sequence[DatedValue],
    *,
    window: EstimationWindow = "expanding",
) -> list[tuple[date, float]]:
    """Return GARCH estimation observations available at origin t."""

    origin_day = as_date(origin)
    assert_forecast_origin_allowed(origin_day)
    values = _ordered_dated_values(dated_returns)
    if window == "expanding":
        lower = date.fromisoformat(CONVENTIONS.sample_start)
        return [(day, value) for day, value in values if lower <= day <= origin_day]
    if window == "rolling_5y":
        lower = _subtract_years(
            origin_day, CONVENTIONS.garch_robustness_window_years
        )
        return [(day, value) for day, value in values if lower < day <= origin_day]
    raise ValueError("window must be 'expanding' or 'rolling_5y'")


def naive_variance_30c(
    origin: date | str,
    dated_returns: Sequence[DatedValue],
) -> float | None:
    """Trailing exact-calendar naive variance using every expected session."""

    origin_day = as_date(origin)
    assert_forecast_origin_allowed(origin_day)
    values = dict(_ordered_dated_values(dated_returns))
    expected = trailing_30c_sessions(
        origin_day, CONVENTIONS.primary_calendar_days
    )
    if any(day not in values for day in expected):
        return None
    return annualize_hvar_30c(
        sum(values[day] * values[day] for day in expected)
    )


def naive_variance_21t(
    origin: date | str,
    dated_returns: Sequence[DatedValue],
) -> float | None:
    """Trailing exact-21-session benchmark for the robustness analysis."""

    origin_day = as_date(origin)
    assert_forecast_origin_allowed(origin_day)
    values = dict(_ordered_dated_values(dated_returns))
    expected = trailing_exchange_sessions(
        origin_day, CONVENTIONS.robustness_trading_days
    )
    if any(day not in values for day in expected):
        return None
    return annualize_hvar_21t(
        sum(values[day] * values[day] for day in expected)
    )


def _normalize_variance_map(
    values: Mapping[date | str, float | None],
    *,
    name: str,
) -> dict[date, float | None]:
    normalized: dict[date, float | None] = {}
    for raw_day, raw_value in values.items():
        day = as_date(raw_day)
        if day in normalized:
            raise ValueError(f"{name} has duplicate normalized date {day.isoformat()}")
        if raw_value is None:
            normalized[day] = None
            continue
        value = float(raw_value)
        if math.isnan(value):
            normalized[day] = None
            continue
        if not math.isfinite(value):
            raise ValueError(f"{name} must contain finite values or missing values")
        if value < 0:
            raise ValueError(f"{name} variance must be non-negative")
        normalized[day] = value
    return normalized


def common_evaluation_mask(
    candidate_origins: Sequence[date | str],
    realized_target: Mapping[date | str, float | None],
    forecasts: Mapping[str, Mapping[date | str, float | None]],
) -> tuple[date, ...]:
    """Return origins observed for target and all three pre-specified forecasts."""

    required = {"vix", "garch", "naive"}
    if set(forecasts) != required:
        raise ValueError(
            "formal comparison requires exactly vix, garch, and naive forecasts"
        )
    origins = _ordered_unique_dates(candidate_origins)
    targets = _normalize_variance_map(realized_target, name="realized_target")
    normalized_forecasts = {
        name: _normalize_variance_map(values, name=name)
        for name, values in forecasts.items()
    }

    common = []
    for origin in origins:
        assert_forecast_origin_allowed(origin)
        if targets.get(origin) is None:
            continue
        if any(
            values.get(origin) is None
            for values in normalized_forecasts.values()
        ):
            continue
        common.append(origin)
    return tuple(common)
