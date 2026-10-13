"""Production acquisition and validation for official daily Cboe VIX history.

This module freezes the predictor-side VIX history without computing VRP
results. The full provider response remains an immutable local acquisition
artifact; a deterministic normalized window is separately persisted and
quality-gated before it can enter the aligned origin panel.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

import pandas as pd

from vrp.calendar import exchange_sessions
from vrp.config import CONVENTIONS
from vrp.data import CBOE_VIX_URL, fetch_bytes, write_immutable


VIX_COLUMNS = ("OPEN", "HIGH", "LOW", "CLOSE")
VIX_METHODOLOGY_BREAK = date.fromisoformat(CONVENTIONS.vix_weekly_methodology_start)


class VixDataValidationError(ValueError):
    """Raised when Cboe VIX data violate the production contract."""


@dataclass(frozen=True)
class VixQualityReport:
    accepted: bool
    expected_session_count: int
    observed_session_count: int
    missing_sessions: tuple[str, ...]
    unexpected_sessions: tuple[str, ...]
    missing_required_values: dict[str, int]
    nonpositive_required_values: dict[str, int]
    ohlc_order_violations: int


@dataclass(frozen=True)
class VixAcquisitionResult:
    retrieved_at_utc: str
    raw_relative_path: str
    normalized_relative_path: str
    manifest_relative_path: str
    raw_sha256: str
    normalized_sha256: str
    row_count: int
    coverage_start: str
    coverage_end: str
    quality: VixQualityReport


def parse_cboe_vix(
    raw: bytes,
    *,
    start_date: date,
    end_exclusive: date,
) -> pd.DataFrame:
    """Parse and freeze the requested Cboe history window deterministically."""

    if start_date >= end_exclusive:
        raise ValueError("start_date must be before end_exclusive")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if reader.fieldnames is None:
            raise VixDataValidationError("Cboe VIX CSV has no header")
        required = {"DATE", *VIX_COLUMNS}
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise VixDataValidationError(f"Cboe VIX schema missing columns: {missing}")
        rows = list(reader)
    except UnicodeError as error:
        raise VixDataValidationError("Cboe VIX CSV is not valid UTF-8") from error
    if not rows:
        raise VixDataValidationError("Cboe VIX source returned no rows")

    parsed: list[dict[str, object]] = []
    for row in rows:
        try:
            day = datetime.strptime(row["DATE"].strip(), "%m/%d/%Y").date()
        except (KeyError, ValueError) as error:
            raise VixDataValidationError("invalid Cboe VIX DATE value") from error
        if not start_date <= day < end_exclusive:
            continue
        item: dict[str, object] = {"Date": day.isoformat()}
        for column in VIX_COLUMNS:
            raw_value = row.get(column, "").strip()
            try:
                item[column] = float(raw_value)
            except ValueError:
                item[column] = math.nan
        parsed.append(item)

    if not parsed:
        raise VixDataValidationError("Cboe VIX source has no rows in frozen window")
    frame = pd.DataFrame(parsed, columns=["Date", *VIX_COLUMNS])
    if frame["Date"].duplicated().any():
        raise VixDataValidationError("Cboe VIX source contains duplicate dates")
    return frame.sort_values("Date", kind="stable").reset_index(drop=True)


def vix_quality_report(
    frame: pd.DataFrame,
    *,
    start_date: date,
    end_exclusive: date,
) -> VixQualityReport:
    """Assess exact XNYS coverage and finite/positive OHLC validity."""

    required = {"Date", *VIX_COLUMNS}
    missing_columns = sorted(required - set(frame.columns))
    if missing_columns:
        raise VixDataValidationError(
            f"VIX production frame missing columns: {missing_columns}"
        )
    dates = [
        timestamp.date()
        for timestamp in pd.to_datetime(frame["Date"], errors="raise")
    ]
    if len(dates) != len(set(dates)):
        raise VixDataValidationError("VIX production frame contains duplicate dates")

    expected = set(exchange_sessions(start_date, end_exclusive - timedelta(days=1)))
    observed = set(dates)
    missing_sessions = tuple(day.isoformat() for day in sorted(expected - observed))
    unexpected_sessions = tuple(day.isoformat() for day in sorted(observed - expected))

    numeric: dict[str, pd.Series] = {}
    missing_values: dict[str, int] = {}
    nonpositive: dict[str, int] = {}
    for column in VIX_COLUMNS:
        series = pd.to_numeric(frame[column], errors="coerce")
        numeric[column] = series
        finite = series.map(
            lambda value: math.isfinite(float(value)) if pd.notna(value) else False
        )
        missing_values[column] = int((~finite).sum())
        nonpositive[column] = int((finite & (series <= 0)).sum())

    valid = pd.DataFrame(numeric).dropna()
    order_bad = (
        (valid["HIGH"] < valid[["OPEN", "CLOSE"]].max(axis=1))
        | (valid["LOW"] > valid[["OPEN", "CLOSE"]].min(axis=1))
        | (valid["HIGH"] < valid["LOW"])
    )
    violations = int(order_bad.sum())
    accepted = (
        not missing_sessions
        and not unexpected_sessions
        and all(value == 0 for value in missing_values.values())
        and all(value == 0 for value in nonpositive.values())
        and violations == 0
    )
    return VixQualityReport(
        accepted=accepted,
        expected_session_count=len(expected),
        observed_session_count=len(observed),
        missing_sessions=missing_sessions,
        unexpected_sessions=unexpected_sessions,
        missing_required_values=missing_values,
        nonpositive_required_values=nonpositive,
        ohlc_order_violations=violations,
    )


def acquire_vix_history(
    raw_root: Path,
    *,
    start_date: date,
    end_exclusive: date,
    retrieved_at: datetime | None = None,
) -> VixAcquisitionResult:
    """Acquire official Cboe history and preserve raw plus normalized snapshots."""

    retrieved = retrieved_at or datetime.now(timezone.utc)
    if retrieved.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    if end_exclusive > retrieved.date():
        raise ValueError(
            "end_exclusive cannot exceed the retrieval date; current-day VIX "
            "must never enter a frozen daily predictor snapshot"
        )

    raw = fetch_bytes(CBOE_VIX_URL)
    normalized = parse_cboe_vix(
        raw,
        start_date=start_date,
        end_exclusive=end_exclusive,
    )
    quality = vix_quality_report(
        normalized,
        start_date=start_date,
        end_exclusive=end_exclusive,
    )
    normalized_bytes = normalized.to_csv(
        index=False,
        lineterminator="\n",
        float_format="%.10g",
    ).encode("utf-8")

    stamp = retrieved.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    raw_relative = Path(stamp) / "cboe" / "VIX_History.csv"
    normalized_relative = Path(stamp) / "cboe" / "vix_frozen_normalized.csv"
    manifest_relative = Path(stamp) / "vix_manifest.json"
    raw_digest = write_immutable(raw_root / raw_relative, raw)
    normalized_digest = write_immutable(
        raw_root / normalized_relative, normalized_bytes
    )

    result = VixAcquisitionResult(
        retrieved_at_utc=retrieved.astimezone(timezone.utc).isoformat(),
        raw_relative_path=raw_relative.as_posix(),
        normalized_relative_path=normalized_relative.as_posix(),
        manifest_relative_path=manifest_relative.as_posix(),
        raw_sha256=raw_digest,
        normalized_sha256=normalized_digest,
        row_count=len(normalized),
        coverage_start=str(normalized["Date"].min()),
        coverage_end=str(normalized["Date"].max()),
        quality=quality,
    )
    manifest = {
        "schema_version": 1,
        "dataset": "Cboe VIX daily history",
        "retrieved_at_utc": result.retrieved_at_utc,
        "source_url": CBOE_VIX_URL,
        "frozen_window": {
            "start_inclusive": start_date.isoformat(),
            "end_exclusive": end_exclusive.isoformat(),
        },
        "raw": {
            "relative_path": result.raw_relative_path,
            "sha256": result.raw_sha256,
            "bytes": len(raw),
        },
        "normalized": {
            "relative_path": result.normalized_relative_path,
            "sha256": result.normalized_sha256,
            "row_count": result.row_count,
            "coverage_start": result.coverage_start,
            "coverage_end": result.coverage_end,
            "columns": ["Date", *VIX_COLUMNS],
        },
        "quality": asdict(quality),
        "methodology": {
            "weekly_inclusive_start": CONVENTIONS.vix_weekly_methodology_start,
            "full_sample_primary": True,
            "post_2003_sensitivity_required": True,
            "post_2014_10_06_sensitivity_required": True,
        },
        "timing_note": (
            "daily CLOSE is treated as an end-of-day predictor; exact historical "
            "same-instant synchronization with the S&P 500 cash close is not assumed"
        ),
        "transport": {
            "verification_override_requested": False,
            "note": "urllib default TLS verification; no verify=False override",
        },
    }
    write_immutable(
        raw_root / manifest_relative,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-exclusive", type=date.fromisoformat, required=True)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = acquire_vix_history(
        args.raw_root,
        start_date=args.start_date,
        end_exclusive=args.end_exclusive,
    )
    print(
        f"VIX: rows={result.row_count}, "
        f"coverage={result.coverage_start}..{result.coverage_end}, "
        f"quality={'accepted' if result.quality.accepted else 'rejected'}"
    )
    print(f"manifest={result.manifest_relative_path}")
    return 0 if result.quality.accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
