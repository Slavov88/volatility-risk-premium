"""Acquire permitted source snapshots for the registered cross-market study.

Raw observations stay in ignored data/raw storage. The tracked manifest contains
metadata and hashes only; it is not a substitute for source entitlements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/cross_market_sources_v1.json"
AGENT = "Mozilla/5.0 (compatible; VRP-cross-market-research/1.0)"
CB0E = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{ticker}_History.csv"
FRED_NDX = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQ100"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dates(frame: pd.DataFrame, column: str) -> tuple[str | None, str | None]:
    values = pd.to_datetime(frame[column], errors="coerce").dropna()
    if values.empty:
        return None, None
    return values.min().date().isoformat(), values.max().date().isoformat()


def acquire_cboe(session: requests.Session, ticker: str, out: Path) -> dict:
    url = CB0E.format(ticker=ticker)
    response = session.get(url, timeout=60)
    response.raise_for_status()
    raw = response.content
    frame = pd.read_csv(pd.io.common.BytesIO(raw))
    required = {"DATE", "OPEN", "HIGH", "LOW", "CLOSE"}
    if not required.issubset(frame.columns):
        raise ValueError(f"{ticker}: unexpected Cboe schema {list(frame.columns)}")
    frame["DATE"] = pd.to_datetime(frame["DATE"], format="%m/%d/%Y", errors="raise")
    if frame.DATE.duplicated().any() or not frame.DATE.is_monotonic_increasing:
        raise ValueError(f"{ticker}: duplicate or unordered dates")
    for col in ("OPEN", "HIGH", "LOW", "CLOSE"):
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    if not (frame[["OPEN", "HIGH", "LOW", "CLOSE"]].gt(0).all().all()):
        raise ValueError(f"{ticker}: nonpositive OHLC")
    if not (frame.HIGH >= frame[["OPEN", "CLOSE", "LOW"]].max(axis=1)).all():
        raise ValueError(f"{ticker}: invalid high")
    if not (frame.LOW <= frame[["OPEN", "CLOSE", "HIGH"]].min(axis=1)).all():
        raise ValueError(f"{ticker}: invalid low")
    path = out / f"cboe_{ticker.lower()}_history.csv"
    path.write_bytes(raw)
    return {
        "provider": "Cboe Global Indices",
        "series": ticker,
        "url_requested": url,
        "url_final": response.url,
        "definition": f"Official daily OHLC history for Cboe {ticker} volatility index",
        "units": "index points; volatility-index methodology-specific annualized measure",
        "rows": int(len(frame)),
        "first_date": frame.DATE.min().date().isoformat(),
        "last_date": frame.DATE.max().date().isoformat(),
        "missing_cells": int(frame[list(required)].isna().sum().sum()),
        "raw_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "raw_sha256": sha256(raw),
        "raw_bytes": len(raw),
        "validation": "schema, date order/uniqueness, positive OHLC, and OHLC inequalities passed",
    }


def acquire_ndx(session: requests.Session, out: Path) -> dict:
    response = session.get(FRED_NDX, timeout=60)
    response.raise_for_status()
    raw = response.content
    frame = pd.read_csv(pd.io.common.BytesIO(raw))
    if list(frame.columns) != ["observation_date", "NASDAQ100"]:
        raise ValueError(f"NASDAQ100: unexpected source schema {list(frame.columns)}")
    frame["observation_date"] = pd.to_datetime(frame.observation_date, errors="raise")
    finite = pd.to_numeric(frame.NASDAQ100, errors="coerce")
    valid = frame.loc[finite.notna(), ["observation_date"]].copy()
    valid["close"] = finite.loc[finite.notna()].astype(float).values
    if valid.observation_date.duplicated().any() or not valid.observation_date.is_monotonic_increasing:
        raise ValueError("NASDAQ100: duplicate or unordered dates")
    if not valid.close.gt(0).all():
        raise ValueError("NASDAQ100: nonpositive close")
    path = out / "nasdaq100_fred_distribution.csv"
    path.write_bytes(raw)
    return {
        "provider": "Nasdaq, Inc. via FRED",
        "series": "NASDAQ100",
        "url_requested": FRED_NDX,
        "url_final": response.url,
        "definition": "NASDAQ-100 daily market-close index value; Nasdaq source series distributed by FRED",
        "units": "index points",
        "rows_total": int(len(frame)),
        "rows_finite": int(len(valid)),
        "missing_values": int(len(frame) - len(valid)),
        "first_date": valid.observation_date.min().date().isoformat(),
        "last_date": valid.observation_date.max().date().isoformat(),
        "raw_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "raw_sha256": sha256(raw),
        "raw_bytes": len(raw),
        "validation": "source schema, date order/uniqueness, and positive finite closes passed; missing source cells retained as missing",
    }


def _yf_csv(ticker: str, frame: pd.DataFrame) -> bytes:
    if isinstance(frame.columns, pd.MultiIndex):
        if frame.columns.nlevels > 1:
            frame.columns = frame.columns.get_level_values(0)
    frame = frame.copy()
    frame.index.name = "Date"
    return frame.to_csv(date_format="%Y-%m-%d", lineterminator="\n", float_format="%.12g").encode("utf-8")


def acquire_yahoo(ticker: str, out: Path) -> dict:
    frame = yf.download(
        ticker,
        start="2000-01-01",
        end="2026-10-15",
        auto_adjust=False,
        actions=True,
        repair=False,
        keepna=True,
        progress=False,
        threads=False,
        group_by="column",
    )
    if frame.empty:
        raise RuntimeError(f"Yahoo returned no data for {ticker}")
    if isinstance(frame.columns, pd.MultiIndex):
        if frame.columns.nlevels > 1:
            frame.columns = frame.columns.get_level_values(0)
    frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError(f"{ticker}: duplicate or unordered dates")
    names = {str(col).lower().replace(" ", "_"): col for col in frame.columns}
    for name in ("open", "high", "low", "close", "adj_close"):
        if name not in names:
            raise ValueError(f"{ticker}: missing {name}")
        frame[names[name]] = pd.to_numeric(frame[names[name]], errors="coerce")
    price = frame[[names[k] for k in ("open", "high", "low", "close")]]
    if price.isna().any().any() or not price.gt(0).all().all():
        raise ValueError(f"{ticker}: missing or nonpositive OHLC")
    if not (frame[names["high"]] >= frame[[names["open"], names["close"], names["low"]]].max(axis=1)).all():
        raise ValueError(f"{ticker}: invalid high")
    if not (frame[names["low"]] <= frame[[names["open"], names["close"], names["high"]]].min(axis=1)).all():
        raise ValueError(f"{ticker}: invalid low")
    data = _yf_csv(ticker, frame)
    path = out / f"yahoo_{ticker.lower().replace('^','')}_normalized.csv"
    path.write_bytes(data)
    dividend_col = next((c for c in frame.columns if str(c).lower() == "dividends"), None)
    split_col = next((c for c in frame.columns if str(c).lower() in {"stock splits", "stock_splits"}), None)
    return {
        "provider": "Yahoo Finance via yfinance",
        "series": ticker,
        "definition": "Vendor daily OHLC, adjusted close, dividend and split action snapshot; unadjusted Close used for price-level returns",
        "request": {"start_inclusive": "2000-01-01", "end_exclusive": "2026-10-15", "auto_adjust": False, "actions": True, "repair": False},
        "software": {"yfinance": yf.__version__, "pandas": pd.__version__},
        "rows": int(len(frame)),
        "first_date": frame.index.min().date().isoformat(),
        "last_date": frame.index.max().date().isoformat(),
        "dividend_events": int((pd.to_numeric(frame[dividend_col], errors="coerce").fillna(0) != 0).sum()) if dividend_col else None,
        "split_events": int((pd.to_numeric(frame[split_col], errors="coerce").fillna(0) != 0).sum()) if split_col else None,
        "raw_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "raw_sha256": sha256(data),
        "raw_bytes": len(data),
        "validation": "daily date order/uniqueness, positive finite OHLC, OHLC inequalities passed; corporate actions retained",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    acquired = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = acquired.strftime("%Y-%m-%dT%H%M%SZ")
    out = args.output or ROOT / "data/raw/cross_market_v1" / stamp
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    session = requests.Session()
    session.headers.update({"User-Agent": AGENT})
    series = [
        acquire_cboe(session, "VXN", out),
        acquire_cboe(session, "RVX", out),
        acquire_ndx(session, out),
        acquire_yahoo("^RUT", out),
        acquire_yahoo("QQQ", out),
        acquire_yahoo("IWM", out),
    ]
    record = {
        "schema_version": 1,
        "study": "cross-market-replication",
        "protocol_commit": "ced7cce",
        "acquired_at_utc": acquired.isoformat().replace("+00:00", "Z"),
        "analysis_origin_cutoff": "2025-12-31",
        "raw_data_policy": "Local ignored storage only; do not redistribute source observations.",
        "rights_basis": "Author attested 2026-10-15 that written permissions cover research use and public sharing of derived results from all proposed providers; license documents are not stored in this checkout.",
        "sources": series,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if MANIFEST.exists():
        raise FileExistsError(f"Refusing to overwrite immutable manifest: {MANIFEST}")
    MANIFEST.write_bytes(payload)
    print(json.dumps({"manifest": str(MANIFEST), "manifest_sha256": sha256(payload), "sources": series}, indent=2))


if __name__ == "__main__":
    main()
