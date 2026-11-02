"""Fresh H1/H2 calculations from exact NDX/VXN and rebuilt SPX targets.

This is not recovery of missing historical output bytes. The registered H1
circular-bootstrap interval is added transparently; the incomplete H1-H5
market-contrast multiplicity family is neither invented nor marked complete.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from pathlib import Path

# Avoid bytecode writes to the supplied checkout or dependency locations.
sys.dont_write_bytecode = True

import exchange_calendars as xc
import numpy as np
import pandas as pd



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True, help="cross-market source checkout")
    parser.add_argument("--source-dir", type=Path, required=True, help="directory containing exact NASDAQ100 and VXNCLS CSVs")
    parser.add_argument("--spx-targets", type=Path, required=True, help="reconstructed six_forward_targets.csv")
    parser.add_argument("--output", type=Path, required=True, help="destination JSON file")
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    sys.path.insert(0, str(checkout / "src"))
    from vrp.cross_market import build_close_panel, evaluate_h1_h2
    from vrp.provisional_analysis import checked_mean, checked_regression

    ndx_path = args.source_dir / "NASDAQ100_exact.csv"
    vxn_path = args.source_dir / "VXNCLS_exact.csv"
    spx_path = args.spx_targets
    require(sha(ndx_path) == "2326ea9359dc6d521ada1c0600b90be23e054b4ba93955a615a5dba97159ff9f", "Nasdaq source hash mismatch")
    require(sha(vxn_path) == "53aa81e815b3f9f5b7b18bcfa64f0c5d02b2341aad5b128307f069d1d7bd3f2f", "VXN source hash mismatch")
    require(sha(spx_path) == "3c7fc89fc510659fca0a976ad0d61f780aa93505cc2764f53d38a3a14d671fbc", "Reconstructed S&P target hash mismatch")
    ndx = pd.read_csv(ndx_path).rename(columns={"observation_date": "date", "NASDAQ100": "close"})
    vxn = pd.read_csv(vxn_path).rename(columns={"observation_date": "date", "VXNCLS": "level"})
    for frame, field in ((ndx, "close"), (vxn, "level")):
        frame["date"] = pd.to_datetime(frame.date).dt.date
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
        frame.dropna(subset=[field], inplace=True)
    calendar = xc.get_calendar("XNYS", start=ndx.date.min().isoformat(), end=ndx.date.max().isoformat())
    sessions = {x.date() for x in calendar.sessions_in_range(ndx.date.min(), ndx.date.max())}
    audit = dict(missing_ndx_sessions=sorted(x.isoformat() for x in sessions-set(ndx.date)),
                 non_session_ndx_dates=sorted(x.isoformat() for x in set(ndx.date)-sessions),
                 non_session_vxn_dates=sorted(x.isoformat() for x in set(vxn.date)-sessions))
    ndx = ndx.loc[ndx.date.isin(sessions)].reset_index(drop=True)
    vxn = vxn.loc[vxn.date.isin(sessions)].reset_index(drop=True)
    panel = build_close_panel(ndx, vxn, underlying_date="date", underlying_close="close",
                              implied_date="date", implied_close="level")
    require(len(panel) == 6241, "Unexpected Nasdaq panel size")
    within = evaluate_h1_h2(panel)
    spx = pd.read_csv(spx_path, dtype={"origin":str}, float_precision="round_trip")
    joint = panel.merge(spx, on="origin", suffixes=("_ndx", "_spx"), validate="one_to_one")
    joint = joint.loc[joint.origin.between("2007-01-01", "2025-12-31")].copy()
    require(len(joint) == 4780, "Unexpected paired panel size")
    require(joint.origin.is_monotonic_increasing and not joint.origin.duplicated().any(), "Paired origins must be unique and ordered")
    module_path = checkout / "scripts/compare_cross_market_ndx_spx.py"
    spec = importlib.util.spec_from_file_location("historical_paired", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contrasts = []
    for period, lower in (("common_2007_2025", "2007-01-01"), ("post2014", "2014-10-06")):
        sample = joint.loc[joint.origin >= lower]
        for horizon in ("30c", "21t"):
            x = sample[f"vrp_{horizon}"].to_numpy(float)
            y = sample[f"vrp_x_cc_{horizon}"].to_numpy(float)
            difference = x-y
            require(np.isfinite(difference).all(), "Non-finite paired difference")
            bootstrap = []
            for block in (63,21,126):
                rng = np.random.default_rng(1729)
                draws = []
                for _ in range(1000):
                    starts = rng.integers(0, len(sample), size=int(np.ceil(len(sample)/block)))
                    indices = ((starts[:,None]+np.arange(block)) % len(sample)).ravel()[:len(sample)]
                    draws.append(float(difference[indices].mean()))
                require(np.isfinite(draws).all(), "Non-finite bootstrap draw")
                bootstrap.append(dict(block=block, draws=1000, valid_draws=1000, seed=1729,
                    estimate=float(difference.mean()), percentile_ci95=np.quantile(draws,[.025,.975]).tolist(),
                    status="NEW_PARTIAL_REGISTERED_H1_REPLAY_NOT_COMPLETED_H1_H5_FAMILY"))
            contrasts.append(dict(period=period,horizon=horizon,n=len(sample),
                ndx_hac21=checked_mean(x,21),spx_hac21=checked_mean(y,21),
                paired_hac21=checked_mean(difference,21),h1_bootstrap=bootstrap,
                ndx_calibration_hac21=checked_regression(sample[f"rvar_{horizon}"],sample.ivar_ndx,21,np.eye(2),[0.,1.]),
                spx_calibration_hac21=checked_regression(sample[f"rvar_cc_fwd_{horizon}"],sample.ivar_spx,21,np.eye(2),[0.,1.]),
                paired_calibration_hac21=module.paired_calibration(sample,f"rvar_{horizon}",f"rvar_cc_fwd_{horizon}")))
    output = dict(status="FRESH PROVISIONAL H1/H2 REBUILD, NOT ORIGINAL OUTPUT-BYTE REPLAY",
        raw_sources_exact=True, spx_target_status="Fresh reconstructed targets from exact source freeze; original derived byte hash differs",
        registered_market_h1_h5_family_complete=False, holm_adjustment=None,
        holm_reason="No invented subset family; H3-H5 market contrasts and registered bootstrap tests incomplete",
        inputs_sha256={"ext-recovered/NASDAQ100_exact.csv": sha(ndx_path),
                       "ext-recovered/VXNCLS_exact.csv": sha(vxn_path),
                       "prov-rebuilt/interim/40113d6646b0e7b8/targets/bd7a172882ded86f/six_forward_targets.csv": sha(spx_path)},
        source_code_sha256={"ext-delivery/rebuild_paired_h1_h2.py": sha(Path(__file__)),
                            "ext-c/scripts/compare_cross_market_ndx_spx.py": sha(module_path),
                            "ext-c/src/vrp/cross_market.py": sha(checkout / "src/vrp/cross_market.py")},
        environment=dict(python=platform.python_version(),packages={k:importlib.metadata.version(k) for k in ('numpy','pandas','scipy','statsmodels','exchange-calendars')}),
        panel=dict(n=len(panel),first_origin=panel.origin.min(),last_origin=panel.origin.max(),
                   origins_sha256=hashlib.sha256(('\n'.join(panel.origin)+'\n').encode()).hexdigest()),
        source_session_audit=audit,within_ndx_h1_h2=within,paired_contrasts=contrasts,
        limits=['No fresh independent Cboe overlap audit without separately recovered Cboe inputs',
                'No H3-H8 full raw replay or refits in this script',
                'Percentile bootstrap intervals only; no arbitrary bootstrap p-value convention added'])
    args.output.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(panel=output['panel'], source_session_audit=audit,
        paired=[dict(period=r['period'],horizon=r['horizon'],n=r['n'],mean=r['paired_hac21']['mean'],
                     hac_p=r['paired_hac21']['p_value'],bootstrap63=r['h1_bootstrap'][0]) for r in contrasts]),indent=2))


if __name__ == '__main__':
    main()
