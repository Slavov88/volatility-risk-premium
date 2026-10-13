"""Preservation/control audit across the registered calendar correction."""
import json
import numpy as np
import pandas as pd
from vrp.quant_extension import ROOT, OUT, persist, sha

old = ROOT/"outputs/quant_extension/v1"
before = {p: json.loads((old/f"{p}.json").read_bytes()) for p in ("h6","h7","h8")}
after = {p: json.loads((OUT/f"{p}.json").read_bytes()) for p in before}
assert before["h6"]["n"] == after["h6"]["n"] == before["h7"]["n"] == after["h7"]["n"]
assert before["h6"]["events"] == after["h6"]["events"]
controls = {}
for phase,names in [("h6",["A","B"]),("h7",["vix","trailing","har"])]:
    a = pd.read_csv(old/f"{phase}_forecasts.csv",float_precision="round_trip")
    b = pd.read_csv(OUT/f"{phase}_forecasts.csv",float_precision="round_trip")
    assert a.origin.tolist() == b.origin.tolist()
    for name in names:
        assert np.array_equal(a[name].to_numpy(),b[name].to_numpy())
        controls[phase+"_"+name] = "EXACT_FORECAST_CONTROL_UNCHANGED"
for cost in (0,1,5,10,25):
    for model in ("buyhold","trailing","vix"):
        name=f"h8_{model}_{cost}bps.csv"
        assert sha(old/name) == sha(OUT/name)
        controls[name] = "EXACT_LEDGER_CONTROL_UNCHANGED"
deltas = {"h6":{m:after["h6"]["models"][m]["brier"]-before["h6"]["models"][m]["brier"] for m in before["h6"]["models"]},
          "h7":{m:after["h7"]["models"][m]["qlike"]-before["h7"]["models"][m]["qlike"] for m in before["h7"]["models"]},
          "h8_combined_5bps":{k:after["h8"]["models"]["5"]["combined"][k]-before["h8"]["models"]["5"]["combined"][k] for k in ["cagr","rolling21_target_rmse","annual_vol"]}}
evidence={"status":"PASSED_VERSION_CONTROL_AND_PRESERVATION_AUDIT", "v1_status":"INVALIDATED_FOR_STRICT_AS_OF_CALENDAR", "controls":controls,
          "metric_changes_v2_minus_v1":deltas,"v1_sha256":{p:sha(old/f"{p}.json") for p in before},"v2_sha256":{p:sha(OUT/f"{p}.json") for p in after}}
persist(OUT/"version_comparison.json",evidence)
print(evidence)
