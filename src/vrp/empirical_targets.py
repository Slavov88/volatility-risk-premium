"""Complete forward targets and independent numerical audit; no inference."""
from __future__ import annotations

from datetime import timedelta
import math

import numpy as np
import pandas as pd

from vrp.calendar import forward_30c_sessions, next_exchange_sessions
from vrp.dates import as_date
from vrp.interim_panel import REVIEW
from vrp.premium import ivar_from_vix, ivol_from_vix, volgap, vrp_x
from vrp.range_estimators import (garman_klass_daily, parkinson_daily,
    realized_range_variance_21t, realized_range_variance_30c)
from vrp.returns import log_returns
from vrp.summary import summary_statistics
from vrp.targets import (assert_forecast_origin_allowed, realized_variance_21t,
    realized_variance_30c, realized_volatility)

TARGET_VERSION = "complete-forward-targets/1.0.0"
FAMILIES = ("cc", "parkinson", "gk")
HORIZONS = ("30c", "21t")


def construct_targets(spx: pd.DataFrame, panel: pd.DataFrame):
    """Build returns from ALL SPX rows before masking predictor origins.

    Supply only expected-window pairs to existing selectors to avoid rebuilding
    a full-history dictionary for each target. Selectors still independently
    reject any missing expected date; no partial target mode exists.
    """
    dates = [as_date(d) for d in spx.Date]
    returns = log_returns(dates, spx.Close.tolist())
    if panel.origin.duplicated().any() or panel.origin.tolist() != sorted(panel.origin):
        raise ValueError("Predictor origins must be unique and sorted")
    if not set(panel.origin).issubset(set(spx.Date)):
        raise ValueError("Every predictor requires an observed SPX origin")
    maps = {"cc": dict(returns),
        "parkinson": {d: parkinson_daily(h, l) for d, h, l in zip(dates, spx.High, spx.Low)},
        "gk": {d: garman_klass_daily(o, h, l, c)
            for d, o, h, l, c in zip(dates, spx.Open, spx.High, spx.Low, spx.Close)}}
    daily = spx.copy(deep=True)
    daily["log_return"] = [maps["cc"].get(d, math.nan) for d in dates]
    daily["parkinson_daily"] = [maps["parkinson"][d] for d in dates]
    daily["gk_daily"] = [maps["gk"][d] for d in dates]
    records = []
    for original in panel.to_dict("records"):
        origin = as_date(original["origin"]); assert_forecast_origin_allowed(origin)
        if (not math.isfinite(float(original["vix_close"])) or original["vix_close"] <= 0 or
            original["ivar"] != ivar_from_vix(original["vix_close"]) or
            original["ivol"] != ivol_from_vix(original["vix_close"])):
            raise ValueError("Predictor unit/value mismatch")
        record = dict(original)
        for horizon in HORIZONS:
            sessions = forward_30c_sessions(origin) if horizon == "30c" else next_exchange_sessions(origin, 21)
            record["target_session_count_" + horizon] = len(sessions)
            record["target_first_session_" + horizon] = sessions[0].isoformat()
            record["target_last_session_" + horizon] = sessions[-1].isoformat()
            record["target_end_date_" + horizon] = ((origin + timedelta(days=30)).isoformat()
                if horizon == "30c" else sessions[-1].isoformat())
            for family in FAMILIES:
                pairs = [(d, maps[family][d]) for d in sessions if d in maps[family]]
                function = ({"30c": realized_variance_30c, "21t": realized_variance_21t}
                    if family == "cc" else {"30c": realized_range_variance_30c, "21t": realized_range_variance_21t})[horizon]
                rvar = function(origin, pairs)
                record[f"rvar_{family}_fwd_{horizon}"] = rvar
                record[f"target_status_{family}_{horizon}"] = "COMPLETE" if rvar is not None else "MISSING_REQUIRED_SESSION"
                rvol = realized_volatility(rvar) if rvar is not None else None
                record[f"rvol_{family}_fwd_{horizon}"] = rvol
                record[f"vrp_x_{family}_{horizon}"] = vrp_x(original["ivar"], rvar) if rvar is not None else None
                record[f"volgap_{family}_{horizon}"] = volgap(original["ivol"], rvol) if rvar is not None else None
                if family == "cc":
                    record[f"hvar_cc_fwd_{horizon}"] = sum(v*v for _, v in pairs) if rvar is not None else None
        records.append(record)
    return daily, pd.DataFrame(records)


def audit_targets(spx: pd.DataFrame, panel: pd.DataFrame, daily: pd.DataFrame, targets: pd.DataFrame):
    """Independent numpy formulas and global-calendar membership for EVERY row."""
    if targets.origin.tolist() != panel.origin.tolist() or not daily.Date.equals(spx.Date):
        raise ValueError("Target/daily date preservation mismatch")
    if not daily[list(spx.columns)].equals(spx):
        raise ValueError("Canonical SPX source mutated")
    for col in panel.columns:
        if not targets[col].equals(panel[col]):
            raise ValueError("Predictor changed during outcome construction")
    dates = [as_date(d) for d in spx.Date]
    close = np.asarray(spx.Close, dtype=float)
    r = np.log(close[1:] / close[:-1])
    high, low, open_ = [np.asarray(spx[c], dtype=float) for c in ("High", "Low", "Open")]
    pk = np.log(high/low)**2 / (4*np.log(2))
    gk = np.maximum(0, .5*np.log(high/low)**2 - (2*np.log(2)-1)*np.log(close/open_)**2)
    expected_daily = {"cc": dict(zip(dates[1:], r*r)),
        "parkinson": dict(zip(dates, pk)), "gk": dict(zip(dates, gk))}
    if not math.isnan(float(daily.log_return.iloc[0])) or not np.allclose(daily.log_return.iloc[1:], r, rtol=1e-12, atol=1e-15):
        raise ValueError("Full-history return audit mismatch")
    for col, values in (("parkinson_daily", pk), ("gk_daily", gk)):
        if not np.allclose(daily[col], values, rtol=1e-12, atol=1e-15):
            raise ValueError("Daily range formula audit mismatch")
    counters = {f"{f}_{h}": {"complete": 0, "missing": 0} for f in FAMILIES for h in HORIZONS}
    max_error = 0.; counts30 = []
    for record in targets.to_dict("records"):
        origin = as_date(record["origin"]); assert_forecast_origin_allowed(origin)
        # Reconstruct from global XNYS sessions, rather than producer output dates.
        for horizon in HORIZONS:
            from vrp.calendar import exchange_sessions
            sessions = (exchange_sessions(origin + timedelta(days=1), origin + timedelta(days=30))
                if horizon == "30c" else exchange_sessions(origin + timedelta(days=1), origin + timedelta(days=90))[:21])
            if len(sessions) != record["target_session_count_" + horizon] or any(d <= origin for d in sessions):
                raise ValueError("Target calendar membership mismatch")
            expected_end = (origin + timedelta(days=30)).isoformat() if horizon == "30c" else sessions[-1].isoformat()
            if (record["target_first_session_"+horizon] != sessions[0].isoformat() or
                record["target_last_session_"+horizon] != sessions[-1].isoformat() or
                record["target_end_date_"+horizon] != expected_end):
                raise ValueError("Target endpoint mismatch")
            if horizon == "30c": counts30.append(len(sessions))
            factor = 365/30 if horizon == "30c" else 252/21
            for family in FAMILIES:
                mapping = expected_daily[family]; actual = record[f"rvar_{family}_fwd_{horizon}"]
                complete = all(d in mapping for d in sessions)
                counters[f"{family}_{horizon}"]["complete" if complete else "missing"] += 1
                expected_status = "COMPLETE" if complete else "MISSING_REQUIRED_SESSION"
                if record[f"target_status_{family}_{horizon}"] != expected_status:
                    raise ValueError("Target missingness status mismatch")
                if not complete:
                    for prefix in ("rvar", "rvol"):
                        if pd.notna(record[f"{prefix}_{family}_fwd_{horizon}"]):
                            raise ValueError("Incomplete target silently shortened")
                    for prefix in ("vrp_x", "volgap"):
                        if pd.notna(record[f"{prefix}_{family}_{horizon}"]):
                            raise ValueError("Incomplete target premium silently filled")
                    continue
                holding = float(np.sum([mapping[d] for d in sessions])); expected = factor * holding
                error = abs(actual-expected); max_error = max(max_error, error)
                if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-14):
                    raise ValueError("Independent target annualization/formula mismatch")
                for key, value in {f"rvol_{family}_fwd_{horizon}": math.sqrt(expected),
                    f"vrp_x_{family}_{horizon}": record["ivar"] - expected,
                    f"volgap_{family}_{horizon}": record["ivol"] - math.sqrt(expected)}.items():
                    if not math.isclose(record[key], value, rel_tol=1e-12, abs_tol=1e-14):
                        raise ValueError("Premium/volatility unit audit mismatch")
                if family == "cc" and not math.isclose(record[f"hvar_cc_fwd_{horizon}"], holding, rel_tol=1e-12, abs_tol=1e-14):
                    raise ValueError("Holding-period variance audit mismatch")
    return {"status": "PASSED_ALL_ORIGINS_ALL_SIX_TARGETS", "review_status": REVIEW,
        "target_version": TARGET_VERSION, "origin_count": len(targets), "spx_rows_preserved": len(spx),
        "return_count": len(dates)-1, "first_price_return": "UNAVAILABLE_NO_PREVIOUS_PRICE",
        "post_2025_support_rows": int((spx.Date > "2025-12-31").sum()),
        "counts": counters, "max_independent_rvar_absolute_error": max_error,
        "target_session_count_30c_range": [min(counts30), max(counts30)],
        "inference_executed": False, "forecast_ranking_executed": False,
        "checks": ["source preservation", "all SPX returns before VIX masking", "all expected XNYS sessions",
            "no same-origin return", "no 2026 origins", "six independent numpy formulas",
            "annualization and variance units", "premium sign and volatility square root",
            "exact endpoints", "explicit incomplete-target missingness", "unchanged predictors"]}


def describe_targets(targets: pd.DataFrame):
    columns = ["ivol", "ivar"] + [c for c in targets if c.startswith(("rvar_", "rvol_", "vrp_x_", "volgap_"))]
    subsets = {"full_sample": "1990-01-02", "oos_from_2007": "2007-01-01",
        "post_2003": "2004-01-01", "post_2014_10_06": "2014-10-06"}
    return {"review_status": REVIEW, "interpretation": "Descriptions only; no H1-H5 inference or economic mechanism claim",
        "subsets": {name: {c: summary_statistics(targets.loc[targets.origin >= lower, c].dropna().tolist())
            for c in columns} for name, lower in subsets.items()}}
