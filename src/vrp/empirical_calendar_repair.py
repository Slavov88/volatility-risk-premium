"""Versioned H3/H4 cache correction and all fixed numerical inference."""
from __future__ import annotations
from calendar import monthrange
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import numpy as np
import pandas as pd
from dateutil.easter import easter
from scipy.signal import lfilter

from vrp.asof_garch_calendar import corrected_record, POLICY, forecast_schedule
from vrp.quant_calendar import regular_holiday_dates
from vrp.quant_extension import ROOT, sha, checked_hash, csv_immutable, implementation
from vrp.provisional_analysis import inputs, persist, checked_mean, checked_regression, FREEZE_SHA, EMPIRICAL_SHA
from vrp.recursive_garch import VARIANTS, training_slice
from vrp.calendar import trailing_30c_sessions, trailing_exchange_sessions, forward_30c_sessions, next_exchange_sessions
from vrp.evaluation import naive_variance_30c, naive_variance_21t, common_evaluation_mask
from vrp.inference import overlap_l0, holm_adjust_two
from vrp.forecast_analysis import qlike

STATUS = "CORRECTED / PROVISIONAL — PENDING INDEPENDENT COAUTHOR REVIEW"
OUT = ROOT/"outputs/empirical_calendar_repair/v1"
BASE = ROOT/"outputs/empirical_h1_h5/v1"


def independent_regular_holidays():
    """Independent OOS schedule with dated Juneteenth introduction."""
    def nth(y,m,weekday,n):
        first=date(y,m,1); return first+timedelta(days=(weekday-first.weekday())%7+7*(n-1))
    def last(y,m,weekday):
        end=date(y,m,monthrange(y,m)[1]); return end-timedelta(days=(end.weekday()-weekday)%7)
    def nearest(d):
        return d-timedelta(days=1) if d.weekday()==5 else d+timedelta(days=1) if d.weekday()==6 else d
    result=set()
    for y in range(2007,2027):
        ny=date(y,1,1);result.add(ny+timedelta(days=1) if ny.weekday()==6 else ny)
        result.update([nth(y,1,0,3),nth(y,2,0,3),easter(y)-timedelta(days=2),last(y,5,0),
                       nearest(date(y,7,4)),nth(y,9,0,1),nth(y,11,3,4),nearest(date(y,12,25))])
        if y>=2022:result.add(nearest(date(y,6,19)))
    return result


def holiday_audit():
    independent=independent_regular_holidays()
    pinned={d for d in regular_holiday_dates() if date(2007,1,1)<=d<=date(2026,12,31)}
    if pinned != independent:raise ValueError("Independent regular-holiday schedule differs")
    # Earliest target window containing newly observed Juneteenth must be after announcement.
    announcement=date(2021,9,28);first=date(2022,6,20)-timedelta(days=30)
    if first<=announcement:raise ValueError("Regular-holiday introduction uses future announcement")
    return {"status":"PASSED_INDEPENDENT_REGULAR_RULE_SCHEDULE", "rules_scope":"2007-2025 origins; horizons at most30c/22steps",
            "scheduled_holiday_dates_checked":len(pinned),"juneteenth_public_filing":"2021-09-28",
            "earliest30c_window_reaching_first_observance":first.isoformat(),
            "mlk_announced":"1997-06-05; effective1998, predates all OOS",
            "future_adhoc_policy":"ignore conservatively; actual targets/execution unaffected"}


def preserve():
    path=OUT/"preservation_snapshot.json"
    if path.exists():
        saved=json.loads(path.read_bytes())
        for name,digest in saved.items():checked_hash(ROOT/name,digest)
        return saved
    paths=[]
    for directory in ["outputs/empirical_h1_h5/v1","outputs/quant_extension/v2","data/processed/interim"]:
        paths.extend(p for p in (ROOT/directory).rglob("*") if p.is_file())
    paths.extend(ROOT/"docs"/name for name in ["h1_results.md","h2_results.md","h3_results.md","h4_results.md","h5_results.md","empirical_results_summary.md"])
    paths.extend(p for p in (ROOT/"data/manifests").glob("2026-10-13*.json"))
    saved={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))}
    persist(path,saved)
    return saved


def checked_first_variance(train,params,cached):
    residual=100*np.asarray(train)-params["mu"]
    tau=min(75,len(residual)); weights=.94**np.arange(tau);weights/=weights.sum()
    backcast=float(weights@residual[:tau]**2)
    forcing=params["omega"]+params["alpha[1]"]*np.r_[backcast,residual[:-1]**2]
    sigma,_=lfilter([1.],[1.,-params["beta[1]"]],forcing,zi=[params["beta[1]"]*backcast])
    expected=(params["omega"]+params["alpha[1]"]*residual[-1]**2+params["beta[1]"]*sigma[-1])/10000
    if not np.isclose(expected,cached,rtol=1e-9,atol=1e-14):
        raise ValueError("Independent first-step variance reconstruction failed")
    return abs(float(expected)-cached)


def caches(daily):
    meta=json.loads((ROOT/"data/manifests/2026-10-13_h1_h5_execution_v2.json").read_bytes())
    returns=daily.dropna(subset=["log_return"]);days=[date.fromisoformat(d) for d in returns.Date];values=returns.log_return.to_numpy()
    originals={}; corrected={}; audit={}
    for variant,(dist,window) in VARIANTS.items():
        paths=list((BASE/"garch"/variant).glob("*/forecasts.json"))
        if len(paths)!=1:raise ValueError("Ambiguous original GARCH cache")
        path=paths[0];folder=path.parent;source=meta["garch_sources"][variant]
        checked_hash(path,source["forecasts_sha256"]);checked_hash(folder/"configuration.json",source["configuration_sha256"])
        report=json.loads(path.read_bytes());config=json.loads((folder/"configuration.json").read_bytes())
        if config["distribution"]!=dist or config["window"]!=window or config["freeze_sha256"]!=FREEZE_SHA:
            raise ValueError("Exact fitted model/config mismatch")
        db=sqlite3.connect("file:"+(folder/"checkpoints.sqlite").resolve().as_posix()+"?mode=ro",uri=True)
        if db.execute("SELECT json FROM config WHERE id=1").fetchone()[0]!=json.dumps(config,sort_keys=True):
            raise ValueError("SQLite configuration mismatch")
        old=report["records"];new=[];changes=[];maxfirst=0.;maxrecurrence=0.;extended=0;metadata21=0
        if len(old)!=4780 or len({r["origin"] for r in old})!=4780:raise ValueError("Incomplete cached coverage")
        for r in old:
            payload,digest=db.execute("SELECT payload,sha256 FROM fits WHERE origin=?",(r["origin"],)).fetchone()
            if hashlib.sha256(payload.encode()).hexdigest()!=digest or json.loads(payload)!=r:raise ValueError("SQLite payload/hash mismatch")
            origin=date.fromisoformat(r["origin"]);start,end,train=training_slice(days,values,origin,window)
            expected={"training_n":len(train),"training_start":days[start].isoformat(),"training_end":days[end-1].isoformat(),
                      "training_sha256":hashlib.sha256(train.astype('<f8').tobytes()).hexdigest()}
            if any(r[k]!=v for k,v in expected.items()):raise ValueError("Training/as-of cache mismatch")
            actual=forward_30c_sessions(origin)
            if r["session_count_30c"]!=len(actual) or r["forecast_sessions"]!=[d.isoformat() for d in next_exchange_sessions(origin,max(len(actual),21))]:
                raise ValueError("Original calendar metadata replay mismatch")
            maxfirst=max(maxfirst,checked_first_variance(train,r["parameters"],r["daily_decimal_variances"][0]))
            c=corrected_record(r,dist);new.append(c)
            maxrecurrence=max(maxrecurrence,c["correction_audit"]["stored_recurrence_max_error_decimal_variance"])
            extended+=int(c["correction_audit"]["extended_steps"]>0)
            metadata21+=int(r["forecast_sessions"][:21]!=c["forecast_sessions"][:21])
            if r["session_count_30c"]!=c["session_count_30c"]:
                changes.append({"origin":r["origin"],"actual_count":r["session_count_30c"],"scheduled_count":c["session_count_30c"],
                                "original":r["garch_30c"],"corrected":c["garch_30c"],"signed_change":c["garch_30c"]-r["garch_30c"]})
        db.close();originals[variant]=old;corrected[variant]=new
        digest=persist(OUT/"forecasts"/f"{variant}.json",{"status":STATUS,"calendar_policy":POLICY,"original_source":source,"records":new})
        audit[variant]={"records":len(new),"forecast_refits":0,"changed30c_calendar_count_origins":len(changes),"extended_cached_vectors":extended,
                        "fixed21_numeric_changed":sum(a["garch_21t"]!=b["garch_21t"] for a,b in zip(old,new)),
                        "first21_forecast_date_metadata_changed":metadata21,"first_step_max_error_decimal_variance":maxfirst,
                        "stored_recurrence_max_error_decimal_variance":maxrecurrence,"corrected_forecasts_sha256":digest,"original_source":source,"changes":changes}
        print(variant,{k:v for k,v in audit[variant].items() if k not in ["changes","original_source"]},flush=True)
    return originals,corrected,audit


def analysis(dates,y,pred,horizon,nonoverlap=False):
    y=np.asarray(y,float);pred={name:np.asarray(v,float) for name,v in pred.items()}
    mask=common_evaluation_mask(dates,dict(zip(dates,y)),{m:dict(zip(dates,v)) for m,v in pred.items()})
    if [d.isoformat() for d in mask]!=dates:raise ValueError("Unequal common mask")
    metrics={m:{"n":len(y),"rmse":float(np.sqrt(np.mean((y-v)**2))),"mae":float(np.mean(abs(y-v))),
                "qlike":float(qlike(y,v).mean()),"bias_forecast_minus_actual":float((v-y).mean())} for m,v in pred.items()}
    l0=0 if nonoverlap else overlap_l0(dates) if horizon=="30c" else 20
    lags=[0] if nonoverlap else list(dict.fromkeys([l0,42,63] if horizon=="30c" else [20,10,21,42]))
    sq={m:(y-v)**2 for m,v in pred.items()};tests=[]
    for lag in lags:
        contrasts={label:checked_mean(sq[a]-sq[b],lag) for label,a,b in [("vix_vs_garch","vix","garch"),("vix_vs_naive","vix","naive"),("garch_vs_naive","garch","naive")]}
        adjusted=holm_adjust_two([contrasts["vix_vs_naive"]["p_value"],contrasts["garch_vs_naive"]["p_value"]])
        for label,p in zip(["vix_vs_naive","garch_vs_naive"],adjusted):contrasts[label]["holm_p_value"]=p
        tests.append({"lag":lag,"squared_error":contrasts,"qlike_vix_vs_garch":checked_mean(qlike(y,pred["vix"])-qlike(y,pred["garch"]),lag),
                      "h4":checked_regression(y,np.column_stack([pred["vix"],pred["garch"]]),lag)})
    return {"n_common":len(y),"common_origins_sha256":hashlib.sha256(("\n".join(dates)+"\n").encode()).hexdigest(),
            "metrics":metrics,"l0":l0,"tests":tests,"common_origins":dates}


def fixed_nonoverlap(origins,target_end):
    selected=[];last=None
    for i,(origin,end) in enumerate(zip(origins,target_end)):
        if last is None or origin>last:selected.append(i);last=end
    return np.array(selected,int)


def run():
    preserved=preserve();sys.path.insert(0,str(ROOT/"outputs/archive_inspection"))
    targets,daily,_=inputs(ROOT);holiday=holiday_audit()
    originals,corrected,cache_audit=caches(daily)
    sample=targets.loc[targets.origin>="2007-01-01"].copy();dates=sample.origin.tolist()
    if any([r["origin"] for r in original]!=dates for original in originals.values()):raise ValueError("Cache/target origin mismatch")
    returns={date.fromisoformat(d):float(v) for d,v in zip(daily.Date,daily.log_return) if np.isfinite(v)}
    analyses=[];comparison_rows=[];forecast_rows=[]
    for horizon in ("30c","21t"):
        naive=[]
        for d in dates:
            day=date.fromisoformat(d);sessions=trailing_30c_sessions(day) if horizon=="30c" else trailing_exchange_sessions(day,21)
            fn=naive_variance_30c if horizon=="30c" else naive_variance_21t
            naive.append(fn(day,[(s,returns[s]) for s in sessions]))
        for variant in VARIANTS:
            oldg=np.array([r[f"garch_{horizon}"] for r in originals[variant]])
            newg=np.array([r[f"garch_{horizon}"] for r in corrected[variant]])
            for d,a,b in zip(dates,oldg,newg):forecast_rows.append({"origin":d,"variant":variant,"horizon":horizon,"original":a,"corrected":b,"absolute_change":abs(b-a)})
            for family in ("cc","parkinson","gk"):
                actual=sample[f"rvar_{family}_fwd_{horizon}"].to_numpy()
                for period,cutoff in [("full","2007-01-01"),("post2014","2014-10-06")]:
                    idx=np.flatnonzero(sample.origin.to_numpy()>=cutoff)
                    for mask_name in ("overlapping","nonoverlap"):
                        selected=idx if mask_name=="overlapping" else idx[fixed_nonoverlap(sample.origin.iloc[idx].tolist(),sample[f"target_end_date_{horizon}"].iloc[idx].tolist())]
                        ds=sample.origin.iloc[selected].tolist();yy=actual[selected]
                        pair=[]
                        for values in (oldg,newg):
                            pair.append(analysis(ds,yy,{"vix":sample.ivar.to_numpy()[selected],"garch":values[selected],"naive":np.asarray(naive)[selected]},horizon,mask_name=="nonoverlap"))
                        old,new=pair
                        label={"variant":variant,"horizon":horizon,"family":family,"period":period,"mask":mask_name}
                        analyses.append({**label,"original_control":old,"corrected":new,
                                         "original_control_kind":"ARCHIVED_REPORTED_CELL" if family=="cc" and mask_name=="overlapping" else "NEW_FIXED_DIAGNOSTIC_ORIGINAL_FORECAST_REPLAY"})
                        for ot,nt in zip(old["tests"],new["tests"]):
                            values={"VIX RMSE":(old["metrics"]["vix"]["rmse"],new["metrics"]["vix"]["rmse"]),
                                    "GARCH RMSE":(old["metrics"]["garch"]["rmse"],new["metrics"]["garch"]["rmse"]),
                                    "GARCH MAE":(old["metrics"]["garch"]["mae"],new["metrics"]["garch"]["mae"]),
                                    "GARCH QLIKE":(old["metrics"]["garch"]["qlike"],new["metrics"]["garch"]["qlike"]),
                                    "H3 loss differential":(ot["squared_error"]["vix_vs_garch"]["mean"],nt["squared_error"]["vix_vs_garch"]["mean"]),
                                    "H3 p-value":(ot["squared_error"]["vix_vs_garch"]["p_value"],nt["squared_error"]["vix_vs_garch"]["p_value"]),
                                    "H4 VIX coefficient":(ot["h4"]["coefficients"][1],nt["h4"]["coefficients"][1]),
                                    "H4 GARCH coefficient":(ot["h4"]["coefficients"][2],nt["h4"]["coefficients"][2]),
                                    "H4 VIX p-value":(ot["h4"]["p_values"][1],nt["h4"]["p_values"][1]),
                                    "H4 GARCH p-value":(ot["h4"]["p_values"][2],nt["h4"]["p_values"][2])}
                            for name,(a,b) in values.items():comparison_rows.append({**label,"lag":ot["lag"],"metric":name,"original":a,"corrected":b,"signed_change":b-a,"absolute_change":abs(b-a)})
    digests={"forecast_comparison.csv":csv_immutable(OUT/"forecast_comparison.csv",pd.DataFrame(forecast_rows)),
             "metric_comparison.csv":csv_immutable(OUT/"metric_comparison.csv",pd.DataFrame(comparison_rows))}
    result={"status":STATUS,"freeze_sha256":FREEZE_SHA,"target_manifest_sha256":EMPIRICAL_SHA,"calendar_policy":POLICY,
            "holiday_audit":holiday,"cache_audit":cache_audit,"analyses":analyses,"output_sha256":digests,
            "preserved_files":len(preserved),"preservation_snapshot_sha256":sha(OUT/"preservation_snapshot.json"),
            "forecast_refits":0,"post2003_oos":"identical to full2007-2025 OOS",
            "implementation":implementation(["src/vrp/asof_garch_calendar.py","src/vrp/empirical_calendar_repair.py","src/vrp/recursive_garch.py","src/vrp/quant_calendar.py","scripts/run_empirical_calendar_repair.py"])}
    persist(OUT/"corrected_results.json",result)
    preserve()
    print({"status":STATUS,"sha256":sha(OUT/"corrected_results.json"),"analyses":len(analyses),"metric_rows":len(comparison_rows)},flush=True)
    return result
