"""Frozen NBER HTML chronology and provisional ex-post H5 analysis."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

from vrp.inference import overlap_l0, nonoverlapping_origins_30c
from vrp.provisional_analysis import STATUS, identity, inputs, persist, checked_regression, FREEZE_SHA, EMPIRICAL_SHA
from vrp.regimes import recession_months_from_chronology, label_nber_regimes
from vrp.summary import summary_statistics

NBER_SHA="99401340ae9b97310803cdcd0db0731ba4b4739f5425a83c370d268e3fa5795d"
NBER_URL="https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions"
EXPECTED=[("1990-07","1991-03"),("2001-03","2001-11"),("2007-12","2009-06"),("2020-02","2020-04")]


def parse_nber(raw):
    soup=BeautifulSoup(raw,"html.parser");table=soup.find("table")
    if table is None:raise ValueError("Missing official chronology table")
    episodes=[]
    for row in table.find_all("tr"):
        cells=[c.get_text(" ",strip=True) for c in row.find_all("td")]
        if len(cells)<2:continue
        match=re.match(r"^([A-Za-z]+ \d{4})\s*\(",cells[0])
        trough=re.match(r"^([A-Za-z]+ \d{4})\s*\(",cells[1])
        if not match or not trough:continue
        peak=datetime.strptime(match[1],"%B %Y").strftime("%Y-%m")
        end=datetime.strptime(trough[1],"%B %Y").strftime("%Y-%m")
        if peak>="1990-01":episodes.append((peak,end))
    if episodes!=EXPECTED:raise ValueError("NBER frozen monthly episode contract mismatch")
    months=pd.period_range("1990-01","2025-12",freq="M")
    flags=[int(any(pd.Period(p,"M")<m<=pd.Period(t,"M") for p,t in episodes)) for m in months]
    return [{"month":str(m),"date":m.start_time.date().isoformat(),"recession":f} for m,f in zip(months,flags)]


def freeze_chronology(source_manifest):
    source=json.loads(source_manifest.read_bytes())
    if source["source_url"]!=NBER_URL or source["sha256"]!=NBER_SHA:raise ValueError("NBER identity mismatch")
    raw=(Path("data/raw")/source["relative_path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=NBER_SHA:raise ValueError("NBER snapshot hash mismatch")
    months=parse_nber(raw)
    return {"source":source,"episodes":[{"peak":p,"trough":t} for p,t in EXPECTED],
        "monthly_rule":"peak exclusive, trough inclusive; all later months expansion until next dated peak",
        "chronology_role":"ex-post, never a predictor; current-vintage labels may be revised",
        "monthly_flags":months,"recession_month_count":sum(m["recession"] for m in months)}


def analyze(targets,chronology,forecasts):
    months=chronology["monthly_flags"]
    recession=recession_months_from_chronology([m["date"] for m in months],[m["recession"] for m in months])
    sample=targets.copy();labels=label_nber_regimes(sample.origin.tolist(),recession)
    sample["recession_indicator"]=[int(label=="recession") for _,label in labels]
    results=[]
    for subset,lower in {"full":"1990-01-02","post2003":"2004-01-01","post2014":"2014-10-06"}.items():
        data=sample.loc[sample.origin>=lower];l0=overlap_l0(data.origin.tolist())
        for horizon in ("30c","21t"):
            for family in ("cc","parkinson","gk"):
                for lag in dict.fromkeys([l0,42,63] if horizon=="30c" else [20,10,21,42]):
                    for obj in ("vrp_x","volgap"):
                        y=data[f"{obj}_{family}_{horizon}"]
                        result=checked_regression(y,data.recession_indicator,lag,[[0,1]],[0])
                        result.update({"subset":subset,"horizon":horizon,"family":family,"object":obj,"l0":l0,
                            "regimes":{name:{"n":int((data.recession_indicator==flag).sum()),
                                "mean":float(y[data.recession_indicator==flag].mean()),
                                "median":float(y[data.recession_indicator==flag].median())}
                                for name,flag in (("expansion",0),("recession",1))}})
                        results.append(result)
        chosen={d.isoformat() for d in nonoverlapping_origins_30c(data.origin.tolist())}
        nonoverlap=data.loc[data.origin.isin(chosen)]
        result=checked_regression(nonoverlap.vrp_x_cc_30c,nonoverlap.recession_indicator,0,[[0,1]],[0])
        results.append({"subset":subset,"horizon":"30c_nonoverlap","family":"cc","object":"vrp_x",**result})
    primary=forecasts["analyses"][0]
    common=set(primary["horizons"]["30c"]["common_origins"])
    cases={}
    for year in (2008,2020,2022):
        data=sample.loc[sample.origin.str.startswith(str(year)) & sample.origin.isin(common)]
        cases[str(year)]={"start":f"{year}-01-01","end":f"{year}-12-31","n":len(data),
            "membership":"forecast origin on primary H3 common mask; complete targets retained across year-end",
            "statistics":{c:summary_statistics(data[c].tolist()) for c in
                ("vix_close","ivar","rvar_cc_fwd_30c","vrp_x_cc_30c","volgap_cc_30c")},
            "primary_forecast_losses":primary["horizons"]["30c"]["case_study_metrics"][str(year)]}
    return {"status":STATUS,"chronology_source":chronology["source"],"specification":"VRP_X = alpha + delta recession + error",
        "regressions":results,"case_studies":cases,"regime_origin_counts":sample.recession_indicator.value_counts().to_dict()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-commit",required=True);parser.add_argument("--parser-path",type=Path,required=True)
    parser.add_argument("--chronology",type=Path,required=True);parser.add_argument("--forecasts",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True);args=parser.parse_args();sys.path.insert(0,str(args.parser_path.resolve()))
    ident=identity(args.code_commit,["src/vrp/regime_analysis.py","src/vrp/provisional_analysis.py","src/vrp/inference.py","src/vrp/regimes.py"])
    frozen=json.loads(args.chronology.read_bytes())
    rebuilt=freeze_chronology(Path("data/raw/2026-10-13T181701Z/nber/source_manifest.json"))
    if frozen!=rebuilt:raise ValueError("Frozen NBER derivation replay mismatch")
    targets,_,_=inputs();forecast=json.loads(args.forecasts.read_bytes())
    if forecast["freeze_sha256"]!=FREEZE_SHA:raise ValueError("H3 freeze mismatch")
    result=analyze(targets,frozen,forecast)
    result.update({"implementation":ident,"freeze_sha256":FREEZE_SHA,"target_manifest_sha256":EMPIRICAL_SHA,
        "chronology_manifest_sha256":hashlib.sha256(args.chronology.read_bytes()).hexdigest(),
        "h3_h4_sha256":hashlib.sha256(args.forecasts.read_bytes()).hexdigest()})
    print("H5",persist(args.output,result),flush=True)


if __name__=="__main__":main()
