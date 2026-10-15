"""Run fixed exploratory H6/H7 procedures on Nasdaq-100/VXN forecasts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import exchange_calendars as xc

from vrp.provisional_analysis import persist
from vrp.quant_extension import (H6_FEATURES, H7_FEATURES, HAR_FEATURES, PERIODS,
    alert_metrics, block_indices, bootstrap_pair, build_features, budget_alerts,
    evaluation_panel, fit_h6, holm, matured_training, paired, predict_h6, probability_metrics)
from vrp.quant_variance import fit_h7, predict_h7, qlike, variance_metrics
from vrp.recursive_garch import VARIANTS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/cross_market_v1/2026-10-15T123148Z/nasdaq100_fred_distribution.csv"
TARGETS = ROOT / "outputs/cross_market/v1/ndx_vxn_targets.csv"
GARCH_ROOT = ROOT / "outputs/cross_market/v1/ndx_garch"
OUT = ROOT / "outputs/cross_market/v1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def csv_immutable(path: Path, frame: pd.DataFrame) -> str:
    data = frame.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode()
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"Immutable output differs: {path}")
    if not path.exists():
        path.write_bytes(data)
    return sha(data)


def input_panel() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(SOURCE)
    raw["Date"] = pd.to_datetime(raw.observation_date, errors="raise").dt.date
    raw["Close"] = pd.to_numeric(raw.NASDAQ100, errors="coerce")
    raw = raw.dropna(subset=["Close"])
    cal = xc.get_calendar("XNYS", start=raw.Date.min().isoformat(), end=raw.Date.max().isoformat())
    sessions = [x.date() for x in cal.sessions_in_range(raw.Date.min(), raw.Date.max())]
    raw = raw.loc[raw.Date.isin(sessions)].set_index("Date").sort_index()
    closes = raw.Close.to_dict()
    returns = {curr: float(np.log(closes[curr] / closes[prev])) for prev, curr in zip(sessions[:-1], sessions[1:])
               if prev in closes and curr in closes}
    daily = pd.DataFrame({"Date": [d.isoformat() for d in sessions],
                          "log_return": [returns.get(d, np.nan) for d in sessions]})
    targets = pd.read_csv(TARGETS, dtype={"origin": str})
    targets = targets.rename(columns={"rvar_30c": "rvar_cc_fwd_30c"})
    targets["target_status_cc_30c"] = "COMPLETE"
    garch_paths = list((GARCH_ROOT / "normal_expanding").glob("*/forecasts.json"))
    if len(garch_paths) != 1:
        raise ValueError("Expected exactly one complete normal-expanding forecast run")
    gobj = json.loads(garch_paths[0].read_bytes())
    if not gobj.get("coverage_complete") or len(gobj["records"]) != 4780:
        raise ValueError("Incomplete normal-expanding GARCH forecast set")
    garch = pd.DataFrame({"origin": [r["origin"] for r in gobj["records"]],
                          "garch": [r["garch_30c"] for r in gobj["records"]]})
    panel = build_features(targets, daily, garch)
    if len(evaluation_panel(panel)) != 3520:
        raise ValueError("H6/H7 common evaluation panel differs from 2012-2025 date support")
    return panel, {"source_sha256": sha(SOURCE.read_bytes()), "target_sha256": sha(TARGETS.read_bytes()),
                   "normal_expanding_forecasts_sha256": sha(garch_paths[0].read_bytes()),
                   "evaluation_origins": len(evaluation_panel(panel))}


def run_h6_local(panel: pd.DataFrame) -> dict:
    sample = evaluation_panel(panel)
    rows, fits, previous = [], [], None
    for _, row in sample.iterrows():
        month = row.origin[:7]
        if month != previous:
            models, audit = fit_h6(matured_training(panel, row.origin, H6_FEATURES))
            audit["as_of"] = row.origin
            fits.append(audit)
            previous = month
        prediction = predict_h6(models, row)
        rows.append({"origin": row.origin, "y": int(row.event), "as_of_fit": audit["as_of"], **prediction,
                     **{f"{n}_alert_threshold": audit[n]["threshold90"] for n in prediction}})
    forecasts = pd.DataFrame(rows)
    y = forecasts.y.to_numpy()
    metrics = {n: probability_metrics(y, forecasts[n].to_numpy(), forecasts[f"{n}_alert_threshold"].to_numpy())
               for n in ("A", "B", "C", "D")}
    tests = []
    for candidate in ("C", "D"):
        for baseline in ("A", "B"):
            a = (y-forecasts[candidate].to_numpy())**2
            b = (y-forecasts[baseline].to_numpy())**2
            tests.append({"candidate": candidate, "baseline": baseline, **paired(a-b),
                          "relative_brier_reduction": bootstrap_pair(a,b,lambda u,v:float(1-u.mean()/v.mean()))})
            pa, pb = forecasts[candidate].to_numpy(), forecasts[baseline].to_numpy()
            rng = np.random.default_rng(1729); gains = []
            for _ in range(1000):
                idx = block_indices(len(y),rng)
                if y[idx].sum():
                    gains.append(alert_metrics(y[idx],budget_alerts(pa[idx]))["recall"]-
                                 alert_metrics(y[idx],budget_alerts(pb[idx]))["recall"])
            tests[-1]["budget_recall_gain"] = {"estimate": metrics[candidate]["budget10_retrospective"]["recall"]-
                metrics[baseline]["budget10_retrospective"]["recall"],"ci95":np.quantile(gains,[.025,.975]).tolist()}
    holm(tests)
    periods = {}
    for name,(lo,hi) in PERIODS.items():
        sub=forecasts.loc[forecasts.origin.between(lo,hi)]; yy=sub.y.to_numpy()
        periods[name]={"n":len(sub),"events":int(yy.sum()),"models":{m:{"brier":float(np.mean((yy-sub[m])**2)),
            "budget":alert_metrics(yy,budget_alerts(sub[m]))} for m in metrics}}
    digest=csv_immutable(OUT/"ndx_vxn_h6_forecasts.csv",forecasts)
    return {"status":"EXPLORATORY — POST H1-H5 — PENDING INDEPENDENT REVIEW","n":len(forecasts),"events":int(y.sum()),
        "prevalence":float(y.mean()),"models":metrics,"comparisons":tests,"periods":periods,"fits":fits,
        "failed_fits":0,"forecasts_sha256":digest,"common_origin_sha256":sha(("\n".join(forecasts.origin)+"\n").encode())}


def run_h7_local(panel: pd.DataFrame) -> dict:
    sample=evaluation_panel(panel); fits=[]; rows=[]; previous=None
    clipping={n:0 for n in ("vix","garch","trailing","ewma","har","combined")}
    for _,row in sample.iterrows():
        if row.origin[:7]!=previous:
            models,audit=fit_h7(matured_training(panel,row.origin,H7_FEATURES+HAR_FEATURES))
            audit["as_of"]=row.origin;fits.append(audit);previous=row.origin[:7]
        prediction,clips=predict_h7(models,row)
        for name,count in clips.items():clipping[name]+=count
        rows.append({"origin":row.origin,"y":float(row.y),"as_of_fit":audit["as_of"],**prediction})
    forecasts=pd.DataFrame(rows);y=forecasts.y.to_numpy()
    metrics={name:variance_metrics(y,forecasts[name].to_numpy()) for name in clipping}
    tests=[];candidate_qlike=qlike(y,forecasts.combined.to_numpy())
    for baseline in ("vix","garch","trailing"):
        baseline_qlike=qlike(y,forecasts[baseline].to_numpy())
        tests.append({"candidate":"combined","baseline":baseline,**paired(candidate_qlike-baseline_qlike),
            "relative_qlike_reduction":bootstrap_pair(candidate_qlike,baseline_qlike,lambda u,v:float(1-u.mean()/v.mean())),
            "mse_difference":paired((y-forecasts.combined)**2-(y-forecasts[baseline])**2),
            "mae_difference":paired(np.abs(y-forecasts.combined)-np.abs(y-forecasts[baseline]))})
    holm(tests);periods={}
    for name,(lo,hi) in PERIODS.items():
        sub=forecasts.loc[forecasts.origin.between(lo,hi)]
        periods[name]={"n":len(sub),"models":{m:variance_metrics(sub.y.to_numpy(),sub[m].to_numpy()) for m in metrics}}
    digest=csv_immutable(OUT/"ndx_vxn_h7_forecasts.csv",forecasts)
    return {"status":"EXPLORATORY — POST H1-H5 — PENDING INDEPENDENT REVIEW","n":len(forecasts),
        "models":metrics,"comparisons":tests,"periods":periods,"fits":fits,"failed_fits":0,"floor_counts":clipping,
        "forecasts_sha256":digest,"common_origin_sha256":sha(("\n".join(forecasts.origin)+"\n").encode())}


def main() -> None:
    panel, provenance=input_panel()
    commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    code_files=["src/vrp/quant_extension.py","src/vrp/quant_variance.py","scripts/run_cross_market_ndx_h6_h7.py"]
    code={p:sha((ROOT/p).read_bytes()) for p in code_files}
    for name,runner in (("h6",run_h6_local),("h7",run_h7_local)):
        result=runner(panel)
        result.update({"market":"NASDAQ-100 / Cboe VXN","code_commit":commit,"code_sha256":code,"inputs":provenance})
        path=OUT/f"ndx_vxn_{name}_v1.json"
        print(name,persist(path,result),"n",result["n"],flush=True)
        print(json.dumps({"name":name,"n":result["n"],"events":result.get("events"),"metrics":result["models"]},indent=2),flush=True)


if __name__=="__main__":
    main()
