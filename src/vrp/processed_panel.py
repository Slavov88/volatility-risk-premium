"""Build only provenance-verified SPX/VIX predictor-origin panels.

Raw source hashes, manifests, complete XNYS coverage, and production quality
are independently checked before promotion. No returns, RVAR or VRP results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from vrp.config import CONVENTIONS
from vrp.data import write_immutable
from vrp.dates import as_date
from vrp.origin_panel import align_origin_panel
from vrp.spx_data import YAHOO_SPX_HISTORY_URL, production_quality_report
from vrp.vix_data import parse_cboe_vix, vix_quality_report
from vrp.data import CBOE_VIX_URL

CALENDAR_VERSION = "4.13.2"


class PanelProvenanceError(ValueError):
    """One or more production provenance/quality invariants failed."""


@dataclass(frozen=True)
class VerifiedPanelResult:
    panel_relative_path: str
    manifest_relative_path: str
    panel_sha256: str
    origin_count: int
    first_origin: str
    last_origin: str
    row_losses: dict[str, Any]


def _safe_path(root: Path, path: Path | str, *, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute() and ".." in candidate.parts:
        raise PanelProvenanceError(f"{label}: path traversal is prohibited")
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise PanelProvenanceError(f"{label}: path escapes acquisition root")
    return resolved


def _read_manifest(root: Path, path: Path, label: str) -> tuple[dict[str, Any], str]:
    manifest_path = _safe_path(root, path, label=label)
    try:
        raw = manifest_path.read_bytes()
        record = json.loads(raw)
    except (OSError, UnicodeError, ValueError) as error:
        raise PanelProvenanceError(f"{label}: invalid or missing manifest") from error
    if not isinstance(record, dict):
        raise PanelProvenanceError(f"{label}: manifest must be a JSON object")
    return record, hashlib.sha256(raw).hexdigest()


def _verified_artifact(root: Path, info: Any, label: str) -> bytes:
    if not isinstance(info, dict):
        raise PanelProvenanceError(f"{label}: missing artifact metadata")
    path_str, expected = info.get("relative_path"), info.get("sha256")
    if not isinstance(path_str, str) or not path_str or Path(path_str).is_absolute():
        raise PanelProvenanceError(f"{label}: invalid relative artifact path")
    if not isinstance(expected, str) or len(expected) != 64:
        raise PanelProvenanceError(f"{label}: invalid SHA-256")
    path = _safe_path(root, path_str, label=label)
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise PanelProvenanceError(f"{label}: source artifact inaccessible") from error
    if hashlib.sha256(raw).hexdigest() != expected:
        raise PanelProvenanceError(f"{label}: SHA-256 mismatch")
    return raw


def _window(record: dict[str, Any], label: str, end: str) -> tuple[date, date]:
    frozen = record.get("frozen_window")
    if not isinstance(frozen, dict) or (
        frozen.get("start_inclusive") != CONVENTIONS.sample_start
        or frozen.get("end_exclusive") != end
    ):
        raise PanelProvenanceError(f"{label}: acquisition window differs from locked protocol")
    return as_date(CONVENTIONS.sample_start), as_date(end)


def _accepted(actual: Any, recorded: Any, label: str) -> None:
    if not isinstance(recorded, dict) or recorded.get("accepted") is not True:
        raise PanelProvenanceError(f"{label}: acquisition not accepted")
    if not actual.accepted or recorded != json.loads(json.dumps(asdict(actual))):
        raise PanelProvenanceError(f"{label}: independent quality check disagrees with manifest")


def _frame(raw: bytes, label: str) -> pd.DataFrame:
    try:
        frame = pd.read_csv(BytesIO(raw), dtype={"Date": "string"})
        if frame.empty:
            raise ValueError("empty CSV")
        for value in frame["Date"]:
            as_date(value)
    except (KeyError, ValueError, TypeError) as error:
        raise PanelProvenanceError(f"{label}: invalid normalized acquisition CSV") from error
    return frame


def _load_spx(root: Path, record: dict[str, Any]) -> pd.DataFrame:
    if record.get("schema_version") != 4 or record.get("dataset") != "S&P 500 price index daily OHLC":
        raise PanelProvenanceError("SPX: invalid schema/source")
    start, end = _window(record, "SPX", CONVENTIONS.spx_target_support_end_exclusive)
    if record.get("transport", {}).get("verification_override_requested") is not False:
        raise PanelProvenanceError("SPX: TLS override not ruled out")
    calendar = record.get("exchange_calendar", {})
    if calendar.get("name") != "XNYS" or calendar.get("library_version") != CALENDAR_VERSION:
        raise PanelProvenanceError("SPX: calendar provenance mismatch")
    yahoo = record.get("yahoo", {})
    if (yahoo.get("symbol") != "^GSPC"
        or yahoo.get("provider_response_persisted") is not False
        or yahoo.get("source_page") != YAHOO_SPX_HISTORY_URL):
        raise PanelProvenanceError("SPX: not a canonical Yahoo index snapshot")
    frame = _frame(_verified_artifact(root, yahoo, "SPX"), "SPX")
    quality = production_quality_report(frame, start_date=start, end_exclusive=end)
    _accepted(quality, record.get("production_quality"), "SPX")
    dates = [as_date(d) for d in frame["Date"]]
    if calendar.get("expected_session_count") != quality.expected_session_count:
        raise PanelProvenanceError("SPX: expected-session provenance mismatch")
    if yahoo.get("row_count") != len(frame) or yahoo.get("coverage_start") != min(dates).isoformat() or yahoo.get("coverage_end") != max(dates).isoformat():
        raise PanelProvenanceError("SPX: snapshot coverage/rows mismatch")
    return frame


def _load_vix(root: Path, record: dict[str, Any]) -> pd.DataFrame:
    if (record.get("schema_version") != 1
        or record.get("dataset") != "Cboe VIX daily history"
        or record.get("source_url") != CBOE_VIX_URL):
        raise PanelProvenanceError("VIX: invalid schema/source")
    expected_end = (as_date(CONVENTIONS.sample_end) + timedelta(days=1)).isoformat()
    start, end = _window(record, "VIX", expected_end)
    if record.get("transport", {}).get("verification_override_requested") is not False:
        raise PanelProvenanceError("VIX: TLS override not ruled out")
    raw = _verified_artifact(root, record.get("raw"), "VIX raw")
    normalized_info = record.get("normalized", {})
    normalized = _verified_artifact(root, normalized_info, "VIX normalized")
    replay = parse_cboe_vix(raw, start_date=start, end_exclusive=end)
    if replay.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8") != normalized:
        raise PanelProvenanceError("VIX: normalized data does not reproduce from raw provider bytes")
    frame = _frame(normalized, "VIX")
    quality = vix_quality_report(frame, start_date=start, end_exclusive=end)
    _accepted(quality, record.get("quality"), "VIX")
    dates = [as_date(d) for d in frame["Date"]]
    if normalized_info.get("row_count") != len(frame) or normalized_info.get("coverage_start") != min(dates).isoformat() or normalized_info.get("coverage_end") != max(dates).isoformat():
        raise PanelProvenanceError("VIX: snapshot coverage/rows mismatch")
    if record.get("methodology", {}).get("weekly_inclusive_start") != CONVENTIONS.vix_weekly_methodology_start:
        raise PanelProvenanceError("VIX: methodology transition metadata mismatch")
    return frame


def build_verified_origin_panel(
    raw_root: Path, spx_manifest: Path, vix_manifest: Path, processed_root: Path
) -> VerifiedPanelResult:
    """Accept only locked, independently validated acquisition snapshots."""

    root = raw_root.resolve()
    if version("exchange-calendars") != CALENDAR_VERSION:
        raise PanelProvenanceError("Installed exchange calendar differs from locked version")
    spx_record, spx_manifest_sha = _read_manifest(root, spx_manifest, "SPX")
    vix_record, vix_manifest_sha = _read_manifest(root, vix_manifest, "VIX")
    spx = _load_spx(root, spx_record)
    vix = _load_vix(root, vix_record)
    rows, losses = align_origin_panel(
        spx["Date"].tolist(),
        list(zip(vix["Date"].tolist(), vix["CLOSE"].tolist())),
    )
    if not rows:
        raise PanelProvenanceError("SPX/VIX: no common forecast origins")
    closes = dict(zip(spx["Date"].tolist(), spx["Close"].tolist()))
    panel = pd.DataFrame([
        {
            "origin": r.origin.isoformat(),
            "spx_close": float(closes[r.origin.isoformat()]),
            "vix_close": r.vix_close,
            "ivol": r.ivol,
            "ivar": r.ivar,
            "vix_methodology_regime": r.vix_methodology_regime,
        }
        for r in rows
    ])
    raw_panel = panel.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")
    label = hashlib.sha256((spx_manifest_sha + vix_manifest_sha).encode("ascii")).hexdigest()[:16]
    relative_csv = Path(label) / "verified_origin_panel.csv"
    relative_manifest = Path(label) / "origin_panel_manifest.json"
    output_sha = write_immutable(processed_root / relative_csv, raw_panel)
    row_losses = asdict(losses)
    report = {
        "schema_version": 1,
        "purpose": "Validated SPX/VIX forecast origins only; no empirical VRP results",
        "protocol_version": CONVENTIONS.protocol_version,
        "forecast_origin_cutoff": CONVENTIONS.sample_end,
        "spx_source_manifest_sha256": spx_manifest_sha,
        "vix_source_manifest_sha256": vix_manifest_sha,
        "spx_source_data_sha256": spx_record["yahoo"]["sha256"],
        "vix_raw_sha256": vix_record["raw"]["sha256"],
        "vix_normalized_sha256": vix_record["normalized"]["sha256"],
        "calendar": {"name": "XNYS", "version": CALENDAR_VERSION},
        "row_losses": row_losses,
        "panel": {
            "relative_path": relative_csv.as_posix(),
            "sha256": output_sha,
            "row_count": len(rows),
            "first_origin": rows[0].origin.isoformat(),
            "last_origin": rows[-1].origin.isoformat(),
            "columns": list(panel.columns),
        },
    }
    write_immutable(
        processed_root / relative_manifest,
        (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return VerifiedPanelResult(
        relative_csv.as_posix(),
        relative_manifest.as_posix(),
        output_sha,
        len(rows),
        rows[0].origin.isoformat(),
        rows[-1].origin.isoformat(),
        row_losses,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--spx-manifest", type=Path, required=True)
    parser.add_argument("--vix-manifest", type=Path, required=True)
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_verified_origin_panel(
        args.raw_root, args.spx_manifest, args.vix_manifest, args.processed_root
    )
    print(f"validated origins={result.origin_count} {result.first_origin}..{result.last_origin}")
    print(f"panel={result.panel_relative_path} sha256={result.panel_sha256}")
    print(f"manifest={result.manifest_relative_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
