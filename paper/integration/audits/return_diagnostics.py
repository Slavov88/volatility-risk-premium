"""Descriptive return diagnostics, by the forecast origin cutoff and initial split."""

from pathlib import Path
import hashlib
import json
import math
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import acf
from vrp.recursive_garch import diagnostics

OUT = Path(__file__).resolve().parent.parent
p = Path(sys.argv[1])
if (
    hashlib.sha256(p.read_bytes()).hexdigest()
    != "dd7838e8470a5056e99b82dba808bf9df226ced891e0826e4425d55a8d0f544e"
):
    raise ValueError("Expected the frozen Yahoo acquisition snapshot")
prices = pd.read_csv(p)
logret = np.array([math.log(b / a) for a, b in zip(prices.Close, prices.Close[1:])])
dates = prices.Date.iloc[1:].to_numpy()
by_sample = {}
for cut in ["2006-12-31", "2025-12-31"]:
    sample = logret[dates <= cut]
    by_sample[cut] = {"n": len(sample), **diagnostics(sample)}
print(json.dumps(by_sample, indent=2, sort_keys=True, allow_nan=False))

# A restricted quantile grid is sufficient to display tail shape.
probs = np.r_[0.001, 0.005, np.arange(0.01, 1, 0.01), 0.995, 0.999]
normal = stats.norm.ppf(probs)
standardized = (sample - np.mean(sample)) / np.std(sample, ddof=1)
fig, (qq, corr) = plt.subplots(1, 2, figsize=(6.4, 2.5), layout="constrained")
qq.plot(normal, np.quantile(standardized, probs), ".", ms=3, color="#21536a")
qq.plot([-3.2, 3.2], [-3.2, 3.2], ls="--", color="#757575", lw=0.9)
qq.set(
    xlabel="Gaussian quantile",
    ylabel="Standardized return quantile",
    title="A   Return tails",
)
for data, label, style in [
    (sample, "Returns", "o-"),
    (sample**2, "Squared returns", "s--"),
]:
    corr.plot(
        np.arange(1, 22), acf(data, nlags=21)[1:], style, ms=2.5, lw=0.9, label=label
    )
corr.axhline(0, color="#757575", lw=0.8)
corr.legend(fontsize=8, frameon=False)
corr.set(
    xlabel="Lag (sessions)",
    ylabel="Sample autocorrelation",
    title="B   Serial dependence",
)
for axis in (qq, corr):
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(labelsize=8)
fig.savefig(
    OUT / "figures" / "return-diagnostics.pdf",
    metadata={
        "CreationDate": None,
        "ModDate": None,
        "Creator": "VRP research integration",
    },
)

fig.savefig(OUT / "figures" / "return-diagnostics.svg", metadata={"Date":None})
