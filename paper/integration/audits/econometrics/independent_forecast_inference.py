"""Independent NumPy primary H3/H4 from NEW per-origin fitted records.
Usage: python independent_forecast_inference.py TARGETS FRESH_DIR OUTPUT
"""

import sys, json, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm

p, folder, out = map(Path, sys.argv[1:])
a = pd.read_csv(p, float_precision="round_trip")
a = a[a.origin >= "2007-01-01"]
y = a.rvar_cc_fwd_30c.to_numpy()
v = a.ivar.to_numpy()


def fit(y, x, lag=21):
    x = np.column_stack([np.ones(len(y)), np.asarray(x).reshape(len(y), -1)])
    b = np.linalg.lstsq(x, y, rcond=None)[0]
    s = x * (y - x @ b)[:, None]
    m = s.T @ s
    for j in range(1, lag + 1):
        c = s[j:].T @ s[:-j]
        m += (1 - j / (lag + 1)) * (c + c.T)
    z = np.linalg.inv(x.T @ x)
    cov = z @ m @ z * len(y) / (len(y) - x.shape[1])
    se = np.sqrt(np.diag(cov))
    return {
        "coefficients": b.tolist(),
        "se": se.tolist(),
        "p_values": (2 * norm.sf(abs(b / se))).tolist(),
    }


results = {}
for f in sorted(folder.glob("*_results.json")):
    r = json.loads(f.read_text())
    variant = r["configuration"]["variant"]
    source = folder / (variant + ".jsonl")
    records = [json.loads(l) for l in source.read_text().splitlines()]
    assert [x["origin"] for x in records] == a.origin.tolist()
    g = np.array([x["garch_30c"] for x in records])
    assert np.isfinite(g).all()
    h3 = fit((y - v) ** 2 - (y - g) ** 2, np.empty((len(y), 0)))
    h4 = fit(y, np.column_stack([v, g]))
    ref = r["analyses"][0]["fresh_refit"]["tests"][0]
    diff = {}
    for key, ours, expected in [
        ("h3_coef", h3["coefficients"], [ref["squared_error"]["vix_vs_garch"]["mean"]]),
        ("h3_se", h3["se"], [ref["squared_error"]["vix_vs_garch"]["standard_error"]]),
        ("h3_p", h3["p_values"], [ref["squared_error"]["vix_vs_garch"]["p_value"]]),
        ("h4_coef", h4["coefficients"], ref["h4"]["coefficients"]),
        ("h4_se", h4["se"], ref["h4"]["se"]),
        ("h4_p", h4["p_values"], ref["h4"]["p_values"]),
    ]:
        diff[key] = float(np.max(abs(np.array(ours) - expected)))
    results[variant] = {
        "h3": h3,
        "h4": h4,
        "n": len(y),
        "lag": 21,
        "max_abs_error_vs_new_producer": diff,
        "fresh_record_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
assert len(results) == 3
out.write_text(
    json.dumps(
        {
            "run_kind": "INDEPENDENT_NUMPY_FORECAST_INFERENCE_FROM_NEW_FITS",
            "results": results,
        },
        indent=2,
    )
    + "\n"
)
