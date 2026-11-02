"""Fresh exact anchor refit replay and after-origin perturbation test.
Usage: PYTHONPATH=CHECKOUT/src python check_leakage.py DAILY OUT
No historical cache is read. Tests producer training slicing/forecast calendar.
"""

import sys, json, hashlib
from pathlib import Path
from datetime import date
import pandas as pd, numpy as np
from vrp.recursive_garch import training_slice, fit_origin, VARIANTS
from vrp.asof_garch_calendar import forecast_schedule

p, out = map(Path, sys.argv[1:])
d = pd.read_csv(p, float_precision="round_trip").dropna(subset=["log_return"])
days = [date.fromisoformat(v) for v in d.Date]
v = d.log_return.to_numpy()
rows = []
for origin in [
    "2007-01-03",
    "2012-10-26",
    "2012-10-29",
    "2018-12-03",
    "2022-05-20",
    "2025-12-31",
]:
    day = date.fromisoformat(origin)
    if day not in days:
        continue
    for variant, (dist, window) in VARIANTS.items():
        start, end, train = training_slice(days, v, day, window)
        perturbed = v.copy()
        perturbed[end:] = np.linspace(-0.5, 0.5, len(v) - end)
        _, _, other = training_slice(days, perturbed, day, window)
        assert np.array_equal(train, other)
        ss, s = forecast_schedule(day)
        first = fit_origin(train, dist, len(s))
        second = fit_origin(other, dist, len(s))
        assert first == second
        rows.append(
            {
                "origin": origin,
                "variant": variant,
                "training_rows": len(train),
                "training_end": days[end - 1].isoformat(),
                "exact_new_refit_repeat": True,
                "after_origin_perturbation_changes_prediction": False,
                "fit_status": first["status"],
                "forecast_steps30c": len(ss),
            }
        )
r = {
    "run_kind": "SAME_RUNTIME_NEW_ANCHOR_FIT_REPEAT_NOT_HISTORICAL_REPLAY",
    "anchors": rows,
    "all_exact": True,
    "input_daily_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
}
out.write_text(json.dumps(r, indent=2) + "\n")
print(len(rows), "anchor fits repeated exactly; future perturbations excluded")
