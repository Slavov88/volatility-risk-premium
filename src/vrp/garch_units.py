"""Locked unit conversions around ARCH/GARCH estimation.

Internal returns are decimal log returns. For numerical conditioning, the
`arch` model is fit to percentage returns (100*r). Conditional variances
returned by the fitted model are therefore in percentage-squared units and
must be divided by 10,000 before comparison with IVAR/RVAR.
"""

from __future__ import annotations

import math
from typing import Sequence

from vrp.config import CONVENTIONS


def to_garch_fit_returns(decimal_returns: Sequence[float]) -> list[float]:
    out: list[float] = []
    for raw in decimal_returns:
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError("GARCH returns must be finite")
        out.append(CONVENTIONS.garch_fit_return_scale * value)
    return out


def from_garch_variance(percent_squared_variance: float) -> float:
    value = float(percent_squared_variance)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("GARCH variance must be finite and non-negative")
    return value / CONVENTIONS.garch_variance_backscale
