"""Resumable all-origin Nasdaq-100 GARCH forecasts for cross-market H3/H4."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import exchange_calendars as xc
from importlib.metadata import version

from vrp.asof_garch_calendar import forecast_schedule, POLICY
from vrp.provisional_analysis import persist
from vrp.recursive_garch import Checkpoints, FIT_CONFIG, VARIANTS, fit_origin, training_slice

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/cross_market_v1/2026-10-15T123148Z/nasdaq100_fred_distribution.csv"
PANEL = ROOT / "outputs/cross_market/v1/ndx_vxn_targets.csv"
OUT = ROOT / "outputs/cross_market/v1/ndx_garch"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def load_returns() -> tuple[list[date], np.ndarray, pd.DataFrame]:
    source = pd.read_csv(SOURCE)
    source["date"] = pd.to_datetime(source.observation_date, errors="raise").dt.date
    source["close"] = pd.to_numeric(source.NASDAQ100, errors="coerce")
    source = source.dropna(subset=["close"])
    cal = xc.get_calendar("XNYS", start=source.date.min().isoformat(), end=source.date.max().isoformat())
    sessions = [x.date() for x in cal.sessions_in_range(source.date.min(), source.date.max())]
    source = source.loc[source.date.isin(sessions)].set_index("date").sort_index()
    closes = source.close.to_dict()
    returns = {}
    for prior, current in zip(sessions[:-1], sessions[1:]):
        if prior in closes and current in closes:
            returns[current] = float(np.log(closes[current] / closes[prior]))
    # A missing endpoint is not bridged with a multi-session return.
    days = sorted(returns)
    values = np.asarray([returns[d] for d in days], dtype=float)
    if not np.isfinite(values).all() or not days:
        raise ValueError("No valid finite Nasdaq daily returns")
    return days, values, source.reset_index()


def run_variant(variant: str, limit: int | None) -> None:
    days, values, source = load_returns()
    targets = pd.read_csv(PANEL, dtype={"origin": str})
    targets = targets.loc[(targets.origin >= "2007-01-01") & (targets.origin <= "2025-12-31")]
    origins = targets.origin.tolist()
    if not origins or origins != sorted(set(origins)):
        raise ValueError("Target origins must be nonempty, unique, and chronological")
    dist, window = VARIANTS[variant]
    files = ["src/vrp/recursive_garch.py", "src/vrp/asof_garch_calendar.py", "src/vrp/quant_calendar.py",
             "scripts/run_cross_market_ndx_garch.py"]
    code_hashes = {p: sha((ROOT / p).read_bytes()) for p in files}
    config = {"market": "NASDAQ100", "variant": variant, "distribution": dist, "window": window,
        "fit": FIT_CONFIG, "forecast_calendar_policy": POLICY,
        "calendar": "XNYS actual dates for return history; scheduled regular holidays for future forecast sessions",
        "source_sha256": sha(SOURCE.read_bytes()), "target_panel_sha256": sha(PANEL.read_bytes()),
        "implementation_sha256": code_hashes, "input_returns_sha256": sha(values.astype("<f8").tobytes()),
        "origin_set_sha256": sha(("\n".join(origins)+"\n").encode()),
        "software": {"arch": version("arch"), "numpy": version("numpy"), "scipy": version("scipy"), "pandas": version("pandas"), "python": sys.version.split()[0]},
        "cutoff": "2025-12-31", "minimum_training_rule": "all available returns through origin; five-calendar-year rolling window for rolling variant"}
    label = sha(canonical(config).encode())[:16]
    base = OUT / variant / label
    base.mkdir(parents=True, exist_ok=True)
    config_bytes = (json.dumps(config, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    config_path = base / "configuration.json"
    if config_path.exists() and config_path.read_bytes() != config_bytes:
        raise ValueError("Existing configuration differs from current frozen inputs/code")
    if not config_path.exists():
        config_path.write_bytes(config_bytes)
    checkpoint = Checkpoints(base / "checkpoints.sqlite", config)
    records = []
    reused = 0
    actual_session_counts = dict(zip(targets.origin, targets.n_sessions_30c))
    for i, origin_text in enumerate(origins):
        if limit is not None and i >= limit:
            break
        origin = date.fromisoformat(origin_text)
        start, end, train = training_slice(days, values, origin, window)
        sessions30, sessions = forecast_schedule(origin)
        if not sessions30 or sessions[:len(sessions30)] != sessions30:
            raise ValueError(f"Invalid deterministic forecast horizon at {origin_text}")
        expected = {"origin": origin_text, "training_start": days[start].isoformat(), "training_end": days[end-1].isoformat(),
            "training_n": len(train), "training_sha256": sha(train.astype("<f8").tobytes()),
            "forecast_sessions": [x.isoformat() for x in sessions], "session_count_30c": len(sessions30),
            "target_actual_session_count_30c": int(actual_session_counts[origin_text])}
        record = checkpoint.read(origin_text, expected)
        if record is None:
            record = {**expected, **fit_origin(train, dist, len(sessions), False)}
            if record["status"] == "CONVERGED":
                daily = record["daily_decimal_variances"]
                record["garch_30c"] = 365 / 30 * sum(daily[:len(sessions30)])
                record["garch_21t"] = 252 / 21 * sum(daily[:21])
                # Numerical recurrence was checked inside fit_origin; this
                # explicit direct recurrence ensures the horizon count used
                # for each registered aggregate is exactly the intended one.
                p = record["parameters"]
                rec = [daily[0]]
                omega = p["omega"] / 10000
                persistence = p["alpha[1]"] + p["beta[1]"]
                for _ in range(1, len(sessions)):
                    rec.append(omega + persistence * rec[-1])
                if not np.allclose(daily, rec, rtol=1e-9, atol=1e-13):
                    raise ValueError(f"Forecast recurrence verification failed: {origin_text}")
                record["recurrence_max_abs_error_decimal_variance"] = float(np.max(np.abs(np.asarray(daily)-np.asarray(rec))))
            checkpoint.write(origin_text, record)
        else:
            reused += 1
        records.append(record)
        if (i + 1) % 50 == 0 or i == 0:
            print(f"{variant} {i+1}/{len(origins)} reused={reused} failures={sum(r['status']!='CONVERGED' for r in records)}", flush=True)
    checkpoint.close()
    if len(records) == len(origins):
        output = {"status": "EXPLORATORY_EXTERNAL_REPLICATION — PROVISIONAL / PENDING INDEPENDENT REVIEW",
            "market": "NASDAQ-100 / Cboe VXN", "variant": variant, "configuration": config,
            "configuration_sha256": sha(config_path.read_bytes()),
            "coverage_complete": True, "expected_origins": len(origins), "completed_origins": len(records),
            "reused_checkpoints": reused, "records": records}
        base.mkdir(parents=True, exist_ok=True)
        path = base / "forecasts.json"
        if path.exists():
            if path.read_bytes() != (json.dumps(output, indent=2, sort_keys=True, allow_nan=False)+"\n").encode():
                raise ValueError("Existing forecast artifact differs from deterministic rebuild")
        else:
            persist(path, output)
    print(f"{variant} checkpoint={base} complete={len(records)}/{len(origins)} reused={reused}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=VARIANTS, action="append")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    for variant in (args.variant or list(VARIANTS)):
        run_variant(variant, args.limit)


if __name__ == "__main__":
    main()
