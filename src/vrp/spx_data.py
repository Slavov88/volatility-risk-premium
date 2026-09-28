"""Reproducible exact-index OHLC acquisition.

This module ingests Yahoo Finance ``^GSPC`` daily OHLC through ``yfinance``,
normalizes the returned DataFrame, and persists an immutable deterministic CSV
acquisition snapshot. The Yahoo CSV is not provider-response bytes. FRED
``SP500`` is not fetched and is not a validation source. The module deliberately
does not construct returns, realized variance, forecasts, or empirical
variance-risk-premium results.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any, Callable, Sequence
from zoneinfo import ZoneInfo

import pandas as pd

from vrp.data import write_immutable


YAHOO_SPX_SYMBOL = "^GSPC"
YAHOO_SPX_HISTORY_URL = "https://finance.yahoo.com/quote/%5EGSPC/history/"
NEW_YORK = ZoneInfo("America/New_York")
YAHOO_COLUMNS = ("Open", "High", "Low", "Close", "Adj Close", "Volume")

YahooDownload = Callable[..., pd.DataFrame]


class DataValidationError(ValueError):
    """Raised when downloaded source data violate the frozen contract."""


class PartialCurrentDayError(DataValidationError):
    """Raised when a provider returns a bar for the current New York date."""


@dataclass(frozen=True)
class SpxAcquisitionResult:
    """Compact handoff from one immutable exact-index acquisition."""

    retrieved_at_utc: str
    yahoo_relative_path: str
    manifest_relative_path: str
    yahoo_sha256: str
    row_count: int
    coverage_start: str
    coverage_end: str
    missing_values: dict[str, int]
    yfinance_version: str


def _flatten_yahoo_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    if not isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [str(column) for column in normalized.columns]
        return normalized

    for level in range(normalized.columns.nlevels):
        labels = [str(column) for column in normalized.columns.get_level_values(level)]
        if set(YAHOO_COLUMNS).issubset(labels):
            normalized.columns = labels
            return normalized
    raise DataValidationError(
        "Yahoo MultiIndex columns do not contain the required OHLC schema"
    )


def normalize_yahoo_spx(
    frame: pd.DataFrame,
    start_date: date,
    end_exclusive: date,
    retrieved_at: datetime,
) -> pd.DataFrame:
    """Normalize yfinance output while enforcing date and schema invariants."""

    if frame is None or frame.empty:
        raise DataValidationError("Yahoo returned no ^GSPC observations")
    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")

    normalized = _flatten_yahoo_columns(frame)
    missing_columns = sorted(set(YAHOO_COLUMNS) - set(normalized.columns))
    if missing_columns:
        raise DataValidationError(f"Yahoo schema missing columns: {missing_columns}")

    if "Date" in normalized.columns:
        parsed_dates = pd.to_datetime(normalized.pop("Date"), errors="raise")
    else:
        parsed_dates = pd.to_datetime(normalized.index, errors="raise")
    parsed_index = pd.DatetimeIndex(parsed_dates)
    if parsed_index.tz is not None:
        parsed_index = parsed_index.tz_convert(NEW_YORK).tz_localize(None)
    observation_dates = [timestamp.date() for timestamp in parsed_index]

    current_new_york_date = retrieved_at.astimezone(NEW_YORK).date()
    current_rows = sorted({value for value in observation_dates if value >= current_new_york_date})
    if current_rows:
        raise PartialCurrentDayError(
            "Yahoo returned current-day or future bars: "
            + ", ".join(value.isoformat() for value in current_rows[:5])
        )

    outside_window = sorted(
        {
            value
            for value in observation_dates
            if value < start_date or value >= end_exclusive
        }
    )
    if outside_window:
        raise DataValidationError(
            "Yahoo returned observations outside the frozen request: "
            + ", ".join(value.isoformat() for value in outside_window[:5])
        )
    if len(observation_dates) != len(set(observation_dates)):
        raise DataValidationError("Yahoo returned duplicate daily dates")

    output = normalized.loc[:, list(YAHOO_COLUMNS)].copy().reset_index(drop=True)
    for column in YAHOO_COLUMNS:
        output[column] = pd.to_numeric(output[column], errors="coerce")
    output.insert(0, "Date", [value.isoformat() for value in observation_dates])
    output = output.sort_values("Date", kind="stable").reset_index(drop=True)
    return output


def yahoo_csv_bytes(frame: pd.DataFrame) -> bytes:
    """Serialize normalized Yahoo observations deterministically."""

    text = frame.to_csv(
        index=False,
        lineterminator="\n",
        na_rep="",
        float_format="%.10g",
    )
    return text.encode("utf-8")


def _default_yahoo_download() -> tuple[YahooDownload, str]:
    try:
        import yfinance as yf
    except ImportError as error:
        raise RuntimeError(
            "yfinance is required; install the pinned project dependencies"
        ) from error
    return yf.download, version("yfinance")


def acquire_spx_index(
    raw_root: Path,
    start_date: date,
    end_exclusive: date,
    retrieved_at: datetime | None = None,
    yahoo_download: YahooDownload | None = None,
    yfinance_version: str | None = None,
    transport_note: str = "default verified TLS transports",
) -> SpxAcquisitionResult:
    """Acquire a frozen normalized ``^GSPC`` snapshot. FRED SP500 is not consulted."""

    retrieved = retrieved_at or datetime.now(timezone.utc)
    if retrieved.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    if start_date >= end_exclusive:
        raise ValueError("start_date must be before end_exclusive")
    current_new_york_date = retrieved.astimezone(NEW_YORK).date()
    if end_exclusive > current_new_york_date:
        raise ValueError(
            "end_exclusive cannot be after the current New York date; "
            "current-day observations are prohibited"
        )

    if yahoo_download is None:
        downloader, installed_version = _default_yahoo_download()
        yfinance_version = installed_version
    else:
        downloader = yahoo_download
        yfinance_version = yfinance_version or "test-double-unspecified"

    request_parameters: dict[str, Any] = {
        "tickers": YAHOO_SPX_SYMBOL,
        "start": start_date.isoformat(),
        "end": end_exclusive.isoformat(),
        "interval": "1d",
        "auto_adjust": False,
        "actions": False,
        "progress": False,
        "threads": False,
        "group_by": "column",
        "repair": False,
        "keepna": True,
        "prepost": False,
        "multi_level_index": False,
    }
    yahoo_provider_frame = downloader(**request_parameters)
    yahoo_frame = normalize_yahoo_spx(
        yahoo_provider_frame,
        start_date=start_date,
        end_exclusive=end_exclusive,
        retrieved_at=retrieved,
    )
    yahoo_snapshot = yahoo_csv_bytes(yahoo_frame)

    stamp = retrieved.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    yahoo_relative_path = Path(stamp) / "yahoo" / "gspc_ohlc_unadjusted.csv"
    manifest_relative_path = Path(stamp) / "gspc_manifest.json"
    yahoo_path = raw_root / yahoo_relative_path
    yahoo_digest = write_immutable(yahoo_path, yahoo_snapshot)

    missing_values = {
        column: int(yahoo_frame[column].isna().sum()) for column in YAHOO_COLUMNS
    }
    result = SpxAcquisitionResult(
        retrieved_at_utc=retrieved.astimezone(timezone.utc).isoformat(),
        yahoo_relative_path=yahoo_relative_path.as_posix(),
        manifest_relative_path=manifest_relative_path.as_posix(),
        yahoo_sha256=yahoo_digest,
        row_count=len(yahoo_frame),
        coverage_start=str(yahoo_frame["Date"].min()),
        coverage_end=str(yahoo_frame["Date"].max()),
        missing_values=missing_values,
        yfinance_version=str(yfinance_version),
    )
    manifest = {
        "schema_version": 3,
        "dataset": "S&P 500 price index daily OHLC",
        "research_scope": "Exact-index acquisition only; no realized-variance calculation",
        "retrieved_at_utc": result.retrieved_at_utc,
        "frozen_window": {
            "start_inclusive": start_date.isoformat(),
            "end_exclusive": end_exclusive.isoformat(),
            "current_day_policy": "reject any bar dated on or after retrieval's New York date",
        },
        "yahoo": {
            "provider": "Yahoo Finance via yfinance",
            "artifact_type": "immutable normalized acquisition snapshot",
            "provider_response_persisted": False,
            "symbol": YAHOO_SPX_SYMBOL,
            "source_page": YAHOO_SPX_HISTORY_URL,
            "yfinance_version": result.yfinance_version,
            "request_parameters": request_parameters,
            "relative_path": result.yahoo_relative_path,
            "sha256": result.yahoo_sha256,
            "bytes": len(yahoo_snapshot),
            "row_count": result.row_count,
            "coverage_start": result.coverage_start,
            "coverage_end": result.coverage_end,
            "persisted_columns": ["Date", *YAHOO_COLUMNS],
            "missing_values": result.missing_values,
            "normalization": [
                "schema normalization",
                "numeric parsing",
                "date normalization and sorting",
                "deterministic CSV serialization",
            ],
            "adjustment_policy": (
                "auto_adjust=False; unadjusted OHLC retained in normalized "
                "acquisition snapshot"
            ),
        },
        "index_source": {
            "provider": "Yahoo Finance",
            "symbol": YAHOO_SPX_SYMBOL,
            "fred_sp500_validation": False,
        },
        "redistribution_note": (
            "Normalized acquisition artifacts are ignored by Git; review Yahoo usage terms."
        ),
        "transport_note": transport_note,
    }
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    write_immutable(raw_root / manifest_relative_path, manifest_raw)
    return result


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("dates must use YYYY-MM-DD") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", type=_parse_date, required=True)
    parser.add_argument("--end-exclusive", type=_parse_date, required=True)
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
        help="local raw-data root (default: data/raw)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = acquire_spx_index(
        raw_root=args.raw_root,
        start_date=args.start_date,
        end_exclusive=args.end_exclusive,
    )
    print(
        f"{YAHOO_SPX_SYMBOL}: rows={result.row_count}, "
        f"coverage={result.coverage_start}..{result.coverage_end}, "
        f"sha256={result.yahoo_sha256}"
    )
    print(f"manifest={result.manifest_relative_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
