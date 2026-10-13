"""All-origin recursive GARCH with verified, immutable SQLite checkpoints."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from datetime import date
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sqlite3
import sys
import warnings

from arch import arch_model
import numpy as np
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera

from vrp.calendar import forward_30c_sessions, next_exchange_sessions
from vrp.dates import as_date
from vrp.evaluation import _subtract_years
from vrp.garch_units import from_garch_variance, to_garch_fit_returns
from vrp.provisional_analysis import STATUS, AUTHORIZATION, inputs, identity, persist, FREEZE_SHA, EMPIRICAL_SHA
from vrp.summary import summary_statistics

VARIANTS = {"normal_expanding": ("normal","expanding"),
    "t_expanding": ("t","expanding"), "normal_rolling5y": ("normal","rolling_5y")}
FIT_CONFIG = {"mean":"Constant","vol":"GARCH","p":1,"o":0,"q":1,
    "rescale":False,"update_freq":0,"disp":"off","show_warning":True,
    "optimizer":"SLSQP via arch default", "options":{"maxiter":1000,"ftol":1e-9},
    "starting_values":"arch deterministic defaults, cold start at every origin",
    "forecast_method":"analytic","seed":42,"fit_return_scale":100,"variance_backscale":10000,
    "nonconvergence":"record missing forecast, no alternate model or retries"}


def training_slice(days, values, origin, window):
    """Binary-search the same frozen calendar endpoints as estimation_window."""
    end=bisect_right(days,origin)
    start=0 if window=="expanding" else bisect_right(days,_subtract_years(origin,5))
    if window not in ("expanding","rolling_5y"): raise ValueError("Unknown estimation window")
    if not end or days[end-1]!=origin: raise ValueError("Origin return unavailable")
    selected=np.asarray(values[start:end],float)
    if not np.isfinite(selected).all(): raise ValueError("Non-finite training returns")
    return start,end,selected


def diagnostics(values):
    a=np.asarray(values,float); jb=jarque_bera(a);lb=acorr_ljungbox(a,lags=[10,21],return_df=True)
    sq=acorr_ljungbox(a*a,lags=[10,21],return_df=True);lm=het_arch(a,nlags=10)
    return {"summary":summary_statistics(a.tolist()),"jarque_bera":{"statistic":float(jb[0]),"p":float(jb[1])},
        "ljung_box_returns":lb.to_dict("index"),"ljung_box_squared_returns":sq.to_dict("index"),
        "arch_lm_10":{"statistic":float(lm[0]),"p":float(lm[1])},
        "leverage_corr_return_next_squared_return":float(np.corrcoef(a[:-1],a[1:]**2)[0,1]),
        "leverage_role":"descriptive signed return versus next squared return; no causality claim"}


def fit_origin(training, dist, steps, residual_diagnostics=False):
    record={"status":"FAILED","garch_30c":None,"garch_21t":None}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            model=arch_model(to_garch_fit_returns(training),mean="Constant",vol="GARCH",p=1,q=1,
                dist=dist,rescale=False)
            fit=model.fit(update_freq=0,disp="off",show_warning=True,options=FIT_CONFIG["options"])
            params={str(k):float(v) for k,v in fit.params.items()}
            record.update({"convergence_flag":int(fit.convergence_flag),"optimizer_message":str(fit.optimization_result.message),
                "parameters":params,"persistence":params["alpha[1]"]+params["beta[1]"],
                "log_likelihood":float(fit.loglikelihood),"optimizer_iterations":int(fit.optimization_result.nit)})
            if fit.convergence_flag==0:
                forecast=fit.forecast(horizon=steps,method="analytic",reindex=False).residual_variance.values[-1]
                if not np.isfinite(forecast).all() or np.any(forecast<=0): raise ValueError("Invalid model forecast")
                # Independent analytical recurrence, including shock at origin.
                independent=[params["omega"]+params["alpha[1]"]*float(fit.resid[-1])**2+
                    params["beta[1]"]*float(fit.conditional_volatility[-1])**2]
                for _ in range(1,steps): independent.append(params["omega"]+record["persistence"]*independent[-1])
                if not np.allclose(independent,forecast,rtol=1e-9,atol=1e-10): raise ValueError("GARCH recurrence oracle mismatch")
                record.update({"status":"CONVERGED","daily_decimal_variances":[from_garch_variance(v) for v in forecast],
                    "recurrence_max_abs_error_percent_squared":float(np.max(np.abs(forecast-independent)))})
                if residual_diagnostics: record["standardized_residual_diagnostics"]=diagnostics(np.asarray(fit.std_resid)[np.isfinite(fit.std_resid)])
        except Exception as error:
            record.update({"status":"FAILED","error_type":type(error).__name__,"error":str(error)})
        record["warnings"]=[{"category":w.category.__name__,"message":str(w.message)} for w in caught]
    return record


class Checkpoints:
    def __init__(self,path,config):
        path.parent.mkdir(parents=True,exist_ok=True);self.db=sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY CHECK(id=1), json TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS fits (origin TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)")
        encoded=json.dumps(config,sort_keys=True)
        row=self.db.execute("SELECT json FROM config WHERE id=1").fetchone()
        if row and row[0]!=encoded: raise ValueError("Checkpoint configuration mismatch")
        if not row: self.db.execute("INSERT INTO config VALUES (1,?)",(encoded,));self.db.commit()
    def read(self,origin,expected):
        row=self.db.execute("SELECT payload,sha256 FROM fits WHERE origin=?",(origin,)).fetchone()
        if not row:return None
        if hashlib.sha256(row[0].encode()).hexdigest()!=row[1]:raise ValueError("Checkpoint payload hash mismatch")
        data=json.loads(row[0])
        if any(data.get(k)!=v for k,v in expected.items()):raise ValueError("Checkpoint training/input identity mismatch")
        return data
    def write(self,origin,data):
        payload=json.dumps(data,sort_keys=True,allow_nan=False);digest=hashlib.sha256(payload.encode()).hexdigest()
        self.db.execute("INSERT INTO fits VALUES (?,?,?)",(origin,payload,digest));self.db.commit()
    def close(self): self.db.close()


def run(variant,commit,out_root,limit=None):
    np.random.seed(42)
    ident=identity(commit,["src/vrp/recursive_garch.py","src/vrp/provisional_analysis.py",
        "src/vrp/inference.py","src/vrp/evaluation.py","src/vrp/garch_units.py"])
    targets,daily,_=inputs();returns=daily.dropna(subset=["log_return"])
    days=[as_date(d) for d in returns.Date];values=returns.log_return.to_numpy()
    origins=targets.loc[targets.origin>="2007-01-01","origin"].tolist()
    dist,window=VARIANTS[variant]
    config={"variant":variant,"distribution":dist,"window":window,"fit":FIT_CONFIG,
        "implementation":ident,"freeze_sha256":FREEZE_SHA,"target_manifest_sha256":EMPIRICAL_SHA,
        "software":{"arch":version("arch"),"numpy":version("numpy"),"scipy":version("scipy"),"python":sys.version.split()[0]},
        "status":STATUS,"authorization":AUTHORIZATION,"origins":origins,
        "residual_diagnostic_origins":"first and final eligible origin of each calendar year, fixed before fits"}
    label=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    base=out_root/variant/label;base.mkdir(parents=True,exist_ok=True)
    persist(base/"configuration.json",config)
    # Return diagnostics exist before any fit. No future data enter fit windows.
    persist(base/"return_diagnostics.json",{"full_descriptive":diagnostics(values),
        "initial_through_2006":diagnostics(values[:bisect_right(days,date(2006,12,31))]),"status":STATUS})
    checkpoint=Checkpoints(base/"checkpoints.sqlite",config)
    records=[];reused=0
    anchors={next(d for d in origins if d[:4]==str(y)) for y in range(2007,2026)}
    anchors|={next(d for d in reversed(origins) if d[:4]==str(y)) for y in range(2007,2026)}
    for index,text in enumerate(origins):
        if limit is not None and index>=limit:break
        origin=as_date(text);start,end,train=training_slice(days,values,origin,window)
        sessions30=forward_30c_sessions(origin);sessions21=next_exchange_sessions(origin,21)
        sessions=next_exchange_sessions(origin,max(len(sessions30),21))
        if sessions[:len(sessions30)]!=sessions30:raise ValueError("Forward step/session mapping mismatch")
        expected={"origin":text,"training_start":days[start].isoformat(),"training_end":days[end-1].isoformat(),
            "training_n":len(train),"training_sha256":hashlib.sha256(train.astype('<f8').tobytes()).hexdigest(),
            "forecast_sessions":[d.isoformat() for d in sessions],"session_count_30c":len(sessions30)}
        record=checkpoint.read(text,expected)
        if record is None:
            record={**expected,**fit_origin(train,dist,len(sessions),text in anchors)}
            if record["status"]=="CONVERGED":
                forecasts=record["daily_decimal_variances"]
                record["garch_30c"]=(365/30)*sum(forecasts[:len(sessions30)])
                record["garch_21t"]=(252/21)*sum(forecasts[:21])
            checkpoint.write(text,record)
        else:reused+=1
        records.append(record)
        if (index+1)%100==0 or index==0:print(f"{variant}: {index+1}/{len(origins)} reused={reused} failed={sum(r['status']!='CONVERGED' for r in records)}",flush=True)
    checkpoint.close()
    result={"status":STATUS,"configuration_sha256":hashlib.sha256((base/"configuration.json").read_bytes()).hexdigest(),
        "expected_origins":len(origins),"completed_origins":len(records),"coverage_complete":len(records)==len(origins),
        "variant":variant,"records":records}
    if len(records)==len(origins):persist(base/"forecasts.json",result)
    print(f"checkpoint={base} coverage={len(records)}/{len(origins)} reused={reused}",flush=True)
    return base,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant",choices=VARIANTS,required=True);parser.add_argument("--code-commit",required=True)
    parser.add_argument("--parser-path",type=Path,required=True);parser.add_argument("--output-root",type=Path,required=True)
    parser.add_argument("--limit",type=int);args=parser.parse_args();sys.path.insert(0,str(args.parser_path.resolve()))
    run(args.variant,args.code_commit,args.output_root,args.limit)


if __name__=="__main__":main()
