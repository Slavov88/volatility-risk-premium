"""Predefined alternate-close scenarios, isolated from the canonical series."""
from __future__ import annotations

import math
import numpy as np

from vrp.calendar import forward_30c_sessions, next_exchange_sessions
from vrp.dates import as_date
from vrp.interim_panel import REVIEW
from vrp.returns import log_returns
from vrp.spx_discrepancy_impact import correction_footprint
from vrp.targets import realized_variance_30c, realized_variance_21t

DISCREPANCY_DATES = ("2018-11-29", "2019-08-12", "2020-05-11", "2020-10-02",
    "2020-10-05", "2020-10-06", "2021-08-11")


def evaluate_alternate_closes(spx, targets, replacements):
    """Individual and joint CC target changes; do not mutate canonical OHLC."""
    if set(replacements) != set(DISCREPANCY_DATES):
        raise ValueError("Sensitivity requires all seven pre-registered dates")
    if any(not math.isfinite(float(v)) or v <= 0 for v in replacements.values()):
        raise ValueError("Alternate closes must be finite and positive")
    footprints = correction_footprint(spx.Date.tolist(), spx.Close.tolist(), replacements, targets.origin.tolist())
    indexed = targets.set_index("origin")
    scenarios = []
    for chosen in [{d: replacements[d]} for d in DISCREPANCY_DATES] + [replacements]:
        alternate = spx.copy(deep=True)
        for day, value in chosen.items():
            if (alternate.Date == day).sum() != 1:
                raise ValueError("Alternate close date missing/ambiguous")
            alternate.loc[alternate.Date == day, "Close"] = value
        # Combine adjacent price replacements BEFORE calculating log returns.
        pairs = dict(log_returns([as_date(d) for d in alternate.Date], alternate.Close.tolist()))
        result = {"scenario": "all_seven_joint" if len(chosen) > 1 else next(iter(chosen)),
            "replacement_dates": sorted(chosen), "canonical_source_modified": False, "horizons": {}}
        for horizon in ("30c", "21t"):
            affected = sorted({d for f in footprints if f["correction_date"] in chosen
                for d in f["affected_origins"][horizon]})
            deltas = []
            for origin_text in affected:
                origin = as_date(origin_text)
                sessions = forward_30c_sessions(origin) if horizon == "30c" else next_exchange_sessions(origin,21)
                fn = realized_variance_30c if horizon == "30c" else realized_variance_21t
                value = fn(origin, [(d,pairs[d]) for d in sessions])
                # Separate vector oracle for combined target changes.
                oracle = (365/30 if horizon == "30c" else 252/21)*float(np.sum([pairs[d]**2 for d in sessions]))
                if not math.isclose(value, oracle, rel_tol=1e-12, abs_tol=1e-14):
                    raise ValueError("Alternate target oracle mismatch")
                deltas.append(value-float(indexed.loc[origin_text,f"rvar_cc_fwd_{horizon}"]))
            baseline = targets[f"vrp_x_cc_{horizon}"]
            result["horizons"][horizon] = {"affected_origins": affected, "affected_count": len(affected),
                "max_abs_rvar_change": max(map(abs,deltas), default=0.),
                "mean_vrp_change_full_sample": -sum(deltas)/len(targets),
                "alternate_mean_vrp_full_sample": float(baseline.mean())-sum(deltas)/len(targets)}
        incompatible = alternate.loc[alternate.Date.isin(chosen) &
            ((alternate.Close > alternate.High) | (alternate.Close < alternate.Low)), "Date"].tolist()
        result["gk_ohlc_incompatible_dates"] = incompatible
        result["range_sensitivity_status"] = "NOT_EXECUTED; CC sensitivity only; Parkinson bounds unchanged"
        scenarios.append(result)
    return {"review_status": REVIEW, "role": "PREDEFINED_ALTERNATE_SOURCE_SENSITIVITY",
        "canonical_source_modified": False, "inferential_selection": False,
        "scope": "All seven individual cases and their joint CC scenario; no primary source promotion",
        "scenarios": scenarios}
