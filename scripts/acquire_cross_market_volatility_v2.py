"""Freeze longer Cboe/FRED volatility-index histories after registered overlap audit."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/cross_market_v2"
MANIFEST = ROOT / "data/manifests/cross_market_volatility_v2.json"
USER_AGENT = "Mozilla/5.0 (compatible; VRP-cross-market-research/1.0)"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def acquire(session: requests.Session, symbol: str, fred_id: str) -> dict:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fred_id}"
    response = session.get(url, timeout=60)
    response.raise_for_status()
    frame = pd.read_csv(pd.io.common.BytesIO(response.content))
    if list(frame.columns) != ["observation_date", fred_id]:
        raise ValueError(f"{fred_id}: unexpected CSV schema {frame.columns.tolist()}")
    frame["observation_date"] = pd.to_datetime(frame.observation_date, errors="raise")
    values = pd.to_numeric(frame[fred_id], errors="coerce")
    valid = values.notna()
    dates = frame.loc[valid, "observation_date"]
    if dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError(f"{fred_id}: duplicate or unordered valid observations")
    if not (values[valid] > 0).all():
        raise ValueError(f"{fred_id}: nonpositive value")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"fred_{fred_id.lower()}.csv"
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite frozen source file: {path}")
    path.write_bytes(response.content)
    return {
        "provider": "Cboe via FRED",
        "series": fred_id,
        "market_symbol": symbol,
        "url_requested": url,
        "url_final": response.url,
        "definition": f"Cboe {symbol} daily close distributed by FRED; current-vintage snapshot",
        "units": "volatility-index points",
        "rows_total": int(len(frame)),
        "rows_valid": int(valid.sum()),
        "first_valid_date": dates.min().date().isoformat(),
        "last_valid_date": dates.max().date().isoformat(),
        "missing_source_cells": int((~valid).sum()),
        "retrieved_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "raw_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "raw_bytes": len(response.content),
        "raw_sha256": digest(response.content),
        "vintage_limit": "FRED current distribution; not an ALFRED initial-release/as-of reconstruction",
    }


def main() -> None:
    if MANIFEST.exists():
        raise FileExistsError(f"Refusing to overwrite immutable manifest: {MANIFEST}")
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    sources = [acquire(session, "VXN", "VXNCLS"), acquire(session, "RVX", "RVXCLS")]
    manifest = {
        "schema_version": 1,
        "study": "cross-market-replication",
        "source_version": "v2",
        "protocol_amendment": "source-coverage amendment 2026-10-15, before outcomes",
        "raw_data_policy": "Local ignored storage only; no raw observations committed.",
        "sources": sources,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    MANIFEST.write_bytes(payload)
    print(json.dumps({"manifest": str(MANIFEST), "sha256": digest(payload), "sources": sources}, indent=2))


if __name__ == "__main__":
    main()
