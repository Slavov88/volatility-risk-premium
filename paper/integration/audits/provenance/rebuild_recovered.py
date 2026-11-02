"""Reconstruct private freeze/targets from recovered bytes; no gate bypass.

Usage: PYTHONPATH=REPO/src:PARSER python rebuild_recovered.py REPO ARCHIVE OUTPUT
The output is private market data. Publish only receipt.json and this script.
"""

import hashlib, json, sys, platform
from datetime import date, datetime, timezone
from importlib.metadata import version
from pathlib import Path
import pandas as pd
from vrp.archival_vix import (
    AUTHORIZATION,
    ARCHIVE_SHA,
    ARCHIVE_URL,
    verify_archive,
    insert_archival_close,
)
from vrp.calendar import exchange_sessions
from vrp.origin_panel import align_origin_panel
from vrp.vix_data import parse_cboe_vix
from vrp.empirical_targets import construct_targets, audit_targets, describe_targets
from vrp.spx_data import yahoo_csv_bytes

repo, archive, output = map(Path, sys.argv[1:])
output.mkdir(parents=True, exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
freeze = json.loads(
    (repo / "data/manifests/2026-10-13_interim_freeze.json").read_bytes()
)
target = json.loads(
    (repo / "data/manifests/2026-10-13_provisional_targets.json").read_bytes()
)
raw_spx = (archive / "spx_candidate.csv").read_bytes()
if sha(raw_spx) != freeze["source_artifacts"]["spx"]["sha256"]:
    raise ValueError("SPX CSV does not match the historical source hash")
chart_raw = (archive / "yahoo-chart2.json").read_bytes()
chart = json.loads(chart_raw)["chart"]["result"][0]
q = chart["indicators"]["quote"][0]
chart_frame = pd.DataFrame(
    {
        "Date": [
            datetime.fromtimestamp(t, timezone.utc).date().isoformat()
            for t in chart["timestamp"]
        ],
        **{k.title(): v for k, v in q.items()},
    }
)
chart_frame["Adj Close"] = chart["indicators"]["adjclose"][0]["adjclose"]
chart_frame = chart_frame[
    ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
]
chart_frame = chart_frame.loc[
    (chart_frame.Date >= "1990-01-02") & (chart_frame.Date < "2026-02-03")
]
if yahoo_csv_bytes(chart_frame) != raw_spx:
    raise ValueError("Yahoo chart normalization does not match recovered SPX CSV")
current = (archive / "vix_current.csv").read_bytes()
raw_vix = current[: freeze["source_artifacts"]["vix_raw"]["bytes"]]
if sha(raw_vix) != freeze["source_artifacts"]["vix_raw"]["sha256"]:
    raise ValueError("VIX prefix does not match the historical source hash")
(output / "recovered_VIX_History.csv").write_bytes(raw_vix)
vix = parse_cboe_vix(
    raw_vix, start_date=date(1990, 1, 2), end_exclusive=date(2026, 1, 1)
)
normal = vix.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode()
if sha(normal) != freeze["source_artifacts"]["vix_normalized"]["sha256"]:
    raise ValueError("Normalized VIX does not match the historical hash")
evidence = verify_archive(
    archive,
    {
        "relative_path": "vixarchive.xls",
        "sha256": ARCHIVE_SHA,
        "source_url": ARCHIVE_URL,
    },
)
combined = insert_archival_close(vix, evidence, AUTHORIZATION)
eligible = {
    d.isoformat() for d in exchange_sessions(date(1990, 1, 2), date(2025, 12, 31))
}
close = combined.loc[combined.Date.isin(eligible)].reset_index(drop=True)
spx = pd.read_csv(archive / "spx_candidate.csv", dtype={"Date": "string"})
rows, alignment = align_origin_panel(
    spx.Date.tolist(), list(zip(close.Date, close.CLOSE))
)
source_map = dict(zip(close.Date, close.vix_source))
spx_map = dict(zip(spx.Date, spx.Close))
panel = pd.DataFrame(
    [
        {
            "origin": r.origin.isoformat(),
            "spx_close": float(spx_map[r.origin.isoformat()]),
            "vix_close": r.vix_close,
            "ivol": r.ivol,
            "ivar": r.ivar,
            "vix_methodology_regime": r.vix_methodology_regime,
            "vix_source": source_map[r.origin.isoformat()],
        }
        for r in rows
    ]
)
daily, targets = construct_targets(spx, panel)
audit = audit_targets(spx, panel, daily, targets)
frames = {
    "interim_vix_close.csv": close,
    "interim_origin_panel.csv": panel,
    "canonical_spx_ohlc.csv": spx,
    "canonical_daily.csv": daily,
    "six_forward_targets.csv": targets,
}
records = {}
for name, frame in frames.items():
    raw = frame.to_csv(index=False, lineterminator="\n", float_format="%.17g").encode()
    expected = (freeze["outputs"] if name in freeze["outputs"] else target["outputs"])[
        name
    ]
    if name in freeze["outputs"]:
        if sha(raw) != expected["sha256"]:
            raise ValueError(
                f"{name}: reconstructed freeze hash {sha(raw)} != {expected['sha256']}"
            )
    path = output / expected["relative_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    records[name] = {
        "sha256": sha(raw),
        "rows": len(frame),
        "bytes": len(raw),
        "original_sha256": expected["sha256"],
        "original_hash_match": sha(raw) == expected["sha256"],
        "relative_path": expected["relative_path"],
    }
for name, obj in [
    ("target_audit.json", audit),
    ("descriptive_statistics.json", describe_targets(targets)),
]:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    expected = target["outputs"][name]
    path = output / expected["relative_path"]
    path.write_bytes(raw)
    records[name] = {
        "sha256": sha(raw),
        "original_sha256": expected["sha256"],
        "original_hash_match": sha(raw) == expected["sha256"],
    }
receipt = {
    "status": "EXACT_FREEZE_WITH_NUMERICALLY_AUDITED_FRESH_TARGETS",
    "source_raw_spx_sha256": sha(raw_spx),
    "recovery_yahoo_chart_response_sha256": sha(chart_raw),
    "chart_normalization_exactly_matches_original_spx": True,
    "source_raw_vix_sha256": sha(raw_vix),
    "current_vix_download_sha256": sha(current),
    "vix_prefix_bytes": len(raw_vix),
    "source_xls_sha256": ARCHIVE_SHA,
    "archive_verification": evidence,
    "outputs": records,
    "audit": audit,
    "full_manifest_chain_replayed": False,
    "runtime": {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            p: version(p)
            for p in [
                "numpy",
                "pandas",
                "scipy",
                "statsmodels",
                "arch",
                "exchange-calendars",
                "yfinance",
            ]
        },
    },
    "limitation": "Original SPX source manifest and original FRED SP500 response unavailable. Original VIX manifest is recovered exactly from tracked rejected manifest. No forged replacement; production verify_interim has not passed.",
    "review_status": "PROVISIONAL / NOT INDEPENDENTLY ACCEPTED",
}
(output / "receipt.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(receipt, indent=2))
