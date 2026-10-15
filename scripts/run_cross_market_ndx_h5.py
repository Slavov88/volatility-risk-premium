"""Run registered ex-post NBER regime analysis for Nasdaq-100/VXN H5."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from vrp.inference import nonoverlapping_origins_30c, overlap_l0
from vrp.provisional_analysis import checked_regression, persist
from vrp.regimes import label_nber_regimes, recession_months_from_chronology

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "outputs/cross_market/v1/ndx_vxn_targets.csv"
CHRONOLOGY = ROOT / "data/manifests/2026-10-13_nber_chronology.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    panel = pd.read_csv(PANEL, dtype={"origin": str})
    chronology_raw = CHRONOLOGY.read_bytes()
    chronology = json.loads(chronology_raw)
    months = chronology["monthly_flags"]
    recession = recession_months_from_chronology([r["date"] for r in months], [r["recession"] for r in months])
    labels = label_nber_regimes(panel.origin.tolist(), recession)
    panel["recession"] = [int(label == "recession") for _, label in labels]
    results = []
    for period, lower in (("maximum_available", panel.origin.min()), ("post_2014", "2014-10-06")):
        sub = panel.loc[panel.origin >= lower].copy()
        lag0 = overlap_l0(sub.origin.tolist())
        for lag in dict.fromkeys((lag0, 42, 63)):
            fit = checked_regression(sub.vrp_30c.to_numpy(), sub.recession.to_numpy(), lag, [[0, 1]], [0])
            fit.update({"period": period, "horizon": "30c", "lag": lag,
                        "regime_n": {"expansion": int((sub.recession == 0).sum()), "recession": int(sub.recession.sum())},
                        "regime_means": {name: float(sub.loc[sub.recession == flag, "vrp_30c"].mean())
                                         for name, flag in (("expansion", 0), ("recession", 1))}})
            results.append(fit)
        if period == "maximum_available":
            keep = {d.isoformat() for d in nonoverlapping_origins_30c(sub.origin.tolist())}
            n = sub.loc[sub.origin.isin(keep)]
            fit = checked_regression(n.vrp_30c.to_numpy(), n.recession.to_numpy(), 0, [[0, 1]], [0])
            fit.update({"period": period, "horizon": "30c_nonoverlap", "lag": 0, "n": len(n)})
            results.append(fit)
    cases = {}
    for year in (2008, 2020, 2022):
        x = panel.loc[panel.origin.str.startswith(str(year))]
        cases[str(year)] = {"n": len(x), "mean_vrp_30c": float(x.vrp_30c.mean()),
                            "median_vrp_30c": float(x.vrp_30c.median()),
                            "mean_implied_variance": float(x.ivar.mean()),
                            "mean_realized_variance": float(x.rvar_30c.mean())}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    out = {"status": "EXPLORATORY_EXTERNAL_REPLICATION — PROVISIONAL / PENDING INDEPENDENT REVIEW",
           "market": "NASDAQ-100 / Cboe VXN", "chronology_source_sha256": sha(chronology_raw),
           "target_panel_sha256": sha(PANEL.read_bytes()), "code_commit": commit,
           "specification": "VRP_30c = alpha + delta * ex-post NBER recession indicator + error; labels never enter forecasts",
           "regressions": results, "fixed_calendar_year_descriptions": cases}
    result_path = ROOT / "outputs/cross_market/v1/ndx_vxn_h5_v1.json"
    print(persist(result_path, out), flush=True)
    print(json.dumps({"regressions": [{"period": r["period"], "horizon": r["horizon"], "n": r["n"], "lag": r["lag"],
                                     "recession_coefficient": r["coefficients"][1], "ci95": r["ci95"][1],
                                     "p": r["p_values"][1]} for r in results], "cases": cases}, indent=2), flush=True)


if __name__ == "__main__":
    main()
