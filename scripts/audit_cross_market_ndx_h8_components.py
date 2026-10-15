"""Export and hash-check daily H8 QQQ P&L components for the 5 bp ledgers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pandas as pd

from vrp.cross_market_attribution import decompose_ledger

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/cross_market/v1"
H8_OUT=OUT/"h8_cash_yield_v1"
RESULT=H8_OUT/"ndx_qqq_h8_v1.json"
MANIFEST=ROOT/"data/manifests/cross_market_sources_v1.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False,float_format="%.17g",lineterminator="\n").encode()


def run() -> dict:
    result=json.loads(RESULT.read_bytes())
    manifest=json.loads(MANIFEST.read_bytes())
    source=next(x for x in manifest["sources"] if x["series"]=="QQQ")
    price_path=ROOT/source["raw_path"]
    if sha(price_path.read_bytes())!=source["raw_sha256"]:
        raise ValueError("QQQ source hash mismatch")
    prices=pd.read_csv(price_path,dtype={"Date":str},float_precision="round_trip")
    prices=prices.rename(columns={"Open":"Open","Close":"Close"})
    products={}
    maximum=0.0
    for scenario in result["scenarios"]:
        for strategy in ("buyhold","trailing","vix","garch","combined"):
            path=H8_OUT/f"ndx_qqq_h8_{scenario}_{strategy}_5bps.csv"
            key=f"{scenario}_{strategy}_5bps.csv"
            expected=result["ledger_sha256"].get(key)
            if expected and sha(path.read_bytes())!=expected:
                raise ValueError(f"Ledger hash mismatch: {path.name}")
            ledger=pd.read_csv(path,dtype={"Date":str},float_precision="round_trip")
            components=decompose_ledger(ledger,prices)
            maximum=max(maximum,float(components.return_residual.abs().max()))
            target=H8_OUT/f"ndx_qqq_h8_{scenario}_{strategy}_5bps_components.csv"
            raw=csv_bytes(components)
            if target.exists() and target.read_bytes()!=raw:
                raise ValueError(f"Immutable component output differs: {target.name}")
            if not target.exists():target.write_bytes(raw)
            products[target.name]={"sha256":sha(raw),"bytes":len(raw),"rows":len(components),"source_ledger_sha256":sha(path.read_bytes())}
    commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    output={"status":"AUDITED DAILY ATTRIBUTION — PROVISIONAL","code_commit":commit,
        "source_manifest_sha256":sha(MANIFEST.read_bytes()),"qqq_raw_sha256":source["raw_sha256"],
        "h8_result_sha256":sha(RESULT.read_bytes()),"primary_cost_bps":5,
        "scenario_strategy_ledgers":len(products),"max_absolute_daily_return_residual":maximum,
        "identity":"previous-share overnight P&L + old-share dividend cash + post-trade intraday P&L + prior-cash interest - transaction fee, divided by prior NAV equals observed portfolio return.",
        "component_outputs":products}
    path=ROOT/"data/manifests/h8_ledger_component_attribution_v1.json"
    raw=(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    if path.exists() and path.read_bytes()!=raw:raise ValueError("Immutable component manifest differs")
    if not path.exists():path.write_bytes(raw)
    print(sha(raw),"rows/ledger",3520,"max_abs_residual",maximum,flush=True)
    return output


if __name__=="__main__":run()
