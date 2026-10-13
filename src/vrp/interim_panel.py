"""Explicitly authorized interim panel, separate from both historical gates."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

from vrp.archival_vix import (AMENDMENT, AUTHORIZATION, ARCHIVE_SHA, ARCHIVE_URL,
    INSERT_DATE, insert_archival_close, verify_archive, verify_fred_corroboration)
from vrp.calendar import exchange_sessions
from vrp.config import CONVENTIONS
from vrp.data import write_immutable
from vrp.dates import as_date
from vrp.origin_panel import align_origin_panel
from vrp.processed_panel import PanelProvenanceError, _load_spx, _read_manifest, _verified_artifact
from vrp.vix_close_candidate import _render_candidate, _source_vix

CONTRACT = "authorized-interim-vix-close/1.0.0"
REVIEW = "PROVISIONAL / NOT INDEPENDENTLY ACCEPTED"
ORIGINAL_MISSING = ["1991-03-01", "1997-01-31", "1997-11-26", INSERT_DATE]
ARCHIVE = {"relative_path": "2026-10-13T142430Z/cboe/vixarchive.xls",
    "sha256": ARCHIVE_SHA, "source_url": ARCHIVE_URL}
FRED = {"relative_path": "2026-10-13T150732Z/fred/vixcls_1999-12-31.csv",
    "sha256": "cf5fd219cd8cd428b287c6f260baaefd746e11ca8ef1eb19ffc9741204d58bcb",
    "source_url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=1999-12-30&coed=2000-01-03"}
SOURCE_MANIFEST_HASHES = {
    "spx": "29bb559550a8470b1b8c034cf752b8bd3919b2585069ed27d252ddc2bb6873a5",
    "vix": "68c11d8fe5a9f454761a898b1bd6bdee499c7a55b30ce370ec28549fc8805d92"}
CODE_FILES = ("interim_panel.py", "archival_vix.py", "vix_close_candidate.py",
    "processed_panel.py", "origin_panel.py", "calendar.py", "config.py", "dates.py",
    "premium.py", "vix_data.py", "spx_data.py", "data.py", "acquisition_audit.py")


def code_identity(commit: str) -> dict:
    """Bind execution to committed scientific code, ignoring checkout EOLs."""
    if not isinstance(commit, str) or not re.fullmatch("[0-9a-f]{40}", commit):
        raise PanelProvenanceError("Exact implementation commit required")
    root = Path(__file__).resolve().parents[2]
    hashes = {}
    for name in CODE_FILES:
        relative = "src/vrp/" + name
        saved = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=root,
            capture_output=True, check=False)
        current = (root / relative).read_bytes().replace(b"\r\n", b"\n")
        if saved.returncode or saved.stdout.replace(b"\r\n", b"\n") != current:
            raise PanelProvenanceError("Implementation differs from recorded commit: " + relative)
        hashes[relative] = hashlib.sha256(current).hexdigest()
    return {"commit": commit, "source_sha256_lf": hashes}


def render_interim(raw_root: Path, spx_manifest: Path, vix_manifest: Path,
    authorization_path: Path, commit: str):
    try:
        auth_raw = authorization_path.read_bytes()
        auth = json.loads(auth_raw)
    except (OSError, ValueError) as error:
        raise PanelProvenanceError("Missing/invalid authorization") from error
    if auth != AUTHORIZATION:
        raise PanelProvenanceError("Unauthorized or modified methodology metadata")
    identity = code_identity(commit)
    _, _, candidate, _ = _render_candidate(raw_root, spx_manifest, vix_manifest)
    if {k: v["sha256"] for k, v in candidate["source_manifests"].items()} != SOURCE_MANIFEST_HASHES:
        raise PanelProvenanceError("Original frozen source manifest mismatch")
    validation = candidate["validation"]
    if (validation["missing_predictor_origins"] != ORIGINAL_MISSING or
        len(validation["rejected_non_session_dates"]) != 28 or
        validation["source_ohlc_diagnostics"]["row_count"] != 47):
        raise PanelProvenanceError("Original source findings differ from authorized contract")
    root = raw_root.resolve()
    spx_record, _ = _read_manifest(root, spx_manifest, "SPX")
    vix_record, _ = _read_manifest(root, vix_manifest, "VIX")
    spx = _load_spx(root, spx_record)
    evidence = verify_archive(root, ARCHIVE)
    corroboration = verify_fred_corroboration(root, FRED)
    source = _source_vix(root, vix_record)
    combined = insert_archival_close(source, evidence, auth)
    # Retention has already passed original CLOSE/range checks; archive is separately checked.
    eligible = {d.isoformat() for d in exchange_sessions(as_date(CONVENTIONS.sample_start),
        as_date(CONVENTIONS.sample_end))}
    close = combined.loc[combined.Date.isin(eligible)].reset_index(drop=True)
    rows, alignment = align_origin_panel(spx.Date.tolist(), list(zip(close.Date, close.CLOSE)))
    source_map = dict(zip(close.Date, close.vix_source)); spx_map = dict(zip(spx.Date, spx.Close))
    panel = pd.DataFrame([{"origin": r.origin.isoformat(), "spx_close": float(spx_map[r.origin.isoformat()]),
        "vix_close": r.vix_close, "ivol": r.ivol, "ivar": r.ivar,
        "vix_methodology_regime": r.vix_methodology_regime,
        "vix_source": source_map[r.origin.isoformat()]} for r in rows])
    if list(alignment.missing_vix_on_spx) != ORIGINAL_MISSING[:-1] or len(panel) != len(close):
        raise PanelProvenanceError("Unexpected interim row losses")
    coverage = {}
    days = set(panel.origin)
    for label, lower in {"full_sample": CONVENTIONS.sample_start, "oos_from_2007": "2007-01-01",
        "post_2003": "2004-01-01", "post_2014_10_06": "2014-10-06"}.items():
        expected = {d.isoformat() for d in exchange_sessions(as_date(lower), as_date(CONVENTIONS.sample_end))}
        coverage[label] = {"start_inclusive": lower, "expected": len(expected),
            "available": len(expected & days), "missing": sorted(expected - days)}
    seed = json.dumps({"contract": CONTRACT, "identity": identity, "sources": candidate["source_manifests"],
        "authorization_sha256": hashlib.sha256(auth_raw).hexdigest()}, sort_keys=True).encode()
    base = Path("interim") / hashlib.sha256(seed).hexdigest()[:16]
    frames = {"interim_vix_close.csv": close, "interim_origin_panel.csv": panel,
        "canonical_spx_ohlc.csv": spx}
    content = {name: frame.to_csv(index=False, lineterminator="\n", float_format="%.17g").encode()
        for name, frame in frames.items()}
    report = {"schema_version": 1, "dataset": "Authorized interim CLOSE predictor freeze",
        "contract_version": CONTRACT, "protocol_version": CONVENTIONS.protocol_version,
        "data_amendment": AMENDMENT, "authorization": auth,
        "authorization_sha256": hashlib.sha256(auth_raw).hexdigest(), "implementation": identity,
        "review_status": REVIEW, "technical_gate": "PASSED_SOURCE_AND_ELIGIBILITY_REPLAY",
        "confirmatory_execution_allowed": False, "provisional_target_execution_allowed": True,
        "calendar": candidate["calendar"], "source_manifests": candidate["source_manifests"],
        "source_artifacts": {**candidate["source_artifacts"], "archive": ARCHIVE, "fred_vix": FRED},
        "original_vix_acquisition_accepted": False, "original_strict_quality": vix_record["quality"],
        "original_close_validation": validation, "archival_insertions": [{**evidence,
            "code_commit": commit, "authorization_status": auth["status"]}],
        "fred_corroboration": corroboration, "row_losses": asdict(alignment), "coverage": coverage,
        "spx_preservation": {"original_rows": len(spx), "retained_rows": len(spx), "removed_rows": 0,
            "post_cutoff_support_rows": int((spx.Date > CONVENTIONS.sample_end).sum()),
            "canonical_source_replaced": False},
        "outputs": {name: {"relative_path": (base / name).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "rows": len(frames[name])}
            for name, raw in content.items()}}
    return base, content, report, panel, spx


def build_interim(raw_root: Path, processed_root: Path, spx_manifest: Path, vix_manifest: Path,
    authorization_path: Path, commit: str) -> Path:
    base, content, report, _, _ = render_interim(raw_root, spx_manifest, vix_manifest, authorization_path, commit)
    for name, raw in content.items():
        write_immutable(processed_root / base / name, raw)
    path = processed_root / base / "interim_manifest.json"
    write_immutable(path, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    return path


def verify_interim(raw_root: Path, processed_root: Path, manifest: Path, authorization_path: Path):
    record, _ = _read_manifest(processed_root.resolve(), manifest, "Interim")
    try:
        sources = record["source_manifests"]
        _, content, expected, panel, spx = render_interim(raw_root, Path(sources["spx"]["relative_path"]),
            Path(sources["vix"]["relative_path"]), authorization_path, record["implementation"]["commit"])
    except (KeyError, TypeError) as error:
        raise PanelProvenanceError("Interim provenance missing") from error
    if json.loads(json.dumps(expected)) != record:
        raise PanelProvenanceError("Interim manifest replay mismatch; approval cannot be self-granted")
    for name, raw in content.items():
        if _verified_artifact(processed_root.resolve(), record["outputs"][name], name) != raw:
            raise PanelProvenanceError("Interim content replay mismatch")
    return panel, spx, record


def require_independent_acceptance(record: dict):
    raise PanelProvenanceError("Independent freeze acceptance pending; interim outputs are provisional")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--spx-manifest", type=Path, required=True)
    parser.add_argument("--vix-manifest", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--parser-path", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.parser_path.resolve()))
    path = build_interim(args.raw_root, args.processed_root, args.spx_manifest, args.vix_manifest,
        args.authorization, args.code_commit)
    panel, _, _ = verify_interim(args.raw_root, args.processed_root, path.resolve(), args.authorization)
    print(f"{REVIEW} origins={len(panel)} manifest={path}")


if __name__ == "__main__":
    main()
