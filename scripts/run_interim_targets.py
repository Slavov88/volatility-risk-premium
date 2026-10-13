"""Replay the authorized freeze, execute six targets and write immutable audit."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys

from vrp.close_sensitivity import DISCREPANCY_DATES, evaluate_alternate_closes
from vrp.data import write_immutable
from vrp.empirical_targets import TARGET_VERSION, construct_targets, audit_targets, describe_targets
from vrp.interim_panel import REVIEW, code_identity, verify_interim
from vrp.processed_panel import PanelProvenanceError, _read_manifest, _verified_artifact
from vrp.spx_data import parse_fred_sp500


def run(raw_root, processed_root, freeze_manifest, authorization, commit):
    identity = code_identity(commit)
    root = Path(__file__).resolve().parents[1]
    files = ["scripts/run_interim_targets.py"] + ["src/vrp/"+p+".py" for p in
        ("empirical_targets", "close_sensitivity", "returns", "targets", "range_estimators",
         "summary", "spx_discrepancy_impact")]
    hashes = {}
    for relative in files:
        saved = subprocess.run(["git", "show", f"{commit}:{relative}"],cwd=root,capture_output=True)
        current = (root / relative).read_bytes().replace(b"\r\n",b"\n")
        if saved.returncode or saved.stdout.replace(b"\r\n",b"\n") != current:
            raise PanelProvenanceError("Target implementation differs from commit: "+relative)
        hashes[relative] = hashlib.sha256(current).hexdigest()
    panel, spx, freeze = verify_interim(raw_root, processed_root, freeze_manifest, authorization)
    daily, targets = construct_targets(spx, panel)
    audit = audit_targets(spx, panel, daily, targets)
    descriptions = describe_targets(targets)
    source, _ = _read_manifest(raw_root.resolve(), Path(freeze["source_manifests"]["spx"]["relative_path"]), "SPX")
    fred = source["fred_close_validation"]
    fred_frame, _ = parse_fred_sp500(_verified_artifact(raw_root.resolve(), fred, "FRED SP500 sensitivity"))
    if fred_frame.Date.duplicated().any():
        raise PanelProvenanceError("Duplicate FRED sensitivity dates")
    prices = dict(zip(fred_frame.Date, fred_frame.FRED_SP500))
    replacements = {d: float(prices[d]) for d in DISCREPANCY_DATES}
    sensitivity = evaluate_alternate_closes(spx, targets, replacements)
    sensitivity["source_sha256"] = fred["sha256"]
    sensitivity["source_url"] = fred["validation"]["fred_source_url"]
    freeze_sha = hashlib.sha256(freeze_manifest.read_bytes()).hexdigest()
    seed = json.dumps({"freeze": freeze_sha, "target_commit": commit, "source_hashes": hashes},sort_keys=True).encode()
    base = freeze_manifest.parent.relative_to(processed_root) / "targets" / hashlib.sha256(seed).hexdigest()[:16]
    content = {"canonical_daily.csv": daily.to_csv(index=False,lineterminator="\n",float_format="%.17g").encode(),
        "six_forward_targets.csv": targets.to_csv(index=False,lineterminator="\n",float_format="%.17g").encode()}
    for name, obj in {"target_audit.json": audit, "descriptive_statistics.json": descriptions,
        "alternate_close_sensitivity.json": sensitivity}.items():
        content[name] = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()
    report = {"schema_version": 1, "dataset": "Provisional six-target empirical execution",
        "protocol_version": freeze["protocol_version"], "data_amendment": freeze["data_amendment"],
        "review_status": REVIEW, "confirmatory_execution_allowed": False,
        "target_version": TARGET_VERSION, "freeze_manifest_sha256": freeze_sha,
        "freeze_manifest_relative_path": freeze_manifest.relative_to(processed_root).as_posix(),
        "freeze_implementation_commit": freeze["implementation"]["commit"],
        "target_implementation": {"commit": commit,"source_sha256_lf": hashes},
        "parameters": {"30c_annualization": "365/30", "21t_annualization": "252/21",
            "vix_scale": "CLOSE/100", "sign": "implied_minus_realized", "imputation": False,
            "post_2003_start": "2004-01-01", "seed": 42},
        "software": {"python": sys.version.split()[0], **{p:version(p) for p in
            ("pandas", "numpy", "exchange-calendars")}, "archive_parser": "xlrd==2.0.2 isolated"},
        "environment_lock_sha256": hashlib.sha256((root / "requirements-dev.lock").read_bytes()).hexdigest(),
        "audit": audit, "outputs": {name: {"relative_path": (base/name).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} for name,raw in content.items()}}
    for name,raw in content.items(): write_immutable(processed_root/base/name,raw)
    path = processed_root/base/"empirical_manifest.json"
    write_immutable(path,(json.dumps(report,indent=2,sort_keys=True)+"\n").encode())
    print(f"{REVIEW}; targets={len(targets)}; audit={audit['status']}; manifest={path}")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--freeze-manifest", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--parser-path", type=Path, required=True)
    args = parser.parse_args(); sys.path.insert(0,str(args.parser_path.resolve()))
    run(args.raw_root,args.processed_root,args.freeze_manifest,args.authorization,args.code_commit)
