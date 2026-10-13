"""Archived-result replay, scoring controls, H1/H2/H5 dependency and cases."""
import copy
from datetime import date
import json
import sys
import numpy as np
import pandas as pd
from vrp.empirical_calendar_repair import ROOT,OUT,BASE,STATUS,preserve,analysis
from vrp.quant_extension import sha,checked_hash,csv_immutable
from vrp.provisional_analysis import inputs,persist,run_h1_h2
from vrp.regime_analysis import analyze as regimes
from vrp.calendar import trailing_30c_sessions,trailing_exchange_sessions
from vrp.evaluation import naive_variance_30c,naive_variance_21t


def close(a,b,name):
    if not np.allclose(a,b,rtol=1e-11,atol=1e-13):raise ValueError("Archived numeric control differs: "+name)


def run():
    preserve();sys.path.insert(0,str(ROOT/"outputs/archive_inspection"))
    targets,daily,_=inputs(ROOT);new=json.loads((OUT/"corrected_results.json").read_bytes())
    original=json.loads((BASE/"h3_h4.json").read_bytes());post=json.loads((BASE/"h3_h4_post2014.json").read_bytes())
    original_checks=0;decisions=[];fixed21_cells=0;score_errors=[]
    for a in new["analyses"]:
        old=a["original_control"];corrected=a["corrected"]
        if a["horizon"]=="21t":
            if old!=corrected:raise ValueError("Fixed21 inference unexpectedly changed")
            fixed21_cells+=1
        if a["family"]=="cc" and a["mask"]=="overlapping":
            archived=next(x for x in original["analyses"] if x["variant"]==a["variant"])["horizons"][a["horizon"]]
            for o in old["tests"]:
                if a["period"]=="full":
                    source=next(x for x in archived["h3_tests"] if x["lag"]==o["lag"])
                    regression=next(x for x in archived["h4"] if x["lag"]==o["lag"])
                    for model in old["metrics"]:
                        for metric in ("rmse","mae","qlike"):close(old["metrics"][model][metric],archived["metrics"][model][metric],metric)
                    contrast=source["squared_error"]
                else:
                    source=next(x for x in post["analyses"] if x["variant"]==a["variant"] and x["horizon"]==a["horizon"] and x["lag"]==o["lag"])
                    regression=source["h4"];contrast=source["h3"]
                    for model in old["metrics"]:
                        for metric in ("rmse","mae"):close(old["metrics"][model][metric],source["metrics"][model][metric],metric)
                for pair in contrast:
                    for field in ("mean","standard_error","p_value","ci_lower","ci_upper"):
                        close(o["squared_error"][pair][field],contrast[pair][field],field)
                for field in ("coefficients","se","ci95","p_values"):
                    close(o["h4"][field],regression[field],field)
                original_checks+=1
        for ot,nt in zip(old["tests"],corrected["tests"]):
            for pair in ot["squared_error"]:
                key="p_value" if pair=="vix_vs_garch" else "holm_p_value"
                if (ot["squared_error"][pair][key]<.05)!=(nt["squared_error"][pair][key]<.05):decisions.append({**{k:a[k] for k in ["variant","family","period","horizon","mask"]},"lag":ot["lag"],"test":pair})
            for i,label in [(1,"beta_vix"),(2,"gamma_garch")]:
                if (ot["h4"]["p_values"][i]<.05)!=(nt["h4"]["p_values"][i]<.05):decisions.append({"variant":a["variant"],"period":a["period"],"test":label})
    # Case metrics retain all original fixed years, models, horizons and variants.
    forecasts=pd.read_csv(OUT/"forecast_comparison.csv",float_precision="round_trip")
    returns={date.fromisoformat(d):float(v) for d,v in zip(daily.Date,daily.log_return) if np.isfinite(v)}
    cases=[];corrected_case_primary={}
    for year in (2008,2020,2022):
        sample=targets.loc[targets.origin.str.startswith(str(year))];dates=sample.origin.tolist()
        for horizon in ("30c","21t"):
            naive=[]
            for d in dates:
                origin=date.fromisoformat(d);sessions=trailing_30c_sessions(origin) if horizon=="30c" else trailing_exchange_sessions(origin,21)
                fn=naive_variance_30c if horizon=="30c" else naive_variance_21t
                naive.append(fn(origin,[(s,returns[s]) for s in sessions]))
            for variant in ("normal_expanding","t_expanding","normal_rolling5y"):
                selected=forecasts.loc[forecasts.variant.eq(variant)&forecasts.horizon.eq(horizon)&forecasts.origin.str.startswith(str(year))]
                if selected.origin.tolist()!=dates:raise ValueError("Case forecast mask mismatch")
                for family in ("cc","parkinson","gk"):
                    y=sample[f"rvar_{family}_fwd_{horizon}"].to_numpy()
                    for version in ("original","corrected"):
                        predictions={"vix":sample.ivar.to_numpy(),"garch":selected[version].to_numpy(),"naive":np.asarray(naive)}
                        mm={}
                        for model,f in predictions.items():
                            squared=(y-f)**2;ql=y/f+np.log(f)-np.log(y)-1
                            mm[model]={"n":len(y),"rmse":float(np.sqrt(squared.mean())),"mae":float(abs(y-f).mean()),"qlike":float(ql.mean())}
                            cases.append({"year":year,"variant":variant,"horizon":horizon,"family":family,"version":version,"model":model,**mm[model]})
                        if family=="cc" and horizon=="30c" and variant=="normal_expanding" and version=="corrected":
                            corrected_case_primary[str(year)]={m:{k:v for k,v in x.items() if k!="qlike"} for m,x in mm.items()}
    csv_immutable(OUT/"case_metrics.csv",pd.DataFrame(cases))
    # Real dependency audit: H5 embeds H3 case losses, but its regression inputs do not use GARCH.
    h1_h2=run_h1_h2(targets);archived12=json.loads((BASE/"h1_h2.json").read_bytes())
    if h1_h2["h1"]!=archived12["h1"] or h1_h2["h2"]!=archived12["h2"]:raise ValueError("H1/H2 control changed")
    chronology=json.loads((ROOT/"data/manifests/2026-10-13_nber_chronology.json").read_bytes())
    corrected_h3=copy.deepcopy(original)
    corrected_h3["analyses"][0]["horizons"]["30c"]["case_study_metrics"]=corrected_case_primary
    rerun5=regimes(targets,chronology,corrected_h3);archived5=json.loads((BASE/"h5.json").read_bytes())
    if rerun5["regressions"]!=archived5["regressions"]:raise ValueError("Formal H5 control changed")
    h5_case_changes=[]
    for year,metrics in corrected_case_primary.items():
        old=archived5["case_studies"][year]["primary_forecast_losses"]
        for model in metrics:
            for metric in ("rmse","mae"):
                difference=metrics[model][metric]-old[model][metric]
                if difference!=0:h5_case_changes.append({"year":year,"model":model,"metric":metric,"original":old[model][metric],"corrected":metrics[model][metric],"signed_change":difference})
    # Independent scoring on all full CC vectors.
    for variant in ("normal_expanding","t_expanding","normal_rolling5y"):
        for horizon in ("30c","21t"):
            rows=forecasts.loc[forecasts.variant.eq(variant)&forecasts.horizon.eq(horizon)]
            sample=targets.loc[targets.origin.isin(rows.origin)]
            y=sample[f"rvar_cc_fwd_{horizon}"].to_numpy();f=rows.corrected.to_numpy()
            cell=next(a for a in new["analyses"] if a["variant"]==variant and a["period"]=="full" and a["horizon"]==horizon and a["family"]=="cc" and a["mask"]=="overlapping")
            error=abs(float((y/f+np.log(f)-np.log(y)-1).mean())-cell["corrected"]["metrics"]["garch"]["qlike"])
            if error>1e-13:raise ValueError("Independent QLIKE identity failed")
            score_errors.append(error)
    result={"status":STATUS,"archived_CC_inference_cells_replayed":original_checks,"fixed21_analysis_cells_exact":fixed21_cells,
            "five_percent_decision_changes":decisions,"h1_h2_all_cells_exact":True,"h5_all_regressions_exact":True,
            "h5_case_forecast_loss_dependency":True,"h5_case_loss_changes":h5_case_changes,
            "h5_updated_case_forecast_loss_companion":corrected_case_primary,"independent_qlike_max_error":max(score_errors),
            "corrected_results_sha256":sha(OUT/"corrected_results.json"),"case_metrics_sha256":sha(OUT/"case_metrics.csv"),
            "unchanged_result_hashes":{name:sha(BASE/name) for name in ["h1_h2.json","h5.json"]}}
    persist(OUT/"independent_audit.json",result);preserve();print(result)
    return result


if __name__=="__main__":run()
