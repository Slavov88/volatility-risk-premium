"""Deterministic predictor-origin alignment without empirical VRP output."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Sequence

from vrp.calendar import is_exchange_session
from vrp.config import CONVENTIONS
from vrp.dates import as_date
from vrp.premium import ivar_from_vix, ivol_from_vix


@dataclass(frozen=True)
class OriginRow:
    origin: date
    vix_close: float
    ivol: float
    ivar: float
    vix_methodology_regime: str


@dataclass(frozen=True)
class OriginAlignmentReport:
    spx_origin_candidates: int
    vix_rows_in_sample: int
    common_origins: int
    missing_vix_on_spx: tuple[str, ...]
    vix_without_spx: tuple[str, ...]


def align_origin_panel(
    spx_dates: Sequence[date | str],
    vix_closes: Sequence[tuple[date | str, float]],
) -> tuple[tuple[OriginRow, ...], OriginAlignmentReport]:
    """Align VIX predictors to S&P 500 origin sessions through 2025-12-31.

    Post-2025 S&P 500 dates may exist as target support but are intentionally
    excluded from the predictor-origin panel.
    """

    sample_start = date.fromisoformat(CONVENTIONS.sample_start)
    sample_end = date.fromisoformat(CONVENTIONS.sample_end)
    methodology_break = date.fromisoformat(CONVENTIONS.vix_weekly_methodology_start)

    normalized_spx = [as_date(day) for day in spx_dates]
    if len(normalized_spx) != len(set(normalized_spx)):
        raise ValueError("S&P origin dates must be unique")
    if any(not is_exchange_session(day) for day in normalized_spx):
        raise ValueError("S&P origin dates must be XNYS exchange sessions")
    spx_set = {
        day for day in normalized_spx
        if sample_start <= day <= sample_end
    }

    vix_map: dict[date, float] = {}
    for raw_day, raw_close in vix_closes:
        day = as_date(raw_day)
        if day in vix_map:
            raise ValueError(f"duplicate VIX date {day.isoformat()}")
        if not is_exchange_session(day):
            raise ValueError(f"VIX date {day.isoformat()} is not an XNYS session")
        close = float(raw_close)
        if not math.isfinite(close) or close <= 0.0:
            raise ValueError("VIX close must be finite and strictly positive")
        if sample_start <= day <= sample_end:
            vix_map[day] = close

    common = sorted(spx_set & set(vix_map))
    rows = tuple(
        OriginRow(
            origin=day,
            vix_close=vix_map[day],
            ivol=ivol_from_vix(vix_map[day]),
            ivar=ivar_from_vix(vix_map[day]),
            vix_methodology_regime=(
                "weekly_inclusive" if day >= methodology_break else "month_only"
            ),
        )
        for day in common
    )
    report = OriginAlignmentReport(
        spx_origin_candidates=len(spx_set),
        vix_rows_in_sample=len(vix_map),
        common_origins=len(common),
        missing_vix_on_spx=tuple(
            day.isoformat() for day in sorted(spx_set - set(vix_map))
        ),
        vix_without_spx=tuple(
            day.isoformat() for day in sorted(set(vix_map) - spx_set)
        ),
    )
    return rows, report
