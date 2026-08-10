"""Versioned raw-data acquisition for the initial feasibility study.

The module downloads source bytes without cleaning them, writes immutable
date-stamped snapshots, and records a provenance manifest. The Nasdaq SPY feed
is deliberately labelled as a provisional OHLC proxy rather than S&P 500 index
data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Sequence


CBOE_VIX_URL = (
    "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
)
TREASURY_YIELD_CURVE_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
)
NASDAQ_SPY_URL = "https://api.nasdaq.com/api/quote/SPY/historical"
USER_AGENT = "volatility-risk-premium-research/0.1 (academic reproducibility)"


@dataclass(frozen=True)
class SourceSpec:
    """A raw source and its scientific role."""

    name: str
    url: str
    relative_path: str
    authority: str
    research_role: str
    status: str


@dataclass(frozen=True)
class SourceSummary:
    """Auditable metadata for one raw snapshot."""

    name: str
    source_url: str
    authority: str
    research_role: str
    status: str
    retrieved_at_utc: str
    relative_path: str
    sha256: str
    bytes: int
    row_count: int
    coverage_start: str | None
    coverage_end: str | None
    raw_columns: list[str]
    missing_values: dict[str, int]


def source_specs(start_date: date, end_date: date) -> tuple[SourceSpec, ...]:
    """Return the pre-declared sources for a dated feasibility run."""

    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    query = urllib.parse.urlencode(
        {
            "assetclass": "etf",
            "fromdate": start_date.isoformat(),
            "todate": end_date.isoformat(),
            "limit": 5000,
        }
    )
    specs = [
        SourceSpec(
            name="cboe_vix",
            url=CBOE_VIX_URL,
            relative_path="cboe/vix_history.csv",
            authority="Cboe Global Markets",
            research_role="Primary VIX index history",
            status="primary",
        ),
    ]
    for year in range(start_date.year, end_date.year + 1):
        specs.append(
            SourceSpec(
                name=f"treasury_yield_curve_{year}",
                url=TREASURY_YIELD_CURVE_URL.format(year=year),
                relative_path=f"treasury/yield_curve_{year}.xml",
                authority="U.S. Department of the Treasury",
                research_role="Primary yield curve; 3-month point is provisional rate proxy",
                status="primary-provisional-tenor",
            )
        )
    specs.append(
        SourceSpec(
            name="nasdaq_spy_ohlc",
            url=f"{NASDAQ_SPY_URL}?{query}",
            relative_path="nasdaq/spy_ohlc.json",
            authority="Nasdaq",
            research_role="Engineering-only OHLC proxy for the S&P 500",
            status="provisional-proxy-not-final-index-data",
        )
    )
    return tuple(specs)


def fetch_bytes(url: str, timeout_seconds: float = 30.0) -> bytes:
    """Fetch source bytes with an explicit user agent and timeout."""

    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        if response.status != 200:
            raise RuntimeError(f"download failed with HTTP {response.status}: {url}")
        return response.read()


def _csv_summary(raw: bytes, date_column: str) -> tuple[int, str, str, list[str], dict[str, int]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or date_column not in reader.fieldnames:
        raise ValueError(f"missing required date column {date_column!r}")
    rows = list(reader)
    if not rows:
        raise ValueError("source returned no data rows")

    columns = list(reader.fieldnames)
    missing = {
        column: sum(row.get(column, "").strip() in {"", ".", "NA", "null"} for row in rows)
        for column in columns
    }
    dates = sorted(row[date_column].strip() for row in rows if row[date_column].strip())
    return len(rows), dates[0], dates[-1], columns, missing


def summarize_cboe_vix(raw: bytes) -> tuple[int, str, str, list[str], dict[str, int]]:
    """Validate and summarize the unmodified Cboe VIX CSV."""

    summary = _csv_summary(raw, "DATE")
    required = {"DATE", "OPEN", "HIGH", "LOW", "CLOSE"}
    if not required.issubset(summary[3]):
        raise ValueError(f"Cboe schema missing columns: {sorted(required - set(summary[3]))}")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    parsed_dates = sorted(
        datetime.strptime(row["DATE"].strip(), "%m/%d/%Y").date()
        for row in reader
        if row["DATE"].strip()
    )
    return (
        summary[0],
        parsed_dates[0].isoformat(),
        parsed_dates[-1].isoformat(),
        summary[3],
        summary[4],
    )


def summarize_treasury_yield_curve(
    raw: bytes,
) -> tuple[int, str, str, list[str], dict[str, int]]:
    """Validate and summarize an unmodified Treasury Atom/XML yield feed."""

    root = ET.fromstring(raw)
    atom = {"atom": "http://www.w3.org/2005/Atom"}
    data_namespace = "http://schemas.microsoft.com/ado/2007/08/dataservices"
    entries = root.findall("atom:entry", atom)
    if not entries:
        raise ValueError("Treasury source returned no entries")

    records: list[dict[str, str]] = []
    for entry in entries:
        record: dict[str, str] = {}
        for element in entry.iter():
            if element.tag.startswith(f"{{{data_namespace}}}"):
                name = element.tag.split("}", 1)[1]
                record[name] = (element.text or "").strip()
        records.append(record)

    required = {"NEW_DATE", "BC_3MONTH"}
    columns = sorted({column for record in records for column in record})
    if not required.issubset(columns):
        raise ValueError(f"Treasury schema missing columns: {sorted(required - set(columns))}")
    dates = sorted(record["NEW_DATE"][:10] for record in records if record.get("NEW_DATE"))
    missing = {
        column: sum(record.get(column, "") == "" for record in records)
        for column in columns
    }
    return len(records), dates[0], dates[-1], columns, missing


def summarize_nasdaq_spy(raw: bytes) -> tuple[int, str, str, list[str], dict[str, int]]:
    """Validate and summarize Nasdaq's SPY OHLC JSON response."""

    payload = json.loads(raw)
    status = payload.get("status", {})
    if status.get("rCode") != 200:
        raise ValueError(f"Nasdaq response was not successful: {status}")
    rows = payload["data"]["tradesTable"]["rows"]
    if not rows:
        raise ValueError("Nasdaq source returned no rows")

    columns = ["date", "open", "high", "low", "close", "volume"]
    missing = {
        column: sum(row.get(column) in {None, "", "N/A"} for row in rows)
        for column in columns
    }
    parsed_dates = sorted(datetime.strptime(row["date"], "%m/%d/%Y").date() for row in rows)
    return (
        len(rows),
        parsed_dates[0].isoformat(),
        parsed_dates[-1].isoformat(),
        columns,
        missing,
    )


SUMMARIZERS: dict[
    str, Callable[[bytes], tuple[int, str, str, list[str], dict[str, int]]]
] = {
    "cboe_vix": summarize_cboe_vix,
    "nasdaq_spy_ohlc": summarize_nasdaq_spy,
}


def write_immutable(path: Path, raw: bytes) -> str:
    """Write bytes atomically; refuse to alter an existing different snapshot."""

    digest = hashlib.sha256(raw).hexdigest()
    if path.exists():
        existing_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing_digest != digest:
            raise FileExistsError(f"immutable snapshot differs from source: {path}")
        return digest

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(raw)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)
    return digest


def acquire_samples(
    root: Path,
    start_date: date,
    end_date: date,
    retrieved_at: datetime | None = None,
) -> list[SourceSummary]:
    """Download, validate, and version the feasibility sources."""

    retrieved = retrieved_at or datetime.now(timezone.utc)
    if retrieved.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    stamp = retrieved.date().isoformat()
    summaries: list[SourceSummary] = []

    for spec in source_specs(start_date, end_date):
        raw = fetch_bytes(spec.url)
        summarizer = (
            summarize_treasury_yield_curve
            if spec.name.startswith("treasury_yield_curve_")
            else SUMMARIZERS[spec.name]
        )
        row_count, coverage_start, coverage_end, columns, missing = summarizer(raw)
        relative_path = Path(stamp) / spec.relative_path
        target = root / relative_path
        digest = write_immutable(target, raw)
        summaries.append(
            SourceSummary(
                name=spec.name,
                source_url=spec.url,
                authority=spec.authority,
                research_role=spec.research_role,
                status=spec.status,
                retrieved_at_utc=retrieved.astimezone(timezone.utc).isoformat(),
                relative_path=relative_path.as_posix(),
                sha256=digest,
                bytes=len(raw),
                row_count=row_count,
                coverage_start=coverage_start,
                coverage_end=coverage_end,
                raw_columns=columns,
                missing_values=missing,
            )
        )

    manifest_path = root / stamp / "manifest.json"
    manifest = {
        "schema_version": 1,
        "retrieved_at_utc": retrieved.astimezone(timezone.utc).isoformat(),
        "requested_sample_window": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "sources": [asdict(summary) for summary in summaries],
    }
    write_immutable(
        manifest_path,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return summaries


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("dates must use YYYY-MM-DD") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", type=_parse_date, required=True)
    parser.add_argument("--end-date", type=_parse_date, required=True)
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
        help="local raw-data root (default: data/raw)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summaries = acquire_samples(args.raw_root, args.start_date, args.end_date)
    for summary in summaries:
        print(
            f"{summary.name}: rows={summary.row_count}, "
            f"coverage={summary.coverage_start}..{summary.coverage_end}, "
            f"sha256={summary.sha256[:12]}..."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
