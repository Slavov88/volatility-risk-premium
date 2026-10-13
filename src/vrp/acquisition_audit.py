"""Data-free diagnostics for immutable production acquisitions, including rejection.

This audit never repairs data or relaxes promotion gates. It recomputes source
quality and describes defects by date/category without redistributing prices.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import timedelta
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
from typing import Sequence

from vrp.config import CONVENTIONS
from vrp.data import write_immutable
from vrp.dates import as_date
from vrp.processed_panel import (
    CALENDAR_VERSION, PanelProvenanceError, _load_spx,
    _read_manifest, _verified_artifact, _window,
)
from vrp.spx_data import production_quality_report
from vrp.vix_data import parse_cboe_vix, vix_quality_report


def sanitized_spx_manifest(record: dict) -> dict:
    """Copy provenance while removing restricted provider close observations."""
    result = json.loads(json.dumps(record))
    validation = result.get("fred_close_validation", {}).get("validation")
    if validation is not None:
        validation["discrepancy_sample"] = [
            {"date": row["date"], "absolute_difference": row["absolute_difference"]}
            for row in validation["discrepancy_sample"]
        ]
    return result


def ohlc_defects(frame, columns: tuple[str, str, str, str]) -> dict:
    """Return date-only diagnostics; categories can overlap within a row."""
    open_col, high, low, close = columns
    categories = {
        "high_below_open": frame[high] < frame[open_col],
        "high_below_close": frame[high] < frame[close],
        "low_above_open": frame[low] > frame[open_col],
        "low_above_close": frame[low] > frame[close],
        "high_below_low": frame[high] < frame[low],
    }
    dates = sorted({str(day) for mask in categories.values() for day in frame.loc[mask, "Date"]})
    return {
        "row_count": len(dates), "dates": dates,
        "categories": {name: frame.loc[mask, "Date"].tolist() for name, mask in categories.items()},
    }


def audit_acquisitions(raw_root: Path, spx_manifest: Path, vix_manifest: Path) -> dict:
    root = raw_root.resolve()
    if version("exchange-calendars") != CALENDAR_VERSION:
        raise PanelProvenanceError("Installed exchange calendar differs from locked version")
    spx_record, spx_sha = _read_manifest(root, spx_manifest, "SPX")
    vix_record, vix_sha = _read_manifest(root, vix_manifest, "VIX")
    # SPX is gate-accepted; this is the exact verified-panel source loader.
    spx = _load_spx(root, spx_record)
    expected_end = (as_date(CONVENTIONS.sample_end) + timedelta(days=1)).isoformat()
    start, end = _window(vix_record, "VIX", expected_end)
    from vrp.data import CBOE_VIX_URL
    if vix_record.get("source_url") != CBOE_VIX_URL or vix_record.get("schema_version") != 1:
        raise PanelProvenanceError("VIX: invalid schema/source")
    if vix_record.get("transport", {}).get("verification_override_requested") is not False:
        raise PanelProvenanceError("VIX: TLS override not ruled out")
    raw = _verified_artifact(root, vix_record.get("raw"), "VIX raw")
    normalized = _verified_artifact(root, vix_record.get("normalized"), "VIX normalized")
    vix = parse_cboe_vix(raw, start_date=start, end_exclusive=end)
    if vix.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode() != normalized:
        raise PanelProvenanceError("VIX: normalization replay mismatch")
    quality = asdict(vix_quality_report(vix, start_date=start, end_exclusive=end))
    quality = json.loads(json.dumps(quality))
    if quality != vix_record.get("quality"):
        raise PanelProvenanceError("VIX: recorded quality differs from audit")
    info = vix_record["normalized"]
    if (info["row_count"] != len(vix) or info["coverage_start"] != vix.Date.min()
            or info["coverage_end"] != vix.Date.max()):
        raise PanelProvenanceError("VIX: coverage provenance mismatch")
    fred = spx_record.get("fred_close_validation", {})
    fred_summary = {"status": fred.get("status", "not_requested")}
    if fred.get("status") == "available":
        from vrp.spx_data import parse_fred_sp500, validate_fred_closes
        fred_raw = _verified_artifact(root, fred, "FRED validation")
        fred_frame, metadata = parse_fred_sp500(fred_raw)
        validation = asdict(validate_fred_closes(
            spx, fred_frame, fred["validation"]["fred_source_url"], metadata,
        ))
        # Comparison uses the locked 2dp differences; normalized Yahoo storage
        # can round the unrounded close shown in an acquisition discrepancy row.
        validation = sanitized_spx_manifest({"fred_close_validation": {"validation": validation}})["fred_close_validation"]["validation"]
        recorded = sanitized_spx_manifest(spx_record)["fred_close_validation"]["validation"]
        if validation != recorded:
            raise PanelProvenanceError("FRED: recorded validation differs from audit")
        fred_summary.update(sha256=fred["sha256"], validation=validation)
    spx_quality = asdict(production_quality_report(
        spx, start_date=as_date(CONVENTIONS.sample_start),
        end_exclusive=as_date(CONVENTIONS.spx_target_support_end_exclusive),
    ))
    cutoff = CONVENTIONS.sample_end
    common = sorted(set(spx.loc[spx.Date <= cutoff, "Date"]) & set(vix.Date))
    return {
        "schema_version": 1, "protocol_version": CONVENTIONS.protocol_version,
        "status": "QUALITY_PASSED_PENDING_COAUTHOR_REVIEW" if quality["accepted"] else "BLOCKED_VIX_QUALITY",
        "scientific_approval": "NOT_REVIEWED",
        "software": {"python": sys.version.split()[0], **{
            p: version(p) for p in ("exchange-calendars", "yfinance", "pandas", "numpy", "curl-cffi")}},
        "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_manifest_sha256": {"spx": spx_sha, "vix": vix_sha},
        "source_data_sha256": {"spx": spx_record["yahoo"]["sha256"],
            "vix_raw": vix_record["raw"]["sha256"], "vix_normalized": info["sha256"]},
        "frozen_windows": {"spx": spx_record["frozen_window"], "vix": vix_record["frozen_window"]},
        "coverage": {"spx": {k: spx_record["yahoo"][k] for k in ("row_count", "coverage_start", "coverage_end")},
            "vix": {k: info[k] for k in ("row_count", "coverage_start", "coverage_end")}},
        "spx_quality": spx_quality, "vix_quality": quality,
        "vix_ohlc_defects": ohlc_defects(vix, ("OPEN", "HIGH", "LOW", "CLOSE")),
        "fred_validation": fred_summary,
        "alignment_diagnostic_only": {"expected_origins": spx_quality["observed_session_count"] - int((spx.Date > cutoff).sum()),
            "common_dates": len(common), "spx_support_rows_after_cutoff": int((spx.Date > cutoff).sum()),
            "missing_vix_on_spx": sorted(set(spx.loc[spx.Date <= cutoff, "Date"]) - set(vix.Date)),
            "vix_without_spx": sorted(set(vix.Date) - set(spx.Date)),
            "panel_constructed": False},
        "limitations": ["Audit does not repair, drop, fill or approve observations.",
            "Date intersection is diagnostic only; failed quality blocks panel and target construction.",
            "Discrepancy magnitudes are metadata; provider price rows remain local."],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--spx-manifest", type=Path, required=True)
    parser.add_argument("--vix-manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    report = audit_acquisitions(args.raw_root, args.spx_manifest, args.vix_manifest)
    digest = write_immutable(args.report, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    print(f"status={report['status']} report={args.report} sha256={digest}")
    return 0 if report["vix_quality"]["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
