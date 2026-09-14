"""Overlap-aware mean inference locked by Protocol 1.0.1.

Primary HAC uses a Bartlett kernel with ``maxlags = L0``, where ``L0`` is the
greatest ordered origin lag whose 30-calendar-day target date sets overlap.
The 21-trading-day robustness design uses ``maxlags = 20``. Bandwidth is never
selected by significance; ``maxlags`` must be supplied.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Sequence

from vrp.config import CONVENTIONS
from vrp.dates import as_date


def newey_west_mean(values: Sequence[float], maxlags: int) -> dict[str, float]:
    """HAC mean with a Bartlett kernel. ``maxlags`` is required, not estimated."""

    if maxlags < 0:
        raise ValueError("maxlags must be non-negative")
    sample = [float(item) for item in values]
    n_obs = len(sample)
    if n_obs == 0:
        raise ValueError("HAC mean requires observations")
    mean = sum(sample) / n_obs
    residuals = [item - mean for item in sample]
    gamma0 = sum(item * item for item in residuals) / n_obs
    hac = gamma0
    for lag in range(1, maxlags + 1):
        if lag >= n_obs:
            break
        gamma = sum(residuals[index] * residuals[index - lag] for index in range(lag, n_obs)) / n_obs
        weight = 1.0 - lag / (maxlags + 1)
        hac += 2.0 * weight * gamma
    variance = hac / n_obs
    se = math.sqrt(variance) if variance > 0 else 0.0
    t_stat = mean / se if se > 0 else math.inf
    return {
        "mean": mean,
        "standard_error": se,
        "t_statistic": t_stat,
        "n_obs": float(n_obs),
        "maxlags": float(maxlags),
    }


def overlap_l0(
    origins: Sequence[date | str],
    trading_dates: Sequence[date | str],
    *,
    horizon_calendar_days: int | None = None,
) -> int:
    """Greatest origin lag whose primary 30-calendar-day target date sets overlap.

    ``L0`` is derived mechanically from the exchange calendar and the eligible
    origin sequence. It is not chosen from estimated serial correlation.
    """

    horizon = (
        CONVENTIONS.primary_calendar_days
        if horizon_calendar_days is None
        else horizon_calendar_days
    )
    origin_days = [as_date(item) for item in origins]
    sessions = [as_date(item) for item in trading_dates]
    targets = []
    for origin in origin_days:
        end = origin + timedelta(days=horizon)
        targets.append({day for day in sessions if origin < day <= end})
    l0 = 0
    for lag in range(1, len(origin_days)):
        overlaps = any(
            targets[index] & targets[index + lag]
            for index in range(len(origin_days) - lag)
        )
        if overlaps:
            l0 = lag
    return l0
