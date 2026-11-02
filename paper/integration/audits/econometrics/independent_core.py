"""Independent numpy Bartlett-HAC estimation from actual frozen targets.
Usage: python independent_core.py CHECKOUT TARGETS DAILY OUTPUT_JSON
No vrp econometrics routines are imported. Locked NBER dates are transcribed
from protocol/producer chronology; their original HTML bytes are not claimed recovered.
"""

import sys, json, hashlib, platform
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm, chi2

root, tp, dp, output = map(Path, sys.argv[1:])
a = pd.read_csv(tp, float_precision="round_trip")
daily = pd.read_csv(dp, float_precision="round_trip")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def ols(y, predictors, lag, restriction=None, null=None):
    y = np.asarray(y, float)
    x = np.asarray(predictors, float).reshape(len(y), -1)
    x = np.column_stack([np.ones(len(y)), x])
    n, k = x.shape
    b = np.linalg.lstsq(x, y, rcond=None)[0]
    u = y - x @ b
    s = x * u[:, None]
    meat = s.T @ s
    for j in range(1, lag + 1):
        c = s[j:].T @ s[:-j]
        meat += (1 - j / (lag + 1)) * (c + c.T)
    bread = np.linalg.inv(x.T @ x)
    cov = bread @ meat @ bread * n / (n - k)
    se = np.sqrt(np.diag(cov))
    z = b / se
    p = 2 * norm.sf(abs(z))
    r = {
        "n": n,
        "lag": lag,
        "coefficients": b.tolist(),
        "se": se.tolist(),
        "p_values": p.tolist(),
        "ci95": np.column_stack(
            [b - norm.ppf(0.975) * se, b + norm.ppf(0.975) * se]
        ).tolist(),
        "covariance": cov.tolist(),
    }
    if restriction is not None:
        R = np.asarray(restriction)
        diff = R @ b - np.asarray(null)
        w = float(diff @ np.linalg.solve(R @ cov @ R.T, diff))
        r["wald"] = {"statistic": w, "p_value": float(chi2.sf(w, len(diff)))}
    return r


# Reconstruct exact target sets using all preserved SPX dates, not VIX eligibility.
all_dates = pd.to_datetime(daily.Date).to_numpy()
origin = pd.to_datetime(a.origin).to_numpy()
sets = []
for d in origin:
    sets.append(
        set(
            np.flatnonzero((all_dates > d) & (all_dates <= d + np.timedelta64(30, "D")))
        )
    )
l0 = 0
for i, ss in enumerate(sets):
    for j in range(i + 1, min(i + 25, len(sets))):
        if ss & sets[j]:
            l0 = max(l0, j - i)
# Independently reconstruct all six target arrays from canonical raw OHLC CSV.
from math import log

c = daily.Close.to_numpy()
o = daily.Open.to_numpy()
h = daily.High.to_numpy()
l = daily.Low.to_numpy()
ret = np.r_[np.nan, np.diff(np.log(c))]
cc = ret**2
pa = np.log(h / l) ** 2 / (4 * np.log(2))
gk = 0.5 * np.log(h / l) ** 2 - (2 * np.log(2) - 1) * np.log(c / o) ** 2
errors = {}
for family, v in [("cc", cc), ("parkinson", pa), ("gk", gk)]:
    for horizon in ["30c", "21t"]:
        yy = []
        for i, d in enumerate(origin):
            idx = (
                sorted(sets[i])
                if horizon == "30c"
                else np.flatnonzero(all_dates > d)[:21]
            )
            yy.append(sum(v[idx]) * (365 / 30 if horizon == "30c" else 12))
        expected = a["rvar_" + family + "_fwd_" + horizon].to_numpy()
        err = float(np.max(abs(np.array(yy) - expected)))
        assert np.allclose(yy, expected, rtol=1e-10, atol=1e-13)
        errors[family + "_" + horizon] = err
assert np.allclose(a.ivar, (a.vix_close / 100) ** 2, rtol=0, atol=1e-16)
y = a.ivar.to_numpy() - a.rvar_cc_fwd_30c.to_numpy()
assert np.allclose(y, a.vrp_x_cc_30c, rtol=0, atol=1e-15)
recession = np.array(
    [
        any(
            p < d[:7] <= t
            for p, t in [
                ("1990-07", "1991-03"),
                ("2001-03", "2001-11"),
                ("2007-12", "2009-06"),
                ("2020-02", "2020-04"),
            ]
        )
        for d in a.origin
    ],
    int,
)
results = {}
for lag in [l0, 42, 63]:
    h1 = ols(y, np.empty((len(y), 0)), lag)
    h2 = ols(a.rvar_cc_fwd_30c, a.ivar, lag, np.eye(2), [0, 1])
    h5 = ols(y, recession, lag, [[0, 1]], [0])
    results[str(lag)] = {"h1": h1, "h2": h2, "h5": h5}
base = json.loads(
    (root / "data/manifests/2026-10-13_h1_h5_execution_v2.json").read_text()
)["primary_results"]
differences = {}
for name, r in results[str(l0)].items():
    old = base[name]
    key = "coefficients"
    oldcoef = old[key] if name != "h1" else [old["mean"]]
    oldse = old["se"] if name != "h1" else [old["standard_error"]]
    differences[name] = {
        "coefficient_max_abs_error": float(np.max(abs(np.array(r[key]) - oldcoef))),
        "se_max_abs_error": float(np.max(abs(np.array(r["se"]) - oldse))),
    }
    assert np.allclose(r[key], oldcoef, rtol=1e-9, atol=1e-12) and np.allclose(
        r["se"], oldse, rtol=1e-9, atol=1e-12
    )
robustness = []
for subset, lower in [
    ("full", "1990-01-02"),
    ("post2003", "2004-01-01"),
    ("post2014", "2014-10-06"),
]:
    idx = np.flatnonzero(a.origin.to_numpy() >= lower)
    for horizon in ["30c", "21t"]:
        for family in ["cc", "parkinson", "gk"]:
            for lag in [l0, 42, 63] if horizon == "30c" else [20, 10, 21, 42]:
                yy = a["rvar_" + family + "_fwd_" + horizon].to_numpy()[idx]
                iv = a.ivar.to_numpy()[idx]
                gap = iv - yy
                robustness.append(
                    {
                        "subset": subset,
                        "horizon": horizon,
                        "family": family,
                        "lag": lag,
                        "h1": ols(gap, np.empty((len(idx), 0)), lag),
                        "h2": ols(yy, iv, lag, np.eye(2), [0, 1]),
                        "h5": ols(gap, recession[idx], lag, [[0, 1]], [0]),
                    }
                )
    # Deterministic nonoverlap: next origin strictly after previous 30c end.
    chosen = []
    last = None
    for i in idx:
        if last is None or origin[i] > last:
            chosen.append(i)
            last = origin[i] + np.timedelta64(30, "D")
    ix = np.array(chosen)
    yy = a.rvar_cc_fwd_30c.to_numpy()[ix]
    iv = a.ivar.to_numpy()[ix]
    gap = iv - yy
    robustness.append(
        {
            "subset": subset,
            "horizon": "30c_nonoverlap",
            "family": "cc",
            "lag": 0,
            "h1": ols(gap, np.empty((len(ix), 0)), 0),
            "h2": ols(yy, iv, 0, np.eye(2), [0, 1]),
            "h5": ols(gap, recession[ix], 0, [[0, 1]], [0]),
        }
    )
receipt = {
    "run_kind": "INDEPENDENT_OBSERVATION_LEVEL_NUMPY_RECONSTRUCTION",
    "inputs": {str(tp): sha(tp), str(dp): sha(dp)},
    "python": platform.python_version(),
    "n": len(a),
    "l0_independent_target_set_intersection": l0,
    "recession_n": int(sum(recession)),
    "expansion_n": int(sum(1 - recession)),
    "target_max_abs_errors": errors,
    "results": results,
    "robustness_cells": robustness,
    "comparison_to_committed": differences,
    "nber_original_html_recovered": False,
    "nber_rule": "locked peak exclusive, trough inclusive monthly chronology; source retrieval not claimed",
    "status": "PROVISIONAL pending coauthor review",
}
output.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
