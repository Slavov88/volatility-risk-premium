"""Paired Nasdaq/S&P comparison on common 2007-2025 forecast origins."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
from scipy.stats import chi2
from scipy.stats import norm

from vrp.inference import newey_west_mean, fit_hac_ols
from vrp.provisional_analysis import persist

ROOT = Path(__file__).resolve().parents[1]
NDX = ROOT / "outputs/cross_market/v1/ndx_vxn_targets.csv"
SPX_TARGET_MANIFEST = ROOT / "data/manifests/2026-10-13_provisional_targets.json"
SPX_H12 = ROOT / "outputs/empirical_h1_h5/v1/h1_h2.json"
OUT = ROOT / "outputs/cross_market/v1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def paired_calibration(sample: pd.DataFrame, ndx_target: str, spx_target: str) -> dict:
    """Stack paired markets and estimate market interactions with date-clustered NW HAC."""
    n = len(sample)
    xn = sample.ivar_ndx.to_numpy(float); xs = sample.ivar_spx.to_numpy(float)
    yn = sample[ndx_target].to_numpy(float); ys = sample[spx_target].to_numpy(float)
    design = np.empty((2*n, 4), float)
    design[0::2] = np.column_stack([np.ones(n), xs, np.zeros(n), np.zeros(n)])
    design[1::2] = np.column_stack([np.ones(n), xn, np.ones(n), xn])
    response = np.empty(2*n, float); response[0::2] = ys; response[1::2] = yn
    beta = np.linalg.lstsq(design, response, rcond=None)[0]
    score = design * (response-design@beta)[:, None]
    grouped = score[0::2] + score[1::2]
    meat = grouped.T @ grouped
    for lag in range(1, 22):
        cross = grouped[lag:].T @ grouped[:-lag]
        meat += (1-lag/22)*(cross+cross.T)
    bread = np.linalg.inv(design.T @ design)
    covariance = bread @ meat @ bread * (2*n)/(2*n-4)
    se = np.sqrt(np.diag(covariance))
    return {"coefficients_spx_alpha_beta_then_ndx_minus_spx_alpha_beta":beta.tolist(),
            "se_date_clustered_hac21":se.tolist(),"p_values_normal":(2*norm.sf(np.abs(beta/se))).tolist(),
            "ndx_minus_spx_alpha":float(beta[2]),"ndx_minus_spx_beta":float(beta[3]),
            "ndx_minus_spx_alpha_se":float(se[2]),"ndx_minus_spx_beta_se":float(se[3]),
            "ndx_minus_spx_alpha_p":float(2*norm.sf(abs(beta[2]/se[2]))),
            "ndx_minus_spx_beta_p":float(2*norm.sf(abs(beta[3]/se[3]))),
            "independent_score_sandwich":"DATE-CLUSTERED BARTLETT HAC, 21 origin lags"}


def compare() -> dict:
    ndx = pd.read_csv(NDX, dtype={"origin": str}, float_precision="round_trip")
    spec = json.loads(SPX_TARGET_MANIFEST.read_bytes())["outputs"]["six_forward_targets.csv"]
    spx_path = ROOT / "data/processed" / spec["relative_path"]
    if sha(spx_path.read_bytes()) != spec["sha256"]:
        raise ValueError("Frozen S&P target hash mismatch")
    spx = pd.read_csv(spx_path, dtype={"origin": str}, float_precision="round_trip")
    joint = ndx.merge(spx, on="origin", suffixes=("_ndx", "_spx"), validate="one_to_one")
    joint = joint.loc[joint.origin.between("2007-01-01", "2025-12-31")].copy()
    if len(joint) < 4000 or joint.origin.duplicated().any() or not joint.origin.is_monotonic_increasing:
        raise ValueError("Common evaluation panel incomplete or unordered")
    periods = {"full_2007_2025": "2007-01-01", "post_2014": "2014-10-06"}
    h1 = []
    for period, lower in periods.items():
        sample = joint.loc[joint.origin >= lower]
        for horizon in ("30c", "21t"):
            x = sample[f"vrp_{horizon}"].to_numpy(float)
            y = sample[f"vrp_x_cc_{horizon}"].to_numpy(float)
            if not np.isfinite(x).all() or not np.isfinite(y).all():
                raise ValueError("Common H1 series contains missing observations")
            h1.append({"period": period, "horizon": horizon, "n": len(sample),
                "ndx_mean_hac21": newey_west_mean(x, 21), "spx_mean_hac21": newey_west_mean(y, 21),
                "paired_ndx_minus_spx_hac21": newey_west_mean(x-y, 21),
                "ndx_positive_share": float(np.mean(x > 0)), "spx_positive_share": float(np.mean(y > 0))})
    calibrations = []
    for period, lower in periods.items():
        sample = joint.loc[joint.origin >= lower]
        for horizon, target in (("30c", "rvar_cc_fwd_30c"), ("21t", "rvar_cc_fwd_21t")):
            ndx_target = f"rvar_{horizon}"
            fits = {}
            for market, suffix in (("ndx", "_ndx"), ("spx", "_spx")):
                y = sample[ndx_target if market == "ndx" else target].to_numpy(float)
                x = sample["ivar"+suffix].to_numpy(float)
                fit = fit_hac_ols(y, x, maxlags=21)
                fits[market] = {"n": len(y), "alpha": float(fit.params[0]), "beta": float(fit.params[1]),
                                "alpha_se": float(fit.bse[0]), "beta_se": float(fit.bse[1]),
                                "alpha_beta_cov": float(fit.cov_params()[0,1]), "wald_p_alpha0_beta1": None}
                restriction = np.eye(2)
                delta = np.array([fit.params[0], fit.params[1]-1.])
                fits[market]["wald_p_alpha0_beta1"] = float(chi2.sf(
                    float(delta @ np.linalg.solve(restriction @ fit.cov_params() @ restriction.T, delta)), 2))
            calibrations.append({"period":period,"horizon":horizon,"n":len(sample),"ndx":fits["ndx"],"spx":fits["spx"],
                "paired_calibration_contrast":paired_calibration(sample, ndx_target, target)})
    commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    return {"status":"EXPLORATORY PAIRED CROSS-MARKET INFERENCE — PROVISIONAL / PENDING INDEPENDENT REVIEW",
      "markets":"NASDAQ-100/VXN and S&P 500/VIX","period":"common eligible origins 2007-01-01 through 2025-12-31; post-2014 lower bound 2014-10-06",
      "n_common_full":len(joint),"first_origin":joint.origin.iloc[0],"last_origin":joint.origin.iloc[-1],
      "h1_paired":h1,"h2_calibration":calibrations,
      "source_hashes":{"ndx_targets":sha(NDX.read_bytes()),"spx_targets":spec["sha256"],"spx_h1_h2":sha(SPX_H12.read_bytes())},
      "code_commit":commit,
      "inference":"HAC Newey-West lag 21 on same-origin paired series; paired slope contrast is a HAC regression on market differences; these are exploratory market contrasts, not independent replication across all global equity markets."}


def main() -> None:
    result = compare()
    print(persist(OUT / "ndx_spx_paired_inference_v3.json", result), flush=True)
    print(json.dumps({"n":result["n_common_full"],"h1":result["h1_paired"],"h2":result["h2_calibration"]},indent=2))


if __name__ == "__main__":
    main()
