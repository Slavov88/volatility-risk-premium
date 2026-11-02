"""Cold-start corrected-calendar GARCH refits; never loads historical caches.
Usage: PYTHONPATH=CHECKOUT/src python fresh_refits.py CHECKOUT TARGETS DAILY OUT VARIANT
Writes resumable NEW run checkpoints. Inference delegated to fixed producer routine.
"""

import sys, json, hashlib, platform, time
from pathlib import Path
from datetime import date
from importlib.metadata import version
import numpy as np, pandas as pd

root, targets_path, daily_path, out, variant = sys.argv[1:]
root = Path(root)
out = Path(out)
out.mkdir(parents=True, exist_ok=True)
from vrp.recursive_garch import fit_origin, training_slice, VARIANTS, FIT_CONFIG
from vrp.asof_garch_calendar import forecast_schedule, POLICY
from vrp.empirical_calendar_repair import analysis, fixed_nonoverlap
from vrp.calendar import trailing_30c_sessions, trailing_exchange_sessions
from vrp.evaluation import naive_variance_30c, naive_variance_21t

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
targets = pd.read_csv(targets_path, float_precision="round_trip")
daily = pd.read_csv(daily_path, float_precision="round_trip")
sample = targets[targets.origin >= "2007-01-01"].copy()
ret = daily.dropna(subset=["log_return"])
days = [date.fromisoformat(d) for d in ret.Date]
values = ret.log_return.to_numpy()
dist, window = VARIANTS[variant]
config = {
    "run_kind": "FRESH_COLD_START_REFITS_NOT_HISTORICAL_CACHE_REPLAY",
    "policy": POLICY,
    "variant": variant,
    "fit": FIT_CONFIG,
    "inputs": {str(p): sha(p) for p in [targets_path, daily_path]},
    "software": {
        k: version(k) for k in ["numpy", "scipy", "pandas", "arch", "statsmodels"]
    },
    "python": platform.python_version(),
    "producer_source_sha256": {
        str(p): sha(root / p)
        for p in [
            "src/vrp/recursive_garch.py",
            "src/vrp/asof_garch_calendar.py",
            "src/vrp/quant_calendar.py",
        ]
    },
}
cp = out / (variant + ".jsonl")
records = []
if cp.exists():
    records = [json.loads(x) for x in cp.read_text().splitlines()]
configfile = out / (variant + "_configuration.json")
if configfile.exists():
    assert json.loads(configfile.read_text()) == config
else:
    configfile.write_text(json.dumps(config, indent=2) + "\n")
starttime = time.time()
with cp.open("a") as f:
    for i, origin in enumerate(sample.origin):
        if i < len(records):
            assert records[i]["origin"] == origin
            continue
        d = date.fromisoformat(origin)
        start, end, train = training_slice(days, values, d, window)
        s30, sessions = forecast_schedule(d)
        record = {
            "origin": origin,
            "training_start": days[start].isoformat(),
            "training_end": days[end - 1].isoformat(),
            "training_n": len(train),
            "training_sha256": hashlib.sha256(
                train.astype("<f8").tobytes()
            ).hexdigest(),
            "session_count_30c": len(s30),
            "forecast_sessions": [s.isoformat() for s in sessions],
            **fit_origin(train, dist, len(sessions)),
        }
        if record["status"] == "CONVERGED":
            v = record["daily_decimal_variances"]
            record["garch_30c"] = 365 / 30 * sum(v[: len(s30)])
            record["garch_21t"] = 12 * sum(v[:21])
        records.append(record)
        f.write(json.dumps(record, allow_nan=False) + "\n")
        f.flush()
        if (i + 1) % 100 == 0:
            print(
                variant, i + 1, "elapsed", round(time.time() - starttime, 1), flush=True
            )
returns = dict(zip(days, values))
analyses = []
for horizon in ["30c", "21t"]:
    naive = []
    for origin in sample.origin:
        d = date.fromisoformat(origin)
        sessions = (
            trailing_30c_sessions(d)
            if horizon == "30c"
            else trailing_exchange_sessions(d, 21)
        )
        fn = naive_variance_30c if horizon == "30c" else naive_variance_21t
        naive.append(fn(d, [(s, returns[s]) for s in sessions]))
    g = np.array(
        [
            r["garch_" + horizon] if r["status"] == "CONVERGED" else np.nan
            for r in records
        ]
    )
    naive = np.array(naive)
    for family in ["cc", "parkinson", "gk"]:
        y = sample["rvar_" + family + "_fwd_" + horizon].to_numpy()
        for period, lower in [("full", "2007-01-01"), ("post2014", "2014-10-06")]:
            idx = np.flatnonzero(
                (sample.origin.to_numpy() >= lower)
                & np.isfinite(g)
                & np.isfinite(y)
                & np.isfinite(naive)
                & np.isfinite(sample.ivar.to_numpy())
            )
            for mask in ["overlapping", "nonoverlap"]:
                sel = (
                    idx
                    if mask == "overlapping"
                    else idx[
                        fixed_nonoverlap(
                            sample.origin.iloc[idx].tolist(),
                            sample["target_end_date_" + horizon].iloc[idx].tolist(),
                        )
                    ]
                )
                result = analysis(
                    sample.origin.iloc[sel].tolist(),
                    y[sel],
                    {
                        "vix": sample.ivar.to_numpy()[sel],
                        "garch": g[sel],
                        "naive": naive[sel],
                    },
                    horizon,
                    mask == "nonoverlap",
                )
                analyses.append(
                    {
                        "variant": variant,
                        "horizon": horizon,
                        "family": family,
                        "period": period,
                        "mask": mask,
                        "fresh_refit": result,
                    }
                )
result = {
    "configuration": config,
    "completed": len(records),
    "failed": sum((r["status"] != "CONVERGED" for r in records)),
    "cache_reuse": 0,
    "own_new_checkpoint_resume_allowed": True,
    "analyses": analyses,
    "fits_sha256": sha(cp),
}
(out / (variant + "_results.json")).write_text(
    json.dumps(result, indent=2, allow_nan=False) + "\n"
)
print(variant, "DONE", len(records), result["failed"], flush=True)
