"""Close-to-close logarithmic returns.

Protocol 1.0.1 dates each return at the return-ending exchange date:
``r_t = ln(C_t / C_{t-1})``. The first observation is missing by construction.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Sequence


def log_returns(dates: Sequence[date], closes: Sequence[float]) -> list[tuple[date, float]]:
    """Return ``(ending_date, r_t)`` pairs for strictly positive closes."""

    if len(dates) != len(closes):
        raise ValueError("dates and closes must have the same length")
    out: list[tuple[date, float]] = []
    for index in range(1, len(closes)):
        previous = closes[index - 1]
        current = closes[index]
        if previous is None or current is None or previous <= 0 or current <= 0:
            raise ValueError("log returns require strictly positive closes")
        out.append((dates[index], math.log(current / previous)))
    return out
