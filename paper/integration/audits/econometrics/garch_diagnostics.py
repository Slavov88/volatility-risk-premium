"""Summarize fresh recursive fits and refit fixed annual residual-diagnostic anchors.

Usage: PYTHONPATH=CHECKOUT/src python garch_diagnostics.py DAILY_CSV FRESH_DIR OUTPUT_JSON
Reads private per-origin checkpoints but writes only aggregate and diagnostic statistics.
"""

import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from vrp.recursive_garch import VARIANTS, fit_origin, training_slice
from vrp.asof_garch_calendar import forecast_schedule


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values):
    values = np.asarray(values, dtype=float)
    return {
        "n": len(values),
        "min": float(values.min()),
        "median": float(np.median(values)),
        "max": float(values.max()),
        "mean": float(values.mean()),
    }


def main():
    daily_path, folder, output = map(Path, sys.argv[1:])
    daily = pd.read_csv(daily_path, float_precision="round_trip").dropna(
        subset=["log_return"]
    )
    days = [date.fromisoformat(d) for d in daily.Date]
    returns = daily.log_return.to_numpy()
    variants = {}
    for variant, (dist, window) in VARIANTS.items():
        path = folder / f"{variant}.jsonl"
        records = [json.loads(line) for line in path.read_text().splitlines()]
        assert len(records) == 4780 and len({r["origin"] for r in records}) == 4780
        assert all(r["status"] == "CONVERGED" for r in records)
        origins = [r["origin"] for r in records]
        anchors = []
        for year in range(2007, 2026):
            annual = [d for d in origins if d.startswith(str(year))]
            assert len(annual) > 1
            anchors.extend([annual[0], annual[-1]])
        by_origin = {r["origin"]: r for r in records}
        diagnostics = []
        for origin in anchors:
            prior = by_origin[origin]
            day = date.fromisoformat(origin)
            start, end, train = training_slice(days, returns, day, window)
            train_hash = hashlib.sha256(train.astype("<f8").tobytes()).hexdigest()
            if train_hash != prior["training_sha256"]:
                raise ValueError(f"Training mismatch at {variant} {origin}")
            _, sessions = forecast_schedule(day)
            fit = fit_origin(train, dist, len(sessions), residual_diagnostics=True)
            row = {
                "origin": origin,
                "training_n": len(train),
                "training_sha256_match": True,
                "status": fit["status"],
                "convergence_flag": fit.get("convergence_flag"),
                "parameter_abs_differences_vs_fresh_checkpoint": {
                    k: abs(v - prior["parameters"][k])
                    for k, v in fit.get("parameters", {}).items()
                },
                "log_likelihood_abs_difference_vs_fresh_checkpoint": (
                    abs(fit["log_likelihood"] - prior["log_likelihood"])
                    if "log_likelihood" in fit
                    else None
                ),
                "diagnostics": fit.get("standardized_residual_diagnostics"),
                "warnings": fit["warnings"],
            }
            diagnostics.append(row)
            print(variant, origin, fit["status"], flush=True)
        parameters = records[0]["parameters"].keys()
        variants[variant] = {
            "checkpoint_sha256": digest(path),
            "n": len(records),
            "status_counts": dict(Counter(r["status"] for r in records)),
            "convergence_flags": dict(
                Counter(str(r["convergence_flag"]) for r in records)
            ),
            "parameters": {
                key: summary([r["parameters"][key] for r in records])
                for key in parameters
            },
            "persistence": summary([r["persistence"] for r in records]),
            "persistence_at_least_one": sum(r["persistence"] >= 1 for r in records),
            "log_likelihood": summary([r["log_likelihood"] for r in records]),
            "anchor_diagnostics": diagnostics,
        }
    output.write_text(
        json.dumps(
            {
                "kind": "FRESH_REFIT_SUMMARY_AND_NEW_ANCHOR_DIAGNOSTICS",
                "daily_input_sha256": digest(daily_path),
                "anchor_rule": "first and final eligible origin of each year 2007–2025",
                "units": "mu is percent return; omega is percent-squared; alpha, beta, nu and persistence are dimensionless",
                "variants": variants,
            },
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
