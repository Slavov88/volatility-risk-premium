"""Fixed QQQ volatility-targeting replay using Nasdaq/VXN H7 signals."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from vrp.cash_yield import (COSTS, MODELS, SCENARIOS, attribution, bootstrap,
    cash_replay, exact_reference_values, independently_audit, rate_schedule, summarize)
from vrp.provisional_analysis import persist
from vrp.quant_extension import PERIODS, checked_hash
from vrp.quant_portfolio import portfolio_metrics, simulate_spy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/cross_market/v1"
H8_OUT = OUT / "h8_cash_yield_v1"
QQQ_MANIFEST = ROOT / "data/manifests/cross_market_sources_v1.json"
RATE_MANIFEST = ROOT / "data/manifests/h8_cash_rate_source_v1.json"
H7_JSON = OUT / "ndx_vxn_h7_v1.json"
H7_CSV = OUT / "ndx_vxn_h7_forecasts.csv"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def audit_qqq(frame: pd.DataFrame) -> dict:
    required = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Dividends", "Stock Splits"]
    if frame["Date"].duplicated().any() or not frame.Date.is_monotonic_increasing:
        raise ValueError("QQQ dates duplicate or unordered")
    if frame[required[1:]].isna().any().any() or not np.isfinite(frame[required[1:]].to_numpy(float)).all():
        raise ValueError("QQQ price/action data contain nonfinite values")
    if (frame[["Open", "High", "Low", "Close", "Adj Close"]].to_numpy(float) <= 0).any() or (frame[["Dividends", "Stock Splits"]].to_numpy(float) < 0).any():
        raise ValueError("QQQ price/action values out of bounds")
    if not ((frame.High >= frame[["Open", "Close", "Low"]].max(axis=1)) &
            (frame.Low <= frame[["Open", "Close", "High"]].min(axis=1))).all():
        raise ValueError("QQQ OHLC inequalities failed")
    study = frame.loc[frame.Date.between("2012-01-01", "2026-01-02")].copy()
    if study.empty or study["Stock Splits"].ne(0).any():
        raise ValueError("QQQ split inside the strategy sample requires a separate share-unit bridge")
    share_return = ((study.Close + study.Dividends) / study.Close.shift(1) - 1).iloc[1:].to_numpy()
    vendor_return = study["Adj Close"].pct_change(fill_method=None).iloc[1:].to_numpy()
    diff = share_return-vendor_return
    if np.max(np.abs(diff)) > .002:
        raise ValueError("QQQ dividend/adjusted-close reconciliation failed")
    return {"rows": len(frame), "study_rows": len(study), "first": frame.Date.iloc[0], "last": frame.Date.iloc[-1],
        "split_events_full_history": int(frame["Stock Splits"].ne(0).sum()), "split_events_in_study": 0,
        "dividend_events_in_study": int(study.Dividends.gt(0).sum()),
        "max_abs_total_return_vs_adj_close_difference": float(np.max(np.abs(diff))),
        "sample_continuity": "no share-unit discontinuity inside 2012-2026 strategy interval; pre-sample 2000 split vendor-normalized"}


def audit_ledger(log: pd.DataFrame, qqq: pd.DataFrame, cost_bps: int) -> dict:
    market = qqq.set_index("Date"); max_error = 0.0
    previous_nav = 1.0
    for index,row in enumerate(log.itertuples(index=False)):
        p = market.loc[row.Date]
        mark = float(p.Open) if row.final_open_mark else float(p.Close)
        expected_nav = float(row.shares)*mark + float(row.cash)
        errors = [abs(expected_nav-float(row.nav)),
                  abs(float(log["return"].iloc[index])-(float(row.nav)/previous_nav-1)),
                  abs(float(row.cost)-float(cost_bps)/10000*float(row.trade_notional))]
        max_error = max(max_error, *errors)
        previous_nav=float(row.nav)
    if max_error > 2e-11:
        raise ValueError(f"Independent QQQ marked-NAV/trade-fee audit failed: {max_error}")
    return {"rows":len(log),"max_abs_nav_return_fee_error":max_error,"passed":True}


def csv_immutable(path: Path, frame: pd.DataFrame) -> str:
    raw=frame.to_csv(index=False,float_format="%.17g",lineterminator="\n").encode()
    if path.exists() and path.read_bytes()!=raw:raise ValueError(f"Immutable output differs: {path}")
    if not path.exists():path.write_bytes(raw)
    return sha(raw)


def main() -> None:
    H8_OUT.mkdir(parents=True, exist_ok=True)
    manifest=json.loads(QQQ_MANIFEST.read_bytes())
    qsource=next(s for s in manifest["sources"] if s["series"]=="QQQ")
    qpath=ROOT/qsource["raw_path"];checked_hash(qpath,qsource["raw_sha256"])
    qqq=pd.read_csv(qpath,float_precision="round_trip")
    qqq_audit=audit_qqq(qqq)
    h7=json.loads(H7_JSON.read_bytes());signals=pd.read_csv(H7_CSV,float_precision="round_trip")
    if signals.origin.duplicated().any() or not signals.origin.is_monotonic_increasing or len(signals)!=3520:
        raise ValueError("H7 signal date panel is not the registered 2012-2025 common sample")
    strategies={"buyhold":np.ones(len(signals)), **{name:np.clip(.1/np.sqrt(signals[name].to_numpy()),0,1)
                   for name in ("trailing","vix","garch","combined")}}
    zero_logs={};log_hashes={};metric_table={};audits={}
    for cost in COSTS:
        metric_table[str(cost)]={}
        for model,weights in strategies.items():
            log=simulate_spy(qqq,signals,weights,cost)
            zero_logs[model,cost]=log
            audit_ledger(log,qqq,cost)
            metric_table[str(cost)][model]=portfolio_metrics(log)
            log_hashes[f"zero_{model}_{cost}bps.csv"]=csv_immutable(OUT/f"ndx_qqq_h8_zero_{model}_{cost}bps.csv",log)

    rate_meta=json.loads(RATE_MANIFEST.read_bytes())
    schedules={}
    for name in ("DGS1MO","DTB4WK"):
        info=rate_meta["series"][name];path=ROOT/info["initial_path"]
        checked_hash(path,info["initial_sha256"])
        frame=pd.read_csv(path,float_precision="round_trip")
        dates=zero_logs["combined",5].Date.tolist()
        schedules[name]=rate_schedule(frame,dates,name)
    common_rf=schedules["DGS1MO"].cash_factor.to_numpy()
    zero_parts={}
    for model in MODELS:
        for cost in COSTS:
            zero_replay=cash_replay(qqq,zero_logs[model,cost],schedules["DGS1MO"],0.,cost)
            if not exact_reference_values(zero_replay,zero_logs[model,cost]):
                raise ValueError("Zero-interest accrual ledger does not reproduce frozen QQQ reference")
            zero_parts[model,cost]=independently_audit(
                zero_replay,qqq,schedules["DGS1MO"],"DGS1MO",0.,cost)[0]
    logs={}; summaries=[]; attributions=[]; ledger_audits={}; period_rows=[]
    for scenario in SCENARIOS:
        series="DTB4WK" if scenario=="dtb4wk_full" else "DGS1MO"
        multiplier={"zero":0.,"dgs1mo_full":1.,"dgs1mo_half":.5,"dtb4wk_full":1.}[scenario]
        schedule=schedules[series]
        for model in MODELS:
            for cost in COSTS:
                zero=zero_logs[model,cost]
                log=cash_replay(qqq,zero,schedule,multiplier,cost)
                if scenario=="zero" and not exact_reference_values(log,zero):
                    raise ValueError("Zero-cash QQQ replay did not exactly reproduce the frozen zero ledger")
                cash_parts,audit=independently_audit(log,qqq,schedule,series,multiplier,cost)
                extra=audit_ledger(log,qqq,cost)
                audits[f"{scenario}_{model}_{cost}"]={**audit,"independent_marked_nav_fee":extra}
                key=(scenario,model,cost);logs[key]=log
                attribution_row,parts=attribution(log,zero,cash_parts,zero_parts[model,cost])
                attribution_row.update({"scenario":scenario,"strategy":model,"cost_bps":cost})
                attributions.append(attribution_row)
                summary=summarize(log,zero,common_rf,schedule.cash_factor.to_numpy()*multiplier,parts)
                summary.update({"scenario":scenario,"strategy":model,"cost_bps":cost});summaries.append(summary)
                log_hashes[f"{scenario}_{model}_{cost}bps.csv"]=csv_immutable(H8_OUT/f"ndx_qqq_h8_{scenario}_{model}_{cost}bps.csv",log)
                if cost==5:
                    for period,(lo,hi) in PERIODS.items():
                        mask=log.Date.between(lo,hi).to_numpy();sub=log[mask].copy()
                        sub["nav"]=np.cumprod(1+sub["return"].to_numpy())
                        metric=portfolio_metrics(sub)
                        period_rows.append({"scenario":scenario,"strategy":model,"period":period,**metric,
                            "cash_income_initial_nav":float(log.cash_interest[mask].sum())})
        print("Completed QQQ ledger scenario",scenario,flush=True)
    for row in summaries:
        gross=logs[row["scenario"],row["strategy"],0];net=logs[row["scenario"],row["strategy"],row["cost_bps"]]
        row["gross_minus_net_cagr"]=portfolio_metrics(gross)["cagr"]-row["cagr"]
        row["gross_minus_net_log_growth"]=float(np.log1p(gross["return"]).sum()-np.log1p(net["return"]).sum())
    contrasts,ranks=bootstrap(logs,common_rf)
    commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    result={"status":"EXPLORATORY CROSS-MARKET H8 — PROVISIONAL / PENDING INDEPENDENT REVIEW",
        "market":"NASDAQ-100 / Cboe VXN / QQQ","code_commit":commit,
        "source_hashes":{"qqq":qsource["raw_sha256"],"rate_manifest":sha(RATE_MANIFEST.read_bytes()),
                         "h7_forecasts":sha(H7_CSV.read_bytes())},"qqq_audit":qqq_audit,
        "signals":len(signals),"executed_signals":len(signals)-1,"zero_cash_ledgers_replay_exact":len(MODELS)*len(COSTS),
        "models_refitted":0,"cost_bps":COSTS,"scenarios":SCENARIOS,"models":summaries,
        "periods_at_5bps":period_rows,"cash_attribution":attributions,"paired_uncertainty":contrasts,
        "ranking_uncertainty":ranks,"ledger_audits":audits,"ledger_sha256":log_hashes,
        "rate_policy":"Task 3 initial-release DGS1MO and DTB4WK quotes, available only on following calendar date, locked at prior execution open; ACT/365 actual calendar elapsed days.",
        "portfolio_policy":"Same next-XNYS-open signals, long-only 0-100% target, dividends paid on ex-date to old shares, actual QQQ open/close, same 0/1/5/10/25 bp fees, no 2025+ share split in study period.",
        "interpretation_limit":"Treasury quote accrual is not QQQ cash compensation or guaranteed broker sweep yield; exploratory external replication.",
        "bootstrap":{"blocks":[21,63,126],"draws":1000,"seed":1729}}
    for name,rows in (("summary",summaries),("periods",period_rows),("attribution",attributions),
                      ("uncertainty",contrasts),("ranking_uncertainty",ranks)):
        frame=pd.DataFrame(rows)
        for col in frame:
            if frame[col].map(lambda value:isinstance(value,list)).any():
                frame[col]=frame[col].map(lambda value:json.dumps(value) if isinstance(value,list) else value)
        csv_immutable(H8_OUT/f"ndx_qqq_h8_{name}.csv",frame)
    result_path=H8_OUT/"ndx_qqq_h8_v1.json"
    print(persist(result_path,result),flush=True)
    rank5=[r for r in summaries if r["scenario"] in ("zero","dgs1mo_full","dgs1mo_half","dtb4wk_full") and r["cost_bps"]==5]
    print(json.dumps({"rankings":{s:sorted([(r["strategy"],r["cagr"]) for r in rank5 if r["scenario"]==s],key=lambda x:-x[1]) for s in SCENARIOS},
                      "n":len(signals),"audit":qqq_audit},indent=2),flush=True)


if __name__=="__main__":
    main()
