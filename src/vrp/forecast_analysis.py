"""Common-mask forecast loss inference and encompassing; no model selection."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from vrp.calendar import trailing_30c_sessions, trailing_exchange_sessions
from vrp.dates import as_date
from vrp.evaluation import common_evaluation_mask, naive_variance_30c, naive_variance_21t
from vrp.inference import holm_adjust_two, overlap_l0
from vrp.provisional_analysis import (STATUS, inputs, identity, persist, checked_mean, checked_regression,
    FREEZE_SHA, EMPIRICAL_SHA)
from vrp.recursive_garch import Checkpoints, training_slice, VARIANTS


def qlike(realized,forecast):
    actual=np.asarray(realized,float);pred=np.asarray(forecast,float)
    if not np.isfinite(actual).all() or not np.isfinite(pred).all() or np.any(actual<=0) or np.any(pred<=0):
        raise ValueError("QLIKE requires finite strictly positive targets/forecasts")
    ratio=actual/pred
    return ratio-np.log(ratio)-1


def compare(targets,daily,records,variant):
    if len(records)!=4780:raise ValueError("Incomplete GARCH coverage; no full-period H3 conclusion")
    candidate=targets.loc[targets.origin>="2007-01-01"].copy()
    if candidate.origin.tolist()!=[r["origin"] for r in records]:raise ValueError("Forecast origins mismatch")
    returns={as_date(d):float(v) for d,v in zip(daily.Date,daily.log_return) if pd.notna(v)}
    result={"status":STATUS,"variant":variant,"expected_origins":len(candidate),
        "fit_counts":{"converged":sum(r["status"]=="CONVERGED" for r in records),
            "failed":sum(r["status"]!="CONVERGED" for r in records)},
        "failed_origins":[r["origin"] for r in records if r["status"]!="CONVERGED"],
        "warning_origin_count":sum(bool(r["warnings"]) for r in records),
        "persistence_summary":{},"horizons":{}}
    persistence=[r["persistence"] for r in records if "persistence" in r]
    result["persistence_summary"]={"min":min(persistence),"max":max(persistence),
        "median":float(np.median(persistence)),"near_one_ge_099":sum(p>=.99 for p in persistence),
        "at_or_above_one":sum(p>=1 for p in persistence)}
    from vrp.summary import summary_statistics
    names=sorted({p for r in records for p in r.get("parameters",{})})
    result["parameter_summaries"]={p:summary_statistics([r["parameters"][p] for r in records if p in r.get("parameters",{})]) for p in names}
    result["residual_diagnostic_anchors"]={r["origin"]:r["standardized_residual_diagnostics"] for r in records if "standardized_residual_diagnostics" in r}
    for horizon in ("30c","21t"):
        fn=naive_variance_30c if horizon=="30c" else naive_variance_21t
        naive={}
        for text in candidate.origin:
            origin=as_date(text)
            sessions=trailing_30c_sessions(origin) if horizon=="30c" else trailing_exchange_sessions(origin,21)
            naive[text]=fn(origin,[(d,returns[d]) for d in sessions if d in returns])
        target_map=dict(zip(candidate.origin,candidate[f"rvar_cc_fwd_{horizon}"]))
        forecasts={"vix":dict(zip(candidate.origin,candidate.ivar)),"naive":naive,
            "garch":{r["origin"]:r[f"garch_{horizon}"] for r in records}}
        mask=common_evaluation_mask(candidate.origin.tolist(),target_map,forecasts)
        dates=[d.isoformat() for d in mask]
        actual=np.array([target_map[d] for d in dates]);pred={name:np.array([values[d] for d in dates]) for name,values in forecasts.items()}
        squared={name:(actual-f)**2 for name,f in pred.items()}
        metrics={name:{"n":len(dates),"rmse":float(np.sqrt(loss.mean())),"mae":float(np.mean(np.abs(actual-pred[name]))),
            "mean_forecast_error_actual_minus_forecast":float(np.mean(actual-pred[name])),
            "forecast_bias_forecast_minus_actual":float(np.mean(pred[name]-actual)),
            "qlike":float(qlike(actual,pred[name]).mean())} for name,loss in squared.items()}
        l0=overlap_l0(dates) if horizon=="30c" else 20
        lags=list(dict.fromkeys([l0,42,63] if horizon=="30c" else [20,10,21,42]))
        tests=[];encompassing=[]
        for lag in lags:
            paired={"vix_vs_garch":checked_mean(squared["vix"]-squared["garch"],lag),
                "vix_vs_naive":checked_mean(squared["vix"]-squared["naive"],lag),
                "garch_vs_naive":checked_mean(squared["garch"]-squared["naive"],lag)}
            adjusted=holm_adjust_two([paired["vix_vs_naive"]["p_value"],paired["garch_vs_naive"]["p_value"]])
            for name,p in zip(["vix_vs_naive","garch_vs_naive"],adjusted):paired[name]["holm_p_value"]=p
            tests.append({"lag":lag,"squared_error":paired,
                "qlike_vix_vs_garch":checked_mean(qlike(actual,pred["vix"])-qlike(actual,pred["garch"]),lag)})
            regression=checked_regression(actual,np.column_stack([pred["vix"],pred["garch"]]),lag)
            encompassing.append(regression)
        result["horizons"][horizon]={"n_common":len(dates),"common_origins":dates,
            "common_origins_sha256":hashlib.sha256(("\n".join(dates)+"\n").encode()).hexdigest(),
            "excluded_origins":sorted(set(candidate.origin)-set(dates)),"metrics":metrics,"l0":l0,
            "loss_differences":"first named model minus second; negative favors first",
            "qlike_definition":"realized/forecast - log(realized/forecast) - 1",
            "h3_tests":tests,"h4":encompassing,
            "h4_coefficient_order":["alpha","beta_vix","gamma_garch"],
            "h4_restrictions":"individual beta=0 and gamma=0, asymptotic normal two-sided tests",
            "h3_h4_same_mask_verified":True,
            "case_study_metrics":{str(y):{name:{"n":sum(d[:4]==str(y) for d in dates),
                "rmse":float(np.sqrt(np.mean(loss[[d[:4]==str(y) for d in dates]]))),
                "mae":float(np.mean(np.abs(actual-pred[name])[[d[:4]==str(y) for d in dates]]))}
                for name,loss in squared.items()} for y in (2008,2020,2022)}}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-commit",required=True);parser.add_argument("--parser-path",type=Path,required=True)
    parser.add_argument("--garch-root",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.parser_path.resolve()))
    ident=identity(args.code_commit,["src/vrp/forecast_analysis.py","src/vrp/recursive_garch.py",
        "src/vrp/provisional_analysis.py","src/vrp/inference.py","src/vrp/evaluation.py","src/vrp/garch_units.py"])
    targets,daily,_=inputs();returns=daily.dropna(subset=["log_return"])
    days=[as_date(d) for d in returns.Date];values=returns.log_return.to_numpy()
    results=[];sources={}
    for variant in VARIANTS:
        paths=list((args.garch_root/variant).glob("*/forecasts.json"))
        if len(paths)!=1:raise ValueError("Exactly one complete frozen run required per variant")
        path=paths[0];forecast=json.loads(path.read_bytes());config_path=path.parent/"configuration.json"
        config=json.loads(config_path.read_bytes())
        if hashlib.sha256(config_path.read_bytes()).hexdigest()!=forecast["configuration_sha256"] or config["freeze_sha256"]!=FREEZE_SHA:
            raise ValueError("Forecast configuration identity mismatch")
        store=Checkpoints(path.parent/"checkpoints.sqlite",config)
        for record in forecast["records"]:
            origin=as_date(record["origin"]);start,end,train=training_slice(days,values,origin,config["window"])
            expected={"origin":record["origin"],"training_n":len(train),"training_start":days[start].isoformat(),
                "training_end":days[end-1].isoformat(),"training_sha256":hashlib.sha256(train.astype('<f8').tobytes()).hexdigest()}
            if store.read(record["origin"],expected)!=record:raise ValueError("Forecast/checkpoint replay mismatch")
        store.close()
        results.append(compare(targets,daily,forecast["records"],variant))
        sources[variant]={"forecasts_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"configuration_sha256":forecast["configuration_sha256"]}
    output={"status":STATUS,"implementation":ident,"freeze_sha256":FREEZE_SHA,"target_manifest_sha256":EMPIRICAL_SHA,
        "garch_sources":sources,"analyses":results}
    print("H3/H4",persist(args.output,output),flush=True)


if __name__=="__main__":main()
