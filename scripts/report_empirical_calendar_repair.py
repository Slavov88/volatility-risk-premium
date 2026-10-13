"""Source-bound corrected tables, impact summary and supersession metadata."""
import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
from vrp.empirical_calendar_repair import ROOT,OUT,BASE,STATUS,preserve
from vrp.quant_extension import sha,checked_hash
from vrp.provisional_analysis import persist


def fmt(value):
    if isinstance(value,(float,np.floating)):return f"{value:.14g}"
    if isinstance(value,list):return "["+", ".join(fmt(x) for x in value)+"]"
    return str(value)


def table(rows,columns):
    return "| "+" | ".join(columns)+" |\n|"+"|".join(["---"]*len(columns))+"|\n"+"\n".join("| "+" | ".join(fmt(row[k]) for k in columns)+" |" for row in rows)+"\n"


def run():
    result=json.loads((OUT/"corrected_results.json").read_bytes())
    audit=json.loads((OUT/"independent_audit.json").read_bytes())
    replay=json.loads((OUT/"deterministic_replay.json").read_bytes())
    extension=json.loads((OUT/"extension_control_replay.json").read_bytes())
    checked_hash(OUT/"corrected_results.json",audit["corrected_results_sha256"])
    for name,digest in result["output_sha256"].items():checked_hash(OUT/name,digest)
    primary=[];metrics=[];h3=[];h4=[];decisions=[];decision_count=0
    for a in result["analyses"]:
        old=a["original_control"];new=a["corrected"]
        for ot,nt in zip(old["tests"],new["tests"]):
            fields=[]
            for pair in ot["squared_error"]:
                key="p_value" if pair=="vix_vs_garch" else "holm_p_value"
                fields.append((pair,ot["squared_error"][pair][key],nt["squared_error"][pair][key]))
            fields.append(("qlike_vix_vs_garch",ot["qlike_vix_vs_garch"]["p_value"],nt["qlike_vix_vs_garch"]["p_value"]))
            fields.extend((label,ot["h4"]["p_values"][i],nt["h4"]["p_values"][i]) for i,label in enumerate(["alpha","beta","gamma"]))
            for label,before,after in fields:
                decision_count+=1
                if (before<.05)!=(after<.05):decisions.append({"variant":a["variant"],"family":a["family"],"period":a["period"],"horizon":a["horizon"],"mask":a["mask"],"lag":ot["lag"],"test":label,"original_p":before,"corrected_p":after})
        if a["family"]!="cc" or a["mask"]!="overlapping":continue
        tag={"variant":a["variant"],"period":a["period"],"horizon":a["horizon"],"N":new["n_common"]}
        for model,m in new["metrics"].items():metrics.append({**tag,"model":model,"RMSE":m["rmse"],"MAE":m["mae"],"QLIKE":m["qlike"],"bias f-y":m["bias_forecast_minus_actual"]})
        for ot,nt in zip(old["tests"],new["tests"]):
            for pair,t in nt["squared_error"].items():h3.append({**tag,"lag":nt["lag"],"pair":pair,"mean squared-loss difference":t["mean"],"SE":t["standard_error"],"95% CI":[t["ci_lower"],t["ci_upper"]],"p":t["p_value"],"Holm p":t.get("holm_p_value","primary, unadjusted")})
            v=nt["h4"]
            h4.append({**tag,"lag":nt["lag"],"alpha":v["coefficients"][0],"beta VIX":v["coefficients"][1],"gamma GARCH":v["coefficients"][2],
                       "beta95% CI":v["ci95"][1],"gamma95% CI":v["ci95"][2],"p beta":v["p_values"][1],"p gamma":v["p_values"][2]})
        if a["horizon"]=="30c":
            ot=old["tests"][0];nt=new["tests"][0]
            values={"VIX RMSE":(old["metrics"]["vix"]["rmse"],new["metrics"]["vix"]["rmse"]),"GARCH RMSE":(old["metrics"]["garch"]["rmse"],new["metrics"]["garch"]["rmse"]),
                    "H3 loss differential":(ot["squared_error"]["vix_vs_garch"]["mean"],nt["squared_error"]["vix_vs_garch"]["mean"]),"H3 p-value":(ot["squared_error"]["vix_vs_garch"]["p_value"],nt["squared_error"]["vix_vs_garch"]["p_value"]),
                    "H4 VIX coefficient":(ot["h4"]["coefficients"][1],nt["h4"]["coefficients"][1]),"H4 GARCH coefficient":(ot["h4"]["coefficients"][2],nt["h4"]["coefficients"][2])}
            for name,(before,after) in values.items():primary.append({"variant":a["variant"],"period":a["period"],"Metric":name,"Original":before,"Corrected":after,"Absolute change":abs(after-before)})
    decision_audit={"status":STATUS,"decision_threshold":.05,"comparisons_checked":decision_count,"changed_decisions":decisions,
                    "note":"H3 primary/raw QLIKE, secondary two-contrast Holm, all3 H4 coefficients; descriptive audit, not joint acceptance"}
    persist(OUT/"decision_audit.json",decision_audit)
    main=next(a for a in result["analyses"] if a["variant"]=="normal_expanding" and a["period"]=="full" and a["horizon"]=="30c" and a["family"]=="cc" and a["mask"]=="overlapping")
    test=main["corrected"]["tests"][0];loss=test["squared_error"]["vix_vs_garch"];reg=test["h4"]
    header=f"**{STATUS}**\n\n"
    text="# Corrected H3/H4 results\n\n"+header
    text+=f"Actual computations completed for all3 variants ×4780 OOS origins, with **0 refits**. Original fit parameters, first-step variance and full cached recurrences pass independently. Each variant has61 changed30c session-count origins,10 extended vectors,0 changed21t numeric forecasts, and63 changed first21 scheduled date annotations. Values below are annualized decimal variance, with RMSE in variance units. Source `{sha(OUT/'corrected_results.json')}`; data/target freezes unchanged.\n\n"
    text+=f"Primary Gaussian expanding CC30c: VIX RMSE={fmt(main['corrected']['metrics']['vix']['rmse'])}; GARCH RMSE={fmt(main['corrected']['metrics']['garch']['rmse'])}. H3 VIX-minus-GARCH squared-loss mean={fmt(loss['mean'])}, SE={fmt(loss['standard_error'])}, CI={fmt([loss['ci_lower'],loss['ci_upper']])}, p={fmt(loss['p_value'])}. H4 beta={fmt(reg['coefficients'][1])}, gamma={fmt(reg['coefficients'][2])}; gamma CI={fmt(reg['ci95'][2])}, p={fmt(reg['p_values'][2])}.\n\n"
    text+="Primary conclusions unchanged: VIX has lower RMSE, but no statistically established paired squared-loss advantage; primary H4 GARCH increment remains uncertain, whereas VIX's zero-coefficient null is rejected. These coefficient-zero tests do not test unbiased calibration or causality. Rolling5y gamma remains marginal at the original5% threshold; its corrected full30c p is0.04846187433844171. Post2014 primary gamma remains insignificant. No stronger inference or independent acceptance is claimed.\n\n"
    text+="## Required old/corrected numerical comparison\n\nCC30c, primary overlap-derived lag21, full2007–2025 and post2014-10-06. Absolute change is |corrected−original|; signed changes are in CSV.\n\n"+table(primary,["variant","period","Metric","Original","Corrected","Absolute change"])
    text+="\n## Corrected losses: both horizons and all models\n\n"+table(metrics,list(metrics[0]))
    text+="\n## H3 squared-loss inference and Holm sensitivities\n\nNegative differences favor first-named model. Primary VIX/GARCH contrast remains unadjusted under the frozen protocol; the two naive contrasts use Holm at each fixed lag. Bartlett HAC finite-sample correction N/(N−k), normal intervals; independent score-sandwich checks passed.\n\n"+table(h3,list(h3[0]))
    text+="\n## H4 encompassing, all required lag/period sensitivities\n\n"+table(h4,list(h4[0]))
    text+=f"\nComplete72 cells cover CC/Parkinson/GK,30c/21t,3 variants,full/post2014 and deterministic non-overlap. All36 fixed21 analysis objects (metrics, tests, coefficients and masks) are exactly identical to original-forecast controls. All{decision_count} checked5% decisions are unchanged ({len(decisions)} changes). Additional range/non-overlap cells absent from old reports are explicitly **new fixed diagnostic original-forecast replays**, not falsely labeled archived results. Full QLIKE loss differences/CIs, all coefficients/intercept intervals and diagnostics, and all1620 metric comparisons are in the sanitized numerical manifest and local source JSON/CSVs. Post2003 OOS is identical to the full2007+ OOS.\n\n"
    text+="Fixed2008/2020/2022 crisis losses for all variants/horizons/estimators are in `case_metrics.csv` and the tracked cases manifest. No dates were selected after outcomes. Scientific targets use actual exchange sessions; predicted horizons use scheduled sessions. Future ad-hoc closures are excluded even if some were already announced: conservative information restriction, not optimal use of all available notices.61 count changes do not mean every origin was proven pre-announcement.\n\n"
    text+="Reproduce with `scripts/run_empirical_calendar_repair.py`; use `scripts/replay_empirical_calendar_repair.py` in a later checkout to compare every numeric field while recording Git metadata separately. Read-only cache validation, source/result/target hashes and full producer/source/record identity are preserved. Provider artifacts remain local ignored files; fresh clones need them for empirical replay. Original reports/results remain byte-identical; see [impact and supersession](empirical_calendar_impact.md).\n"
    (ROOT/"docs/h3_h4_corrected_results.md").write_text(text,encoding="utf-8",newline="\n")
    rows=[]
    for variant,x in result["cache_audit"].items():
        biggest=max(x["changes"],key=lambda y:abs(y["signed_change"]))
        rows.append({"variant":variant,"changed30c origins":x["changed30c_calendar_count_origins"],"extended vectors":x["extended_cached_vectors"],"changed21t values":x["fixed21_numeric_changed"],"max absolute forecast change":abs(biggest["signed_change"]),"max-change origin":biggest["origin"],"first-step reconstruction error":x["first_step_max_error_decimal_variance"]})
    impact="# Empirical calendar impact and version status\n\n"+header
    impact+="**Current H3/H4 evidence:** [corrected results](h3_h4_corrected_results.md). Original30c GARCH-based H3/H4 comparisons are **SUPERSEDED / INVALID_FOR_STRICT_EX_ANTE_FORECASTING**; their result JSON/manifests, original reports and hashes remain immutable. Original21t numerical evidence is verified unaffected, but date metadata is superseded. This repair changes the forecasting information set, not any fit, target, criterion or selected model.\n\n"
    impact+=table(rows,list(rows[0]))
    impact+=f"\nH1/H2 **all cells exactly reproduced**; formal H5 **all regressions exactly reproduced**. The original target data, VIX, source freeze, NBER labels and inference specifications are unchanged. H5 has a real ancillary dependency: it embeds primary H3 crisis forecast-loss tables. Two GARCH case RMSE display values differ only by floating-point summation: {json.dumps(audit['h5_case_loss_changes'],ensure_ascii=False)}. These are rounding-scale companion-table changes, not revised H5 regime evidence. Preserve original H5 and use the corrected case-loss companion in the audit/cases manifest; never claim the entire H5 artifact is independent of GARCH.\n\n"
    impact+="H6–H8 v2 control: full H6/H7/H8 recomputation passes exact predictor-source hashes, every numerical field and all27 forecast/trade CSV bytes, with original result hashes unchanged. No reranking, refitting of historical GARCH, strategy change or data acquisition. Its Gaussian reaggregation helper already uses this corrected policy.\n\n"
    impact+=f"Calendar-rule verification:185 rule-generated dates2007–2026 match an independent standard-holiday implementation. Juneteenth's2022 observation was known before relevant horizons: [SEC Release34-93183,2021-09-30](https://www.sec.gov/rules/sro/nyse/2021/34-93183.pdf) states filing2021-09-28 and immediate operability. MLK effective1998 predates all OOS; obsolete election/Lincoln/Washington rules end earlier. This verification is limited to the registered2007–2025 origins and30c/at-most22-step horizons, not an assurance of arbitrary historical/horizon safety.\n\n"
    impact+=f"Numerical verification: {audit['archived_CC_inference_cells_replayed']} archived full/post2014 CC lag cells independently replayed; first-step reconstruction error0 for every cached fit; stored recurrence error<=1.74e-18 decimal variance; independent QLIKE identity error{fmt(audit['independent_qlike_max_error'])}. Full producer replay repeats all14340 cache checks and all72 analysis cells exactly, including forecast JSON and comparison CSV bytes. H6–H8 v2 also fully replayed unchanged.\n\n"
    impact+="Original baseline summary/report files are intentionally not edited because their raw-byte hashes form the preserved evidence and extension's validation boundary. Current [versioned empirical summary](empirical_results_summary_calendar_v1.md), README, research-progress and experiment-log links point here. No independent coauthor acceptance or publication readiness is implied. Local validation1816 tests passed; compileall/diff-check and remote CI recorded in the current progress log.\n\n"
    impact+="Artifacts: `outputs/empirical_calendar_repair/v1/{corrected_results.json,forecasts/,metric_comparison.csv,forecast_comparison.csv,case_metrics.csv,independent_audit.json,decision_audit.json,deterministic_replay.json,extension_control_replay.json,preservation_snapshot.json}`. Sanitized manifests under `data/manifests/empirical_calendar_repair_*` preserve exact scalar results/settings/hashes without original provider prices. Failed synthetic assertions (selector return type; weekday rather than XNYS fixture dates) were corrected before final testing; no empirical run or cached fit failed.\n"
    (ROOT/"docs/empirical_calendar_impact.md").write_text(impact,encoding="utf-8",newline="\n")
    summary="# Current empirical results summary — calendar correction v1\n\n"+header
    summary+="The preserved H1–H5 summary is a historical baseline. Current H3/H4 uses the registered as-of calendar repair: [method record](h3_h4_calendar_correction.md), [corrected results](h3_h4_corrected_results.md), [impact/supersession](empirical_calendar_impact.md).\n\n"
    summary+=f"Primary Gaussian CC30c H3 mean loss difference{fmt(loss['mean'])}, CI{fmt([loss['ci_lower'],loss['ci_upper']])}, p{fmt(loss['p_value'])}; H4 beta{fmt(reg['coefficients'][1])}, gamma{fmt(reg['coefficients'][2])}, gamma p{fmt(reg['p_values'][2])}. Substantive conclusions unchanged, no checked5% decisions change. Fixed21 metrics/inference exactly unchanged. H1/H2 and formal H5 regressions exactly reproduced; H5's borrowed crisis-loss table companion changes only at rounding scale. H6–H8 v2 source/numeric/CSV replay exact. All original hashes preserved;0 GARCH refits. Independent review remains pending.\n"
    (ROOT/"docs/empirical_results_summary_calendar_v1.md").write_text(summary,encoding="utf-8",newline="\n")
    compact=copy.deepcopy(result)
    for a in compact["analyses"]:
        for k in ("original_control","corrected"):a[k].pop("common_origins")
    for v in compact["cache_audit"].values():
        v["changed_origin_dates"]=[c["origin"] for c in v.pop("changes")]
    persist(ROOT/"data/manifests/empirical_calendar_repair_results_v1.json",compact)
    cases=pd.read_csv(OUT/"case_metrics.csv",float_precision="round_trip").to_dict("records")
    persist(ROOT/"data/manifests/empirical_calendar_repair_cases_v1.json",{"status":STATUS,"case_metrics":cases})
    for name in ("independent_audit","decision_audit","deterministic_replay","extension_control_replay","preservation_snapshot"):
        persist(ROOT/f"data/manifests/empirical_calendar_repair_{name}_v1.json",json.loads((OUT/f"{name}.json").read_bytes()))
    sources=json.loads((ROOT/"data/manifests/2026-10-13_h1_h5_execution_v2.json").read_bytes())
    status={"status":STATUS,"superseded_original_results":{"h3_h4.json":sources["result_sources"]["h3_h4.json"],"h3_h4_post2014.json":sources["result_sources"]["h3_h4_post2014.json"]},
            "original30c_inference_status":"SUPERSEDED_INVALID_FOR_STRICT_EX_ANTE_CALENDAR","original21t_numeric_status":"VERIFIED_EXACT_UNCHANGED; scheduled date metadata superseded",
            "unchanged_H1_H2_H5_result_hashes":audit["unchanged_result_hashes"],"H5_ancillary_case_losses":"updated companion only; formal regressions exact",
            "current_corrected_results_sha256":sha(OUT/"corrected_results.json"),"cache_original_hashes":result["cache_audit"],"independent_review":"PENDING"}
    status["cache_original_hashes"]={v:x["original_source"] for v,x in result["cache_audit"].items()}
    persist(ROOT/"data/manifests/empirical_calendar_repair_status_v1.json",status)
    files=["h3_h4_corrected_results.md","empirical_calendar_impact.md","empirical_results_summary_calendar_v1.md"]
    stable_names=["corrected_results.json","forecast_comparison.csv","metric_comparison.csv","case_metrics.csv","independent_audit.json","decision_audit.json","deterministic_replay.json","extension_control_replay.json","preservation_snapshot.json"]
    stable_paths=[OUT/name for name in stable_names]+list((OUT/"forecasts").glob("*.json"))+list((OUT/"historical_log_snapshots").glob("*.md"))
    manifest={"status":STATUS,"results_sha256":sha(OUT/"corrected_results.json"),"report_sha256":{f:sha(ROOT/"docs"/f) for f in files},
              "local_output_sha256":{p.relative_to(OUT).as_posix():sha(p) for p in sorted(stable_paths)},
              "generator_sha256_lf":__import__('hashlib').sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),"independent_review":"PENDING"}
    manifest["supersedes_preliminary_inventory"]="empirical_calendar_repair_execution_v1/v2.json; final table-header formatting, numerical results unchanged"
    manifest["archived_prior_impact_report_sha256"]=sha(OUT/"publication_drafts/inventory_v2/empirical_calendar_impact.md")
    persist(ROOT/"data/manifests/empirical_calendar_repair_execution_v3.json",manifest)
    preserve();print({"reports":files,"manifest_sha256":sha(ROOT/"data/manifests/empirical_calendar_repair_execution_v3.json"),"decision_changes":decisions,"decisions_checked":decision_count})


if __name__=="__main__":run()
