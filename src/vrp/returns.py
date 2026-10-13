"""Close-to-close logarithmic returns with exchange-session integrity checks.

Each return is dated by its ending exchange session. By default, price dates
must be consecutive XNYS sessions so a missing market day can never be bridged
silently into one ordinary daily return.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Sequence

from vrp.calendar import exchange_sessions, is_exchange_session
from vrp.dates import as_date


def log_returns(
    dates: Sequence[date],
    closes: Sequence[float],
) -> list[tuple[date, float]]:
    """Return (ending_date, r_t) pairs for finite, strictly positive closes.

    Every supplied date must be an XNYS session and each adjacent pair must be
    consecutive exchange sessions. Production return construction has no
    partial-calendar bypass.
    """

    if len(dates) != len(closes):
        raise ValueError("dates and closes must have the same length")

    normalized_dates = [as_date(day) for day in dates]
    if any(
        current <= previous
        for previous, current in zip(normalized_dates, normalized_dates[1:])
    ):
        raise ValueError("price dates must be strictly increasing and unique")

    numeric_closes: list[float] = []
    for close in closes:
        if close is None:
            raise ValueError("log returns require finite, strictly positive closes")
        value = float(close)
        if not math.isfinite(value) or value <= 0:
            raise ValueError("log returns require finite, strictly positive closes")
        numeric_closes.append(value)

    for day in normalized_dates:
        if not is_exchange_session(day):
            raise ValueError(f"price date {day.isoformat()} is not an XNYS session")
    for previous, current in zip(normalized_dates, normalized_dates[1:]):
        expected = exchange_sessions(previous, current)
        if expected != (previous, current):
            missing = [
                day.isoformat()
                for day in expected
                if day not in {previous, current}
            ]
            detail = ", ".join(missing) if missing else "calendar mismatch"
            raise ValueError(
                "price dates are not consecutive exchange sessions; "
                f"between {previous.isoformat()} and {current.isoformat()}: {detail}"
            )

    out: list[tuple[date, float]] = []
    for index in range(1, len(numeric_closes)):
        out.append(
            (
                normalized_dates[index],
                math.log(numeric_closes[index] / numeric_closes[index - 1]),
            )
        )
    return out
