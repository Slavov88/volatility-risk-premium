"""CANDIDATE ONLY: versioned VIX CLOSE eligibility without OHLC gate bypass.

This contract is proposed, not authorized by protocol 1.1.0. It can generate
inspection artifacts only. Original acquisition quality and the strict
verified-panel builder are unchanged. No returns or empirical targets here.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import asdict
from datetime import date, datetime, timedelta
import hashlib
from importlib.metadata import version
import json
from io import StringIO
import math
from pathlib import Path
from typing import Sequence

import pandas as pd

from vrp.acquisition_audit import ohlc_defects
from vrp.calendar import exchange_sessions
from vrp.config import CONVENTIONS
from vrp.data import CBOE_VIX_URL, write_immutable
from vrp.dates import as_date
from vrp.origin_panel import align_origin_panel
from vrp.processed_panel import (
    CALENDAR_VERSION, PanelProvenanceError, _load_spx, _read_manifest,
    _verified_artifact, _window,
)
from vrp.vix_data import parse_cboe_vix, vix_quality_report

CONTRACT_VERSION = "vix-close-candidate/1.0.0"
APPROVAL_STATUS = "CANDIDATE_UNAPPROVED"


class CloseCandidateError(PanelProvenanceError):
    """CLOSE-specific validation or derived provenance failed."""


class CandidateNotApprovedError(PanelProvenanceError):
    """No confirmatory consumer may use this proposed dataset contract."""


def _by_year(dates: Sequence[str]) -> dict[str, int]:
    return dict(sorted(Counter(day[:4] for day in dates).items()))


def validate_close_history(
    frame: pd.DataFrame, *, start_date: date, end_exclusive: date,
) -> tuple[pd.DataFrame, dict]:
    """Validate retained CLOSE values; explicitly exclude unavailable origins.

    Duplicate dates, including identical duplicate closes, are fatal. Missing
    origins remain missing. Available finite positive HIGH/LOW bounds must be
    internally ordered and contain CLOSE. Unavailable bounds and OPEN defects
    remain diagnostics; OPEN never substitutes for CLOSE.
    """
    if start_date >= end_exclusive:
        raise CloseCandidateError("Invalid CLOSE eligibility window")
    if not {"Date", "CLOSE"}.issubset(frame.columns) or frame.empty:
        raise CloseCandidateError("CLOSE history requires nonempty Date/CLOSE columns")
    if any(not isinstance(value, str) for value in frame["Date"]):
        raise CloseCandidateError("CLOSE observation dates require canonical ISO strings")
    days = [as_date(value).isoformat() for value in frame["Date"]]
    if len(days) != len(set(days)):
        raise CloseCandidateError("Duplicate VIX dates, identical or conflicting, prohibited")
    data = frame.copy()
    data["Date"] = days
    data = data.sort_values("Date", kind="stable").reset_index(drop=True)
    expected = {day.isoformat() for day in exchange_sessions(start_date, end_exclusive - timedelta(days=1))}
    inside = data.Date.between(start_date.isoformat(), (end_exclusive - timedelta(days=1)).isoformat())
    retained = data.loc[data.Date.isin(expected)].copy()
    if retained.empty:
        raise CloseCandidateError("No eligible VIX CLOSE origins")
    closes = pd.to_numeric(retained.CLOSE, errors="coerce")
    bad_close = ~closes.map(lambda v: math.isfinite(float(v)) and float(v) > 0)
    if bad_close.any():
        raise CloseCandidateError("Invalid eligible VIX CLOSE: " + ", ".join(retained.loc[bad_close, "Date"]))
    retained["CLOSE"] = closes
    bounds = {}
    available = {}
    for name in ("HIGH", "LOW"):
        values = pd.to_numeric(retained[name], errors="coerce") if name in retained else pd.Series(math.nan, index=retained.index)
        bounds[name] = values
        available[name] = values.map(lambda v: math.isfinite(float(v)) and float(v) > 0)
    inconsistent = ((available["HIGH"] & (closes > bounds["HIGH"]))
        | (available["LOW"] & (closes < bounds["LOW"]))
        | (available["HIGH"] & available["LOW"] & (bounds["HIGH"] < bounds["LOW"])))
    if inconsistent.any():
        raise CloseCandidateError("CLOSE/range inconsistency: " + ", ".join(retained.loc[inconsistent, "Date"]))
    missing = sorted(expected - set(retained.Date))
    non_sessions = data.loc[inside & ~data.Date.isin(expected), "Date"].tolist()
    outside = data.loc[~inside, "Date"].tolist()
    report = {
        "contract_version": CONTRACT_VERSION, "approval_status": APPROVAL_STATUS,
        "input_rows": len(data), "expected_eligible_origins": len(expected),
        "available_eligible_closes": len(retained), "missing_predictor_origins": missing,
        "rejected_non_session_dates": non_sessions, "outside_origin_window_dates": outside,
        "missing_origins_by_year": _by_year(missing),
        "non_session_exclusions_by_year": _by_year(non_sessions),
        "outside_window_exclusions_by_year": _by_year(outside),
        "missing_oos_origins": [d for d in missing if d >= f"{CONVENTIONS.oos_start_year}-01-01"],
        "retained_close_invalid_count": 0, "retained_close_range_violation_count": 0,
        "unavailable_high_or_low_dates": retained.loc[~(available["HIGH"] & available["LOW"]), "Date"].tolist(),
        "fill_or_stitch_count": 0,
        "retention_rule": "XNYS origins in frozen window with original finite positive CLOSE; missing origins excluded only",
    }
    if {"OPEN", "HIGH", "LOW", "CLOSE"}.issubset(data.columns):
        numeric = data.copy()
        for column in ("OPEN", "HIGH", "LOW", "CLOSE"):
            numeric[column] = pd.to_numeric(numeric[column], errors="coerce")
        report["source_ohlc_diagnostics"] = ohlc_defects(numeric, ("OPEN", "HIGH", "LOW", "CLOSE"))
    return retained[["Date", "CLOSE"]].reset_index(drop=True), report


def _source_vix(root: Path, record: dict) -> pd.DataFrame:
    if (record.get("schema_version") != 1 or record.get("dataset") != "Cboe VIX daily history"
            or record.get("source_url") != CBOE_VIX_URL):
        raise CloseCandidateError("VIX: official acquisition identity mismatch")
    if record.get("transport", {}).get("verification_override_requested") is not False:
        raise CloseCandidateError("VIX: TLS override not ruled out")
    end = (as_date(CONVENTIONS.sample_end) + timedelta(days=1)).isoformat()
    start, stop = _window(record, "VIX", end)
    raw = _verified_artifact(root, record.get("raw"), "VIX raw")
    seen = set()
    for row in csv.DictReader(StringIO(raw.decode("utf-8-sig"))):
        text = row.get("DATE", "")
        try:
            day = datetime.strptime(text, "%m/%d/%Y").date()
        except (ValueError, TypeError) as error:
            raise CloseCandidateError("VIX: malformed original observation date") from error
        if day.strftime("%m/%d/%Y") != text or day in seen:
            raise CloseCandidateError("VIX: ambiguous or duplicate original observation date")
        seen.add(day)
    normalized = _verified_artifact(root, record.get("normalized"), "VIX normalized")
    frame = parse_cboe_vix(raw, start_date=start, end_exclusive=stop)
    if frame.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode() != normalized:
        raise CloseCandidateError("VIX: original normalization replay mismatch")
    quality = json.loads(json.dumps(asdict(vix_quality_report(frame, start_date=start, end_exclusive=stop))))
    if quality != record.get("quality"):
        raise CloseCandidateError("VIX: original strict quality report mismatch")
    info = record["normalized"]
    if (info.get("row_count") != len(frame) or info.get("coverage_start") != frame.Date.min()
            or info.get("coverage_end") != frame.Date.max()):
        raise CloseCandidateError("VIX: original coverage provenance mismatch")
    if record.get("methodology", {}).get("weekly_inclusive_start") != CONVENTIONS.vix_weekly_methodology_start:
        raise CloseCandidateError("VIX: methodology transition mismatch")
    return frame


def _render_candidate(raw_root: Path, spx_manifest: Path, vix_manifest: Path):
    if version("exchange-calendars") != CALENDAR_VERSION:
        raise CloseCandidateError("Installed calendar differs from locked version")
    root = raw_root.resolve()
    spx_record, spx_sha = _read_manifest(root, spx_manifest, "SPX")
    vix_record, vix_sha = _read_manifest(root, vix_manifest, "VIX")
    spx = _load_spx(root, spx_record)
    source_vix = _source_vix(root, vix_record)
    close, validation = validate_close_history(source_vix, start_date=as_date(CONVENTIONS.sample_start),
        end_exclusive=as_date(CONVENTIONS.sample_end) + timedelta(days=1))
    rows, alignment = align_origin_panel(spx.Date.tolist(), list(zip(close.Date, close.CLOSE)))
    if len(rows) != len(close):
        raise CloseCandidateError("SPX and eligible VIX dates disagree")
    close_map = dict(zip(spx.Date, spx.Close))
    panel = pd.DataFrame([{
        "origin": r.origin.isoformat(), "spx_close": float(close_map[r.origin.isoformat()]),
        "vix_close": r.vix_close, "ivol": r.ivol, "ivar": r.ivar,
        "vix_methodology_regime": r.vix_methodology_regime,
    } for r in rows])
    content = {"candidate_vix_close.csv": close.to_csv(index=False, lineterminator="\n", float_format="%.17g").encode(),
        "candidate_origin_panel.csv": panel.to_csv(index=False, lineterminator="\n", float_format="%.17g").encode()}
    implementation_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    label = hashlib.sha256((CONTRACT_VERSION + spx_sha + vix_sha + implementation_sha).encode()).hexdigest()[:16]
    base = Path("candidates") / label
    subsets = {}
    close_dates = set(close.Date)
    # Coverage diagnostics expose the unresolved post-2003 boundary rather
    # than silently inventing a frozen inferential cutoff.
    for name, lower in {"full_sample": CONVENTIONS.sample_start, "oos_from_2007": "2007-01-01",
            "post_2003_calendar_year_proposed": "2004-01-01",
            "from_2003_01_01_boundary_review": "2003-01-01",
            "post_2014_10_06": CONVENTIONS.vix_weekly_methodology_start}.items():
        expected = [d.isoformat() for d in exchange_sessions(max(as_date(lower), as_date(CONVENTIONS.sample_start)), as_date(CONVENTIONS.sample_end))]
        missing = [d for d in expected if d not in close_dates]
        subsets[name] = {"start_inclusive": lower, "expected": len(expected),
            "available": len(expected) - len(missing), "missing": missing}
    report = {
        "schema_version": 1, "dataset": "Candidate SPX / VIX CLOSE predictor origins",
        "protocol_version": CONVENTIONS.protocol_version, "contract_version": CONTRACT_VERSION,
        "approval_status": APPROVAL_STATUS, "confirmatory_execution_allowed": False,
        "purpose": "inspection only; no RVAR, VRP or hypothesis outputs",
        "implementation_sha256": implementation_sha,
        "calendar": {"name": "XNYS", "library_version": CALENDAR_VERSION},
        "source_manifests": {"spx": {"relative_path": str((root / spx_manifest).resolve().relative_to(root)).replace('\\', '/'), "sha256": spx_sha},
            "vix": {"relative_path": str((root / vix_manifest).resolve().relative_to(root)).replace('\\', '/'), "sha256": vix_sha}},
        "source_artifacts": {"spx": spx_record["yahoo"], "vix_raw": vix_record["raw"], "vix_normalized": vix_record["normalized"]},
        "original_vix_acquisition_accepted": vix_record["quality"]["accepted"],
        "original_vix_strict_quality": vix_record["quality"],
        "validation": validation, "row_losses": asdict(alignment), "coverage": subsets,
        "spx_outcome_support": {"preserved_source_rows": len(spx), "removed_rows": 0,
            "post_cutoff_rows": int((spx.Date > CONVENTIONS.sample_end).sum()),
            "policy": "all original SPX observations retained for later outcome construction; no returns computed"},
        "outputs": {name: {"relative_path": (base / name).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "rows": len(close)} for name, raw in content.items()},
    }
    return base, content, report, panel


def build_candidate_close_panel(raw_root: Path, spx_manifest: Path, vix_manifest: Path, processed_root: Path) -> Path:
    """Write immutable inspection artifacts, always explicitly unapproved."""
    base, content, report, _ = _render_candidate(raw_root, spx_manifest, vix_manifest)
    for name, raw in content.items():
        write_immutable(processed_root / base / name, raw)
    path = processed_root / base / "candidate_close_manifest.json"
    write_immutable(path, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    return path


def verify_candidate_close_panel(raw_root: Path, processed_root: Path, manifest: Path) -> pd.DataFrame:
    """Revalidate sources, full provenance and derived bytes for inspection."""
    record, _ = _read_manifest(processed_root.resolve(), manifest, "Candidate")
    if record.get("approval_status") != APPROVAL_STATUS or record.get("confirmatory_execution_allowed") is not False:
        raise CandidateNotApprovedError("Candidate approval cannot be granted by editing metadata")
    if record.get("contract_version") != CONTRACT_VERSION or record.get("schema_version") != 1:
        raise CloseCandidateError("Candidate contract/schema mismatch")
    sources = record.get("source_manifests", {})
    try:
        spx_path = Path(sources["spx"]["relative_path"])
        vix_path = Path(sources["vix"]["relative_path"])
    except (KeyError, TypeError) as error:
        raise CloseCandidateError("Candidate source provenance missing") from error
    _, content, expected, panel = _render_candidate(raw_root, spx_path, vix_path)
    if json.loads(json.dumps(expected)) != record:
        raise CloseCandidateError("Candidate provenance/validation replay mismatch")
    for name, raw in content.items():
        actual = _verified_artifact(processed_root.resolve(), record["outputs"][name], "Derived " + name)
        if actual != raw:
            raise CloseCandidateError("Candidate bytes disagree with source replay")
    return panel


def load_confirmatory_close_panel(raw_root: Path, processed_root: Path, manifest: Path):
    """Explicit approval boundary; no current candidate can cross it."""
    verify_candidate_close_panel(raw_root, processed_root, manifest)
    raise CandidateNotApprovedError("CLOSE candidate methodology requires both authors' authorization; protocol 1.1.0 not amended")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--spx-manifest", type=Path, required=True)
    parser.add_argument("--vix-manifest", type=Path, required=True)
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)
    path = build_candidate_close_panel(args.raw_root, args.spx_manifest, args.vix_manifest, args.processed_root)
    panel = verify_candidate_close_panel(args.raw_root, args.processed_root, path.resolve())
    print(f"CANDIDATE_UNAPPROVED origins={len(panel)} manifest={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
