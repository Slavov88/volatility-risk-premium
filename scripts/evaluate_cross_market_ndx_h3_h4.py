"""Evaluate frozen Nasdaq-100/VXN recursive forecasts on common H3/H4 masks."""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from vrp.calendar import trailing_30c_sessions, trailing_exchange_sessions
from vrp.inference import holm_adjust_two, nonoverlapping_origins_30c, overlap_l0
from vrp.provisional_analysis import checked_mean, checked_regression, persist
from vrp.recursive_garch import VARIANTS
from vrp.targets import annualize_hvar_21t, annualize_hvar_30c

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/cross_market/v1/ndx_garch"
PANEL = ROOT / "outputs/cross_market/v1/ndx_vxn_targets.csv"
SOURCE = ROOT / "data/raw/cross_market_v1/2026-10-15T123148Z/nasdaq100_fred_distribution.csv"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def qlike(actual: np.ndarray, forecast: np.ndarray) -> np.ndarray:
    if not np.isfinite(actual).all() or not np.isfinite(forecast).all() or np.any(actual <= 0) or np.any(forecast <= 0):
        raise ValueError("QLIKE needs finite positive realized and forecast variances")
    ratio = actual / forecast
    return ratio - np.log(ratio) - 1


def load_forecasts() -> dict[str, dict]:
    found = {}
    for variant in VARIANTS:
        paths = list((OUT / variant).glob("*/forecasts.json"))
        if len(paths) != 1:
            raise ValueError(f"{variant}: expected one complete forecasts.json, got {len(paths)}")
        obj = json.loads(paths[0].read_bytes())
        if not obj.get("coverage_complete") or len(obj["records"]) != 4780:
            raise ValueError(f"{variant}: incomplete GARCH output")
        if obj["configuration"]["source_sha256"] != sha(SOURCE.read_bytes()) or obj["configuration"]["target_panel_sha256"] != sha(PANEL.read_bytes()):
            raise ValueError(f"{variant}: source identity mismatch")
        found[variant] = obj
    return found


def verify_record(record: dict, variant: str) -> None:
    if record["status"] != "CONVERGED" or record["training_end"] > record["origin"]:
        raise ValueError(f"{variant} unsafe/failed fit at {record['origin']}")
    p = record["parameters"]
    values = np.asarray(record["daily_decimal_variances"], dtype=float)
    if len(values) < max(21, record["session_count_30c"]) or not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError(f"{variant} invalid daily variance vector at {record['origin']}")
    omega = p["omega"] / 10000
    persistence = p["alpha[1]"] + p["beta[1]"]
    if not np.allclose(values[1:], omega + persistence * values[:-1], rtol=1e-9, atol=1e-13):
        raise ValueError(f"{variant} analytical recurrence mismatch at {record['origin']}")
    if record["garch_30c"] != 365/30 * sum(values[:record["session_count_30c"]]):
        raise ValueError(f"{variant} 30c annualization mismatch at {record['origin']}")
    if record["garch_21t"] != 252/21 * sum(values[:21]):
        raise ValueError(f"{variant} 21t annualization mismatch at {record['origin']}")
    if record["forecast_sessions"][0] <= record["origin"]:
        raise ValueError(f"{variant} non-forward forecast step at {record['origin']}")


def model_metrics(actual: np.ndarray, predictions: dict[str, np.ndarray]) -> dict:
    errors = {name: actual - forecast for name, forecast in predictions.items()}
    return {name: {"rmse": float(np.sqrt(np.mean(errors[name]**2))),
                  "mae": float(np.mean(np.abs(errors[name]))),
                  "qlike": float(np.mean(qlike(actual, predictions[name]))),
                  "mean_error": float(np.mean(errors[name]))} for name in predictions}


def evaluate_mask(origins: list[str], horizon: str, field: str,
                  targets: dict, ivar: dict, naive: dict,
                  records: dict[str, dict], *, nonoverlap: bool = False) -> dict:
    candidates = [d for d in origins if targets.get(d) is not None and naive.get(d) is not None
                  and all(records[v][d]["status"] == "CONVERGED" for v in VARIANTS)]
    if nonoverlap:
        chosen = {d.isoformat() for d in nonoverlapping_origins_30c(candidates)}
        candidates = [d for d in candidates if d in chosen]
    if not candidates:
        raise ValueError(f"No common origins for {horizon}")
    lag0 = overlap_l0(candidates) if horizon == "30c" and not nonoverlap else 20 if horizon == "21t" else 0
    lags = [lag0] if nonoverlap else list(dict.fromkeys([lag0, 42, 63] if horizon == "30c" else [20, 10, 21, 42]))
    actual = np.asarray([targets[d] for d in candidates], float)
    result = {"horizon": horizon, "nonoverlap": nonoverlap, "n": len(candidates),
              "origins_sha256": sha(("\n".join(candidates)+"\n").encode()), "origins": candidates,
              "lags": lags, "variants": {}}
    for variant in VARIANTS:
        pred = {"implied": np.asarray([ivar[d] for d in candidates], float),
                "garch": np.asarray([records[variant][d][field] for d in candidates], float),
                "trailing": np.asarray([naive[d] for d in candidates], float)}
        errors = {n: actual-v for n, v in pred.items()}
        sq = {n: e**2 for n, e in errors.items()}
        tests, h4 = [], []
        for lag in lags:
            primary = checked_mean(sq["implied"]-sq["garch"], lag)
            p1 = checked_mean(sq["implied"]-sq["trailing"], lag)
            p2 = checked_mean(sq["garch"]-sq["trailing"], lag)
            holm = holm_adjust_two([p1["p_value"], p2["p_value"]])
            tests.append({"lag": lag, "implied_minus_garch_squared_loss": primary,
                "implied_minus_trailing_squared_loss": {**p1, "holm_p_value": holm[0]},
                "garch_minus_trailing_squared_loss": {**p2, "holm_p_value": holm[1]},
                "implied_minus_garch_qlike": checked_mean(qlike(actual,pred["implied"])-qlike(actual,pred["garch"]),lag)})
            if not nonoverlap:
                h4.append({"lag": lag, **checked_regression(actual,np.column_stack([pred["implied"],pred["garch"]]),lag)})
        result["variants"][variant] = {"metrics": model_metrics(actual,pred), "h3_tests": tests,
            "h4": h4, "h4_coefficient_order": ["alpha", "beta_implied", "gamma_garch"]}
    return result


def run() -> dict:
    forecasts = load_forecasts()
    targets_frame = pd.read_csv(PANEL, dtype={"origin": str})
    targets_frame = targets_frame.loc[(targets_frame.origin >= "2007-01-01") & (targets_frame.origin <= "2025-12-31")].copy()
    dates = targets_frame.origin.tolist()
    if len(dates) != 4780:
        raise ValueError(f"OOS panel expected 4780 dates; got {len(dates)}")
    for obj in forecasts.values():
        if [r["origin"] for r in obj["records"]] != dates:
            raise ValueError("GARCH origin dates differ from target panel")
    records = {name: {r["origin"]: r for r in obj["records"]} for name, obj in forecasts.items()}
    for name, rows in records.items():
        for row in rows.values():
            verify_record(row, name)

    src = pd.read_csv(SOURCE)
    src["Date"] = pd.to_datetime(src.observation_date, errors="raise").dt.date
    src["Close"] = pd.to_numeric(src.NASDAQ100, errors="coerce")
    src = src.dropna(subset=["Close"])
    import exchange_calendars as xc
    cal = xc.get_calendar("XNYS", start=src.Date.min().isoformat(), end=src.Date.max().isoformat())
    sessions = [x.date() for x in cal.sessions_in_range(src.Date.min(), src.Date.max())]
    src = src.loc[src.Date.isin(sessions)].set_index("Date").sort_index()
    close = src.Close.to_dict()
    returns = {}
    for prev, curr in zip(sessions[:-1], sessions[1:]):
        if prev in close and curr in close:
            returns[curr] = float(np.log(close[curr]/close[prev]))
    return_pairs = sorted(returns.items())
    return_map = dict(return_pairs)
    # Validate the realized return series once. The generic public naive
    # benchmark helpers revalidate all dated values on every call, which is
    # needlessly quadratic for this 4,780-origin cross-market panel.
    if len(return_map) != len(return_pairs) or any(not np.isfinite(v) for v in return_map.values()):
        raise ValueError("Naive benchmark return history is duplicated or non-finite")
    naive = {"30c": {}, "21t": {}}
    actual = {"30c": dict(zip(dates,targets_frame.rvar_30c)), "21t": dict(zip(dates,targets_frame.rvar_21t))}
    ivar = dict(zip(dates,targets_frame.ivar))
    for d in dates:
        day = date.fromisoformat(d)
        horizon30 = trailing_30c_sessions(day)
        horizon21 = trailing_exchange_sessions(day,21)
        naive["30c"][d] = (annualize_hvar_30c(sum(return_map[s]**2 for s in horizon30))
                             if all(s in return_map for s in horizon30) else None)
        naive["21t"][d] = (annualize_hvar_21t(sum(return_map[s]**2 for s in horizon21))
                             if all(s in return_map for s in horizon21) else None)

    results = []
    for horizon, field in (("30c","garch_30c"),("21t","garch_21t")):
        tgt = actual[horizon]
        trail = naive[horizon]
        results.append({"period":"full","horizon":horizon,
                        **evaluate_mask(dates,horizon,field,tgt,ivar,trail,records)})
        if horizon == "30c":
            post = [d for d in dates if d >= "2014-10-06"]
            results.append({"period":"post_2014-10-06","horizon":horizon,
                            **evaluate_mask(post,horizon,field,tgt,ivar,trail,records)})
            results.append({"period":"full","horizon":horizon,
                            **evaluate_mask(dates,horizon,field,tgt,ivar,trail,records,nonoverlap=True)})
    commit = subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    return {"status":"EXPLORATORY_EXTERNAL_REPLICATION — PROVISIONAL / PENDING INDEPENDENT REVIEW",
        "market":"NASDAQ-100 / Cboe VXN","code_commit":commit,
        "source_sha256":sha(SOURCE.read_bytes()),"target_panel_sha256":sha(PANEL.read_bytes()),
        "forecast_configurations":{k:v["configuration_sha256"] for k,v in forecasts.items()},
        "expected_oos_origins":4780,"h3_h4_same_mask_across_variants":True,
        "forecast_validation":{k:{"records":len(v),"failures":sum(x["status"]!="CONVERGED" for x in v.values()),
             "max_recurrence_error":max(x.get("recurrence_max_abs_error_decimal_variance",0.0) for x in v.values())} for k,v in records.items()},
        "evaluations":results}


def main() -> None:
    result=run()
    out=ROOT/"outputs/cross_market/v1/ndx_vxn_h3_h4_v2.json"
    print(persist(out,result),flush=True)
    print(json.dumps({"metrics":[{"period":x["period"],"horizon":x["horizon"],"variants":{v:x["variants"][v]["metrics"] for v in VARIANTS}} for x in result["evaluations"]]},indent=2),flush=True)


if __name__=="__main__":
    main()
