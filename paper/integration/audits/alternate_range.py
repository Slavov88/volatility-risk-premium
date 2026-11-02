"""Replay eight archived CC scenarios, then measure allowable GK sensitivities.

Usage: python alternate_range.py EXACT_SPX.csv FRED_SP500.csv > output.csv
Only the seven FRED cells are used. Each must reproduce its originally recorded
signed log adjustment against the hash-matched Yahoo snapshot.
"""

import csv
import hashlib
import io
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[3] / "data/manifests"


def load(name):
    return json.loads((BASE / name).read_text())


def daily_variance(rows, index, close, prev_close):
    r = math.log(close / prev_close)
    o, h, l = (float(rows[index][key]) for key in ("Open", "High", "Low"))
    if not l <= close <= h:
        raise ValueError("Alternate close falls outside OHLC bounds")
    gk = 0.5 * math.log(h / l) ** 2 - (2 * math.log(2) - 1) * math.log(close / o) ** 2
    return r * r, gk


def main():
    src, overlay = map(Path, sys.argv[1:])
    freeze = load("2026-10-13_interim_freeze.json")
    if (
        hashlib.sha256(src.read_bytes()).hexdigest()
        != freeze["source_artifacts"]["spx"]["sha256"]
    ):
        raise ValueError("Unexpected canonical SPX snapshot")
    with src.open() as f:
        rows = list(csv.DictReader(f))
    with overlay.open() as f:
        fred = {r["observation_date"]: r["SP500"] for r in csv.DictReader(f)}
    original = [float(r["Close"]) for r in rows]
    dates = [date.fromisoformat(r["Date"]) for r in rows]
    signed = load("2026-10-13_source_blocker_diagnostics.json")[
        "hypothetical_single_close_correction_footprints"
    ]
    spx_index = {r["Date"]: i for i, r in enumerate(rows)}
    for record in signed:
        d = record["correction_date"]
        delta = math.log(float(fred[d]) / original[spx_index[d]])
        if not math.isclose(
            delta, record["signed_log_return_adjustments"][0], rel_tol=0, abs_tol=1e-15
        ):
            raise ValueError("FRED cell mismatch: " + d)
    # Close observations are absent at precisely these three eligible sessions.
    missing = set(freeze["coverage"]["full_sample"]["missing"])
    origins = [
        i
        for i, r in enumerate(rows)
        if r["Date"] <= "2025-12-31" and r["Date"] not in missing
    ]
    if len(origins) != freeze["coverage"]["full_sample"]["available"]:
        raise ValueError("Origin mask mismatch")
    archive = load("2026-10-13_alternate_close_sensitivity.json")
    baseline = load("2026-10-13_descriptive_statistics.json")["subsets"]["full_sample"]
    table = csv.writer(sys.stdout, lineterminator="\n")
    table.writerow(
        [
            "scenario",
            "horizon",
            "estimator",
            "affected_origins",
            "max_abs_target_change",
            "mean_proxy_change",
            "alternate_mean_proxy",
        ]
    )
    for scenario in archive["scenarios"]:
        replacements = scenario["replacement_dates"]
        alt = original.copy()
        for d in replacements:
            alt[spx_index[d]] = float(fred[d])
        affected = sorted(
            {idx + k for d in replacements for idx in [spx_index[d]] for k in [0, 1]}
        )
        changes = {}
        for j in affected:
            base = daily_variance(rows, j, original[j], original[j - 1])
            alternative = daily_variance(rows, j, alt[j], alt[j - 1])
            changes[j] = tuple(a - b for a, b in zip(alternative, base))
        for horizon, annual in (("30c", 365 / 30), ("21t", 252 / 21)):
            diffs = [[], []]
            for i in origins:
                included = [
                    v
                    for j, v in changes.items()
                    if i < j
                    and (
                        dates[j] <= dates[i] + timedelta(days=30)
                        if horizon == "30c"
                        else j <= i + 21
                    )
                ]
                for k in range(2):
                    diffs[k].append(annual * math.fsum(v[k] for v in included))
            for k, family in enumerate(("cc", "gk")):
                values = diffs[k]
                delta = -math.fsum(values) / len(values)
                largest = max(map(abs, values))
                if family == "cc":
                    old = scenario["horizons"][horizon]
                    if not (
                        math.isclose(
                            delta, old["mean_vrp_change_full_sample"], abs_tol=1e-16
                        )
                        and math.isclose(
                            largest, old["max_abs_rvar_change"], abs_tol=1e-13
                        )
                    ):
                        raise ValueError("Archived CC sensitivity failed")
                mean = baseline[f"vrp_x_{family}_{horizon}"]["mean"]
                table.writerow(
                    [
                        scenario["scenario"],
                        horizon,
                        family,
                        sum(v != 0 for v in values),
                        largest,
                        delta,
                        mean + delta,
                    ]
                )


if __name__ == "__main__":
    main()
