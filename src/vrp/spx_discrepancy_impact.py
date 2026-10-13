"""Hypothetical close-correction footprint, not production RVAR computation.

No price series is changed. Only signed log-return adjustments and affected
calendar-origin sets are reported. No realized variance, VRP or inference.
"""
from __future__ import annotations

from datetime import date, timedelta
import math
from typing import Mapping, Sequence

from vrp.calendar import forward_30c_sessions, next_exchange_sessions, trailing_exchange_sessions
from vrp.dates import as_date


def correction_footprint(
    dates: Sequence[date | str], closes: Sequence[float],
    replacements: Mapping[date | str, float], origins: Sequence[date | str],
) -> list[dict]:
    """Single-date sensitivity proposals evaluated one at a time.

    C_s -> C'_s changes r_s by e=log(C'_s/C_s), r_next by -e.
    Target membership depends only on dates. No target value is computed.
    """
    days = [as_date(d) for d in dates]
    if len(days) != len(closes) or any(a >= b for a,b in zip(days,days[1:])):
        raise ValueError("Unique increasing dates and aligned closes required")
    if any(not math.isfinite(float(c)) or float(c) <= 0 for c in closes):
        raise ValueError("Finite positive closes required")
    candidates = sorted(as_date(d) for d in origins)
    if len(candidates) != len(set(candidates)):
        raise ValueError("Unique origins required")
    prices = dict(zip(days,closes))
    result = []
    for raw_day, replacement in replacements.items():
        day = as_date(raw_day)
        if day not in prices or not math.isfinite(float(replacement)) or replacement <= 0:
            raise ValueError("Replacement requires an observed date and finite positive close")
        index = days.index(day)
        if index == 0 or index == len(days)-1:
            raise ValueError("Correction footprint requires both adjacent price sessions")
        next_day = days[index+1]
        if next_exchange_sessions(day,1) != (next_day,):
            raise ValueError("Missing next exchange session")
        if next_exchange_sessions(days[index-1],1) != (day,):
            raise ValueError("Missing previous exchange session")
        epsilon = math.log(float(replacement) / float(prices[day]))
        affected = {day,next_day}
        sets = {"30c":[],"21t":[]}
        earliest = min(day-timedelta(days=30), trailing_exchange_sessions(day,22)[0])
        for origin in candidates:
            # Derive the earliest possible origin from the actual calendar,
            # including closures; never impose a heuristic calendar-day cap.
            if origin >= next_day or origin < earliest:
                continue
            for horizon, target in (("30c",forward_30c_sessions(origin)),
                    ("21t",next_exchange_sessions(origin,21))):
                if affected.intersection(target):
                    sets[horizon].append(origin.isoformat())
        result.append({"correction_date":day.isoformat(),
            "affected_return_end_dates":[day.isoformat(),next_day.isoformat()],
            "signed_log_return_adjustments":[epsilon,-epsilon],
            "affected_origins":sets,
            "affected_origin_counts":{h:len(ds) for h,ds in sets.items()},
            "status":"HYPOTHETICAL_ONLY_NO_SOURCE_CORRECTION",
            "variance_change_formula":"For included affected returns: (r+delta)^2-r^2 = 2*r*delta+delta^2; multiply by locked horizon annualizer. No target value computed.",
            "combined_corrections_note":"Adjacent proposed close changes can affect the same return; combine signed adjustments before squaring, never add single-correction squared impacts blindly."})
    return result
