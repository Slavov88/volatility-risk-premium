"""Overlap-aware HAC inference utilities.

The mean estimator is cross-checked through statsmodels' HAC implementation
with a Bartlett kernel and finite-sample correction. Regression-HAC fitting is
provided as infrastructure for later H2/H4/H5 work; this module does not run
any empirical specification by itself.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Sequence

import numpy as np
import statsmodels.api as sm

from vrp.calendar import forward_30c_sessions
from vrp.config import CONVENTIONS
from vrp.dates import as_date
from vrp.targets import assert_forecast_origin_allowed, primary_horizon_end


def _finite_vector(values: Sequence[float], *, name: str) -> np.ndarray:
    sample = np.asarray([float(item) for item in values], dtype=float)
    if sample.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if sample.size == 0:
        raise ValueError(f"{name} requires observations")
    if not np.isfinite(sample).all():
        raise ValueError(f"{name} must contain only finite values")
    return sample


def fit_hac_ols(
    y: Sequence[float],
    predictors: Sequence[Sequence[float]] | np.ndarray,
    *,
    maxlags: int,
    add_constant: bool = True,
):
    """Fit OLS with overlap-aware statsmodels HAC covariance.

    This is a reusable utility for later calibration, encompassing, regime,
    and loss-differential regressions. It performs no model selection.
    """

    if maxlags < 0:
        raise ValueError("maxlags must be non-negative")
    y_array = _finite_vector(y, name="HAC regression dependent variable")
    x_array = np.asarray(predictors, dtype=float)
    if x_array.ndim == 1:
        x_array = x_array.reshape(-1, 1)
    if x_array.ndim != 2:
        raise ValueError("predictors must be a one- or two-dimensional array")
    if x_array.shape[0] != y_array.shape[0]:
        raise ValueError("predictors and dependent variable must have equal rows")
    if not np.isfinite(x_array).all():
        raise ValueError("predictors must contain only finite values")
    if add_constant:
        x_array = sm.add_constant(x_array, has_constant="add")
    if x_array.shape[0] <= x_array.shape[1]:
        raise ValueError("HAC regression requires more observations than parameters")
    return sm.OLS(y_array, x_array).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": maxlags, "use_correction": True},
        use_t=False,
    )


def newey_west_mean(values: Sequence[float], maxlags: int) -> dict[str, float]:
    """Estimate a mean with Bartlett/Newey-West HAC covariance."""

    if maxlags < 0:
        raise ValueError("maxlags must be non-negative")
    sample = _finite_vector(values, name="HAC mean")
    if sample.size < 2:
        raise ValueError("HAC mean requires at least two observations")

    mean = float(sample.mean())
    residual_scale = float(np.max(np.abs(sample - mean)))
    if residual_scale == 0.0:
        if mean == 0.0:
            t_stat = 0.0
            p_value = 1.0
        else:
            t_stat = math.copysign(math.inf, mean)
            p_value = 0.0
        return {
            "mean": mean,
            "standard_error": 0.0,
            "t_statistic": t_stat,
            "p_value": p_value,
            "ci_lower": mean,
            "ci_upper": mean,
            "n_obs": float(sample.size),
            "maxlags": float(maxlags),
        }

    result = sm.OLS(sample, np.ones((sample.size, 1))).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": maxlags, "use_correction": True},
        use_t=False,
    )
    ci = result.conf_int(alpha=CONVENTIONS.significance_level)[0]
    return {
        "mean": float(result.params[0]),
        "standard_error": float(result.bse[0]),
        "t_statistic": float(result.tvalues[0]),
        "p_value": float(result.pvalues[0]),
        "ci_lower": float(ci[0]),
        "ci_upper": float(ci[1]),
        "n_obs": float(sample.size),
        "maxlags": float(maxlags),
    }


def overlap_l0(
    origins: Sequence[date | str],
    trading_dates: Sequence[date | str] | None = None,
    *,
    horizon_calendar_days: int | None = None,
) -> int:
    """Greatest ordered-origin lag whose expected target session sets overlap.

    Target sets come from the deterministic XNYS calendar, not from observed
    outcome values. The optional trading_dates argument is retained for API
    compatibility and is validated for uniqueness but does not define target
    completeness.
    """

    horizon = (
        CONVENTIONS.primary_calendar_days
        if horizon_calendar_days is None
        else int(horizon_calendar_days)
    )
    if horizon <= 0:
        raise ValueError("horizon_calendar_days must be positive")

    origin_days = [as_date(item) for item in origins]
    if len(origin_days) != len(set(origin_days)):
        raise ValueError("origins must be unique")
    origin_days = sorted(origin_days)
    for origin in origin_days:
        assert_forecast_origin_allowed(origin)

    if trading_dates is not None:
        supplied = [as_date(item) for item in trading_dates]
        if len(supplied) != len(set(supplied)):
            raise ValueError("trading_dates must be unique")

    targets = [
        set(forward_30c_sessions(origin, horizon))
        for origin in origin_days
    ]
    l0 = 0
    for lag in range(1, len(origin_days)):
        if any(
            targets[index] & targets[index + lag]
            for index in range(len(origin_days) - lag)
        ):
            l0 = lag
    return l0



def nonoverlapping_origins_30c(
    origins: Sequence[date | str],
) -> tuple[date, ...]:
    """Select the deterministic earliest-phase non-overlapping 30c origins.

    Starting with the earliest eligible origin, retain the earliest later
    origin strictly after the previous selected origin's calendar endpoint.
    Selection depends only on origin dates and the locked horizon, never on
    outcomes.
    """

    days = [as_date(item) for item in origins]
    if len(days) != len(set(days)):
        raise ValueError("origins must be unique")
    ordered = sorted(days)
    for origin in ordered:
        assert_forecast_origin_allowed(origin)

    selected: list[date] = []
    previous_end: date | None = None
    for origin in ordered:
        if previous_end is None or origin > previous_end:
            selected.append(origin)
            previous_end = primary_horizon_end(origin)
    return tuple(selected)


def holm_adjust_two(pvalues: Sequence[float]) -> tuple[float, float]:
    """Holm-adjust exactly the two pre-specified secondary H3 p-values."""

    if len(pvalues) != 2:
        raise ValueError("H3 secondary Holm family must contain exactly two p-values")
    values = [float(value) for value in pvalues]
    if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in values):
        raise ValueError("p-values must be finite and lie in [0, 1]")
    order = sorted(range(2), key=values.__getitem__)
    adjusted = [0.0, 0.0]
    first, second = order
    adjusted[first] = min(1.0, 2.0 * values[first])
    adjusted[second] = min(1.0, max(adjusted[first], values[second]))
    return adjusted[0], adjusted[1]
