"""Descriptive summary statistics required by Protocol 1.1.0.

The convention is fixed before empirical outputs: sample standard deviation
(ddof=1), bias-corrected Fisher-Pearson skewness, and bias-corrected Fisher
excess kurtosis. Quantiles use linear interpolation on positions q*(n-1).
"""

from __future__ import annotations

import math
from typing import Sequence


def summary_statistics(values: Sequence[float]) -> dict[str, float]:
    """Return protocol-required descriptive statistics for a finite series."""

    sample = [float(item) for item in values]
    if any(not math.isfinite(item) for item in sample):
        raise ValueError("summary statistics require only finite values")
    n_obs = len(sample)
    if n_obs == 0:
        return {"n_obs": 0.0}

    ordered = sorted(sample)
    mean = sum(sample) / n_obs
    centered = [item - mean for item in sample]
    sum2 = sum(item * item for item in centered)
    m2 = sum2 / n_obs
    std = math.sqrt(sum2 / (n_obs - 1)) if n_obs >= 2 else math.nan

    if m2 == 0.0:
        skewness = 0.0
        excess_kurtosis = 0.0
    else:
        m3 = sum(item**3 for item in centered) / n_obs
        m4 = sum(item**4 for item in centered) / n_obs
        g1 = m3 / (m2 ** 1.5)
        g2 = m4 / (m2**2) - 3.0
        skewness = (
            math.sqrt(n_obs * (n_obs - 1)) / (n_obs - 2) * g1
            if n_obs >= 3
            else math.nan
        )
        excess_kurtosis = (
            ((n_obs - 1) / ((n_obs - 2) * (n_obs - 3)))
            * ((n_obs + 1) * g2 + 6.0)
            if n_obs >= 4
            else math.nan
        )

    return {
        "n_obs": float(n_obs),
        "mean": mean,
        "std": std,
        "min": ordered[0],
        "max": ordered[-1],
        "median": _quantile(ordered, 0.5),
        "q01": _quantile(ordered, 0.01),
        "q05": _quantile(ordered, 0.05),
        "q25": _quantile(ordered, 0.25),
        "q75": _quantile(ordered, 0.75),
        "q95": _quantile(ordered, 0.95),
        "q99": _quantile(ordered, 0.99),
        "skewness": skewness,
        "excess_kurtosis": excess_kurtosis,
        "proportion_positive": (
            sum(1 for item in sample if item > 0) / n_obs
        ),
    }


def _quantile(ordered: Sequence[float], q: float) -> float:
    if not ordered:
        return math.nan
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    low = int(math.floor(position))
    high = int(math.ceil(position))
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight
