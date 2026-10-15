"""Validate frozen U.S. source snapshots and run Nasdaq-100/VXN H1-H2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import exchange_calendars as xc

from vrp.cross_market import build_close_panel, evaluate_h1_h2
from vrp.provisional_analysis import persist

ROOT = Path(__file__).resolve().parents[1]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_and_verify(manifest_path: Path) -> tuple[dict, dict[str, pd.DataFrame]]:
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    frames = {}
    for source in manifest["sources"]:
        path = ROOT / source["raw_path"]
        raw = path.read_bytes()
        if len(raw) != source["raw_bytes"] or sha(raw) != source["raw_sha256"]:
            raise ValueError(f"Source hash/size mismatch: {source['series']}")
        frames[source["series"]] = pd.read_csv(path)
    return {"record": manifest, "sha256": sha(manifest_raw)}, frames


def verify_vxn_cboe(fred: pd.DataFrame, cboe: pd.DataFrame, fred_id: str, symbol: str) -> dict:
    f = fred[["observation_date", fred_id]].copy()
    c = cboe[["DATE", "CLOSE"]].copy()
    f["observation_date"] = pd.to_datetime(f.observation_date, errors="raise").dt.date
    f[fred_id] = pd.to_numeric(f[fred_id], errors="coerce")
    c["DATE"] = pd.to_datetime(c.DATE, format="%m/%d/%Y", errors="raise").dt.date
    joined = f.merge(c, left_on="observation_date", right_on="DATE", how="inner").dropna(subset=[fred_id])
    if joined.empty or not np.array_equal(joined[fred_id].to_numpy(float), joined.CLOSE.to_numpy(float)):
        raise ValueError(f"{symbol}: FRED/Cboe overlap differs")
    return {"symbol": symbol, "overlap_n": len(joined), "exact_matches": len(joined),
            "first_overlap": min(joined.observation_date).isoformat(),
            "last_overlap": max(joined.observation_date).isoformat(), "max_abs_difference": 0.0}


def main() -> None:
    m1_path = ROOT / "data/manifests/cross_market_sources_v1.json"
    m2_path = ROOT / "data/manifests/cross_market_volatility_v2.json"
    first, f1 = load_and_verify(m1_path)
    second, f2 = load_and_verify(m2_path)
    code_files = ["src/vrp/cross_market.py", "src/vrp/inference.py", "src/vrp/provisional_analysis.py",
                  "src/vrp/calendar.py", "scripts/run_cross_market_us_h1_h2.py"]
    code_hashes = {name: sha((ROOT / name).read_bytes()) for name in code_files}
    vxn_audit = verify_vxn_cboe(f2["VXNCLS"], f1["VXN"], "VXNCLS", "VXN")
    rvx_audit = verify_vxn_cboe(f2["RVXCLS"], f1["RVX"], "RVXCLS", "RVX")
    ndx = f1["NASDAQ100"].rename(columns={"observation_date": "date", "NASDAQ100": "close"})
    ndx["date"] = pd.to_datetime(ndx.date, errors="raise").dt.date
    ndx["close"] = pd.to_numeric(ndx.close, errors="coerce")
    ndx = ndx.dropna(subset=["close"])
    source_calendar = xc.get_calendar("XNYS", start=ndx.date.min().isoformat(), end=ndx.date.max().isoformat())
    sessions = {x.date() for x in source_calendar.sessions_in_range(ndx.date.min(), ndx.date.max())}
    non_sessions = ndx.loc[~ndx.date.isin(sessions)].copy()
    # FRED distributes values carried forward on three dates when U.S. cash
    # markets were closed; these are quarantined rather than treated as returns.
    ndx = ndx.loc[ndx.date.isin(sessions)].reset_index(drop=True)
    missing_ndx_sessions = sorted(sessions - set(ndx.date))
    vxn = f2["VXNCLS"].rename(columns={"observation_date": "date", "VXNCLS": "level"})
    vxn["date"] = pd.to_datetime(vxn.date, errors="raise").dt.date
    vxn["level"] = pd.to_numeric(vxn.level, errors="coerce")
    vxn = vxn.dropna(subset=["level"])
    vxn_non_sessions = vxn.loc[~vxn.date.isin(sessions)].copy()
    vxn = vxn.loc[vxn.date.isin(sessions)].reset_index(drop=True)
    panel = build_close_panel(ndx, vxn, underlying_date="date", underlying_close="close",
                              implied_date="date", implied_close="level")
    h1_h2 = evaluate_h1_h2(panel)
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    output = {"status": "EXPLORATORY_EXTERNAL_REPLICATION — PROVISIONAL / PENDING INDEPENDENT REVIEW",
        "market": "NASDAQ-100 / Cboe VXN", "underlying_series": "NASDAQ100 via FRED (Nasdaq source)",
        "implied_series": "VXNCLS via FRED (Cboe source)", "analysis_origin_cutoff": "2025-12-31",
        "outcome_data_may_extend_to": "2026-01-30 for final 30-calendar-day origins",
        "revision_status": "current-vintage historical snapshots; no ALFRED/as-issued reconstruction",
        "protocol_commits": ["88de0f5", "ced7cce", "fb20a28"], "code_commit": git_commit,
        "code_sha256": code_hashes,
        "source_manifests": {"v1": first["sha256"], "v2": second["sha256"]},
        "source_overlap_audit": [vxn_audit, rvx_audit],
        "ndx_calendar_audit": {"calendar": "XNYS session dates, explicit 1986-2026 bounds",
            "valid_source_values_on_non_sessions_quarantined": [d.isoformat() for d in non_sessions.date],
            "quarantined_rule": "value is retained in raw source and excluded because date is not an XNYS session",
            "missing_expected_sessions": [d.isoformat() for d in missing_ndx_sessions],
            "missing_rule": "no interpolation; any target needing a missing return is excluded, and no return is computed across the gap",
            "observed_sessions_after_quarantine": len(ndx), "calendar_sessions": len(sessions)},
        "vxn_calendar_audit": {"valid_source_values_on_non_sessions_quarantined": [d.isoformat() for d in vxn_non_sessions.date],
            "valid_session_observations": len(vxn), "non_session_values_quarantined": len(vxn_non_sessions)},
        "panel": {"n": len(panel), "first_origin": panel.origin.min(), "last_origin": panel.origin.max(),
                  "origins_sha256": sha(("\n".join(panel.origin) + "\n").encode()),
                  "first_iv_origin": min(vxn.date).isoformat(), "target_horizons": ["30c: 365/30 annualized", "21t: 252/21 annualized"],
                  "calendar": "XNYS actual sessions for realized target construction; no forecast in this H1/H2 stage"},
        "h1_h2": h1_h2,
        "limits": ["FRED's present historical snapshot is not an initial-release/as-of data vintage.",
                   "No Russell index-level source passed the independent full-history verification gate.",
                   "VSTOXX licensed full history was not present in this environment."]}
    out_dir = ROOT / "outputs/cross_market/v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    panel_path = out_dir / "ndx_vxn_targets.csv"
    panel_bytes = panel.to_csv(index=False, lineterminator="\n", float_format="%.17g").encode("utf-8")
    if panel_path.exists():
        if panel_path.read_bytes() != panel_bytes:
            raise ValueError(f"Existing target artifact differs from deterministic rebuild: {panel_path}")
    else:
        panel_path.write_bytes(panel_bytes)
    output["panel"]["target_file"] = str(panel_path.relative_to(ROOT)).replace("\\", "/")
    output["panel"]["target_sha256"] = sha(panel_path.read_bytes())
    path = out_dir / "ndx_vxn_h1_h2_v2.json"
    print(persist(path, output), flush=True)
    print(json.dumps({"market": output["market"], "panel": output["panel"], "h1_primary": [x for x in h1_h2["h1"] if x["period"] == "maximum_available" and x["horizon"] == "30c" and x["lag"] == 21],
                      "h2_primary": [x for x in h1_h2["h2"] if x["period"] == "maximum_available" and x["horizon"] == "30c" and x["lag"] == 21]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
