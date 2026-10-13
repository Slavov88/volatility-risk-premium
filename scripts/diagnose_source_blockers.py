"""Replay supporting evidence and hypothetical correction footprints only."""
import argparse
from io import BytesIO
import json
import math
from pathlib import Path

import pandas as pd

from vrp.data import write_immutable
from vrp.processed_panel import _load_spx, _read_manifest, _verified_artifact
from vrp.spx_data import parse_fred_sp500
from vrp.spx_discrepancy_impact import correction_footprint
from vrp.vix_close_candidate import verify_candidate_close_panel, _source_vix

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--raw-root",type=Path,default=Path("data/raw"))
parser.add_argument("--processed-root",type=Path,default=Path("data/processed"))
parser.add_argument("--candidate-manifest",type=Path,required=True)
parser.add_argument("--notice-manifest",type=Path,required=True)
parser.add_argument("--fred-vix-manifest",type=Path,required=True)
parser.add_argument("--report",type=Path,required=True)
args=parser.parse_args()
root=args.raw_root.resolve()
panel=verify_candidate_close_panel(root,args.processed_root,args.candidate_manifest.resolve())
candidate,candidate_sha=_read_manifest(args.processed_root.resolve(),args.candidate_manifest.resolve(),"Candidate")
spx_record,_=_read_manifest(root,Path(candidate["source_manifests"]["spx"]["relative_path"]),"SPX")
vix_record,_=_read_manifest(root,Path(candidate["source_manifests"]["vix"]["relative_path"]),"VIX")
spx=_load_spx(root,spx_record)
vix=_source_vix(root,vix_record)
fred_raw=_verified_artifact(root,spx_record["fred_close_validation"],"FRED SP500")
fred,_=parse_fred_sp500(fred_raw)
fred_closes=dict(zip(fred.Date,fred.FRED_SP500))
dates=[r["date"] for r in spx_record["fred_close_validation"]["validation"]["discrepancy_sample"]]
footprints=correction_footprint(spx.Date.tolist(),spx.Close.tolist(),{d:fred_closes[d] for d in dates},panel.origin.tolist())
for item in footprints:
    item["source_discrepancy_classification"]=("INDEPENDENTLY_EXPLAINED_REQUIRES_METHODOLOGICAL_DECISION"
        if item["correction_date"]=="2019-08-12" else "UNRESOLVED_BUT_DOCUMENTED")
notices,notice_sha=_read_manifest(root,args.notice_manifest,"Notices")
for info in notices["sources"]:
    _verified_artifact(root,info,"Official notice")
fred_vix,fred_vix_sha=_read_manifest(root,args.fred_vix_manifest,"FRED VIX publication")
availability=[]
for info in fred_vix["sources"]:
    raw=_verified_artifact(root,info,"FRED VIX publication")
    data=pd.read_csv(BytesIO(raw))
    row=data[data.iloc[:,0]==info["investigated_date"]]
    number=pd.to_numeric(row["VIXCLS"],errors="coerce")
    finite=bool(len(number)==1 and math.isfinite(float(number.iloc[0])) and number.iloc[0]>0)
    if finite!=info["published_close_finite_positive"] or bool(len(row))!=info["published_row_present"]:
        raise ValueError("FRED VIX publication replay mismatch")
    availability.append({"date":info["investigated_date"],"row_present":bool(len(row)),"finite_positive_close":finite})
extra=[]
for day in candidate["validation"]["rejected_non_session_dates"]:
    index=vix.Date.tolist().index(day)
    extra.append({"date":day,
        "same_close_as_previous_provider_row":bool(index>0 and vix.iloc[index].CLOSE==vix.iloc[index-1].CLOSE),
        "classification":("OFFICIAL_FULL_CLOSURE_PUBLICATION_VALUE_UNEXPLAINED" if day=="2004-06-11" else
            "GTH_TRADING_DOCUMENTED_CSV_TIMESTAMP_UNCONFIRMED" if day in {"2022-05-30","2025-01-09"} else
            "HOLIDAY_PATTERN_GTH_EXPLANATION_PLAUSIBLE_NOT_INDIVIDUALLY_CONFIRMED"),
        "predictor_eligible":False})
report={"purpose":"Source validity / origin eligibility and hypothetical SPX correction footprint; no source correction or RVAR computation",
    "protocol_version":"1.1.0","approval_status":"CANDIDATE_UNAPPROVED",
    "candidate_manifest_sha256":candidate_sha,"source_data_hashes":{k:v["sha256"] for k,v in candidate["source_artifacts"].items()},
    "notice_manifest_sha256":notice_sha,"notice_sources":notices["sources"],
    "fred_vix_publication_manifest_sha256":fred_vix_sha,"missing_date_publication_checks":availability,
    "non_session_publication_diagnostics":extra,"hypothetical_single_close_correction_footprints":footprints,
    "changes_to_source_prices":0,"production_targets_or_hypothesis_tests_run":False,
    "limitations":["Holiday options trading schedules do not prove the timestamp of CSV CLOSE for each date.",
        "FRED VIXCLS is Cboe-sourced republication, not an independent calculation or authorized source substitute.",
        "Only 2019-08-12 has an independently verified correction explanation; source choice remains unapproved.",
        "Signed return changes are diagnostic counterfactuals; no empirical RVAR/VRP, H1-H5 or GARCH output generated."]}
digest=write_immutable(args.report,(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
print(f"diagnostics={args.report} sha256={digest}")
