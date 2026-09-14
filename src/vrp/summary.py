"""Descriptive summary statistics required by Protocol 1.0.1 §9.

Reported moments are mean, standard deviation, skewness, excess kurtosis,
selected quantiles, median, min/max, and the proportion of positive values.
Central moments use the sample-size divisor ``n`` so a constant series has
zero variance. Quantiles use linear interpolation on the order statistics.
"""

from __future__ import annotations

import math
from typing import Sequence


def summary_statistics(values: Sequence[float]) -> dict[str, float]:
    """Return the protocol-required descriptive statistics for a numeric series."""

    sample = [float(item) for item in values]
    n_obs = len(sample)
    if n_obs == 0:
        return {"n_obs": 0.0}
    ordered = sorted(sample)
    mean = sum(sample) / n_obs
    centered = [item - mean for item in sample]
    second = sum(item * item for item in centered) / n_obs
    std = math.sqrt(second)
    third = sum(item**3 for item in centered) / n_obs
    fourth = sum(item**4 for item in centered) / n_obs
    skewness = 0.0 if second == 0 else third / (second ** 1.5)
    excess_kurtosis = 0.0 if second == 0 else fourth / (second**2) - 3.0
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
        "proportion_positive": sum(1 for item in sample if item > 0) / n_obs,
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
