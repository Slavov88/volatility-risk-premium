"""Configuration-light, audited U.S. cross-market panel construction."""
from __future__ import annotations

from datetime import date, timedelta
import math
import numpy as np
import pandas as pd
import exchange_calendars as xc

from vrp.inference import nonoverlapping_origins_30c, overlap_l0
from vrp.provisional_analysis import checked_mean, checked_regression

US_CALENDAR = "XNYS"
ANALYSIS_CUTOFF = date(2025, 12, 31)


def build_close_panel(underlying: pd.DataFrame, implied: pd.DataFrame, *,
                      underlying_date: str, underlying_close: str,
                      implied_date: str, implied_close: str,
                      cutoff: date = ANALYSIS_CUTOFF) -> pd.DataFrame:
    """Build complete CC targets from close-only index observations.

    Target membership uses actual XNYS sessions. Forecast origins are limited
    to the registered origin cutoff, while realized target observations may
    extend through the final target horizon (the cutoff is not an outcome
    cutoff). This function refuses incomplete windows and does not fill data.
    """
    u = underlying[[underlying_date, underlying_close]].copy()
    v = implied[[implied_date, implied_close]].copy()
    u.columns = ["date", "underlying"]
    v.columns = ["date", "implied_points"]
    u["date"] = pd.to_datetime(u.date, errors="raise").dt.date
    v["date"] = pd.to_datetime(v.date, errors="raise").dt.date
    for frame, col in ((u, "underlying"), (v, "implied_points")):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
        if frame.date.duplicated().any() or not frame.date.is_monotonic_increasing:
            raise ValueError(f"{col}: dates must be unique and ordered")
        if frame[col].isna().any() or not np.isfinite(frame[col]).all() or not frame[col].gt(0).all():
            raise ValueError(f"{col}: values must be finite, positive, and complete")
    # The project-wide XNYS helper is intentionally bounded to 1989 onward;
    # Nasdaq's source starts in 1986, so construct the same named calendar with
    # an explicit historical bound for source-session validation and warm-up.
    cal_end = max(u.date.max(), cutoff + timedelta(days=90))
    cal = xc.get_calendar(US_CALENDAR, start=u.date.min().isoformat(), end=cal_end.isoformat())
    all_sessions = {ts.date() for ts in cal.sessions_in_range(u.date.min(), u.date.max())}
    u_sessions, v_sessions = set(u.date), set(v.date)
    if u_sessions - all_sessions:
        raise ValueError(f"underlying has {len(u_sessions-all_sessions)} non-session dates; quarantine before panel construction")
    if not v_sessions.issubset(all_sessions):
        raise ValueError(f"implied series contains {len(v_sessions-all_sessions)} non-XNYS dates")
    merged = u.merge(v, on="date", how="inner", validate="one_to_one").sort_values("date")
    if merged.empty:
        raise ValueError("underlying and implied data have no common dates")
    # A source gap must not turn a two-session return into a one-day return.
    # Only compute a daily close return when both adjacent actual sessions
    # have observed underlying closes.
    underlying_map = dict(zip(u.date, u.underlying))
    ordered_sessions = sorted(all_sessions)
    return_map = {}
    for previous, current in zip(ordered_sessions[:-1], ordered_sessions[1:]):
        if previous in underlying_map and current in underlying_map:
            return_map[current] = math.log(underlying_map[current] / underlying_map[previous])
    iv_map = dict(zip(merged.date, (merged.implied_points / 100.0) ** 2))
    origin_dates = [d for d in merged.date if d <= cutoff]
    rows = []
    for origin in origin_dates:
        sessions30 = [x.date() for x in cal.sessions_in_range(origin + timedelta(days=1), origin + timedelta(days=30))]
        sessions_long = [x.date() for x in cal.sessions_in_range(origin + timedelta(days=1), origin + timedelta(days=90))]
        sessions21 = sessions_long[:21]
        if len(sessions21) != 21:
            continue
        if any(d not in return_map for d in sessions30 + sessions21):
            continue
        rvar30 = 365 / 30 * sum(return_map[d] ** 2 for d in sessions30)
        rvar21 = 252 / 21 * sum(return_map[d] ** 2 for d in sessions21)
        rows.append({"origin": origin.isoformat(), "underlying_close": float(merged.loc[merged.date.eq(origin), "underlying"].iloc[0]),
                     "implied_points": float(merged.loc[merged.date.eq(origin), "implied_points"].iloc[0]),
                     "ivar": iv_map[origin], "rvar_30c": rvar30, "rvar_21t": rvar21,
                     "vrp_30c": iv_map[origin]-rvar30, "vrp_21t": iv_map[origin]-rvar21,
                     "n_sessions_30c": len(sessions30), "target_30c_start": sessions30[0].isoformat(),
                     "target_30c_end": (origin + timedelta(days=30)).isoformat(),
                     "target_21t_end": sessions21[-1].isoformat()})
    out = pd.DataFrame(rows)
    if out.origin.duplicated().any() or out.origin.tolist() != sorted(out.origin.tolist()):
        raise ValueError("constructed origin panel is not unique chronological")
    return out


def evaluate_h1_h2(panel: pd.DataFrame) -> dict:
    """Run fixed primary and registered horizon/period H1-H2 analyses."""
    outputs = {"h1": [], "h2": []}
    if panel.empty:
        raise ValueError("empty panel")
    for period, lower in (("maximum_available", panel.origin.iloc[0]), ("post_2014", "2014-10-06")):
        sample = panel.loc[panel.origin >= lower].copy()
        for horizon, ycol, vrpcol in (("30c", "rvar_30c", "vrp_30c"), ("21t", "rvar_21t", "vrp_21t")):
            l0 = overlap_l0(sample.origin.tolist())
            primary_lag = l0 if horizon == "30c" else 20
            for lag in dict.fromkeys((primary_lag, 42, 63) if horizon == "30c" else (20, 10, 21, 42)):
                outputs["h1"].append({"period": period, "horizon": horizon, "lag": lag,
                    "n": len(sample), **checked_mean(sample[vrpcol].to_numpy(), lag)})
                outputs["h2"].append({"period": period, "horizon": horizon, "lag": lag,
                    **checked_regression(sample[ycol].to_numpy(), sample.ivar.to_numpy(), lag,
                                         np.eye(2), [0.0, 1.0])})
        if period == "maximum_available":
            chosen = {x.isoformat() for x in nonoverlapping_origins_30c(sample.origin.tolist())}
            nonoverlap = sample.loc[sample.origin.isin(chosen)]
            outputs["h1"].append({"period": period, "horizon": "30c_nonoverlap", "lag": 0,
                "n": len(nonoverlap), **checked_mean(nonoverlap.vrp_30c.to_numpy(), 0)})
            outputs["h2"].append({"period": period, "horizon": "30c_nonoverlap", "lag": 0,
                **checked_regression(nonoverlap.rvar_30c.to_numpy(), nonoverlap.ivar.to_numpy(), 0,
                                     np.eye(2), [0.0, 1.0])})
    return outputs

