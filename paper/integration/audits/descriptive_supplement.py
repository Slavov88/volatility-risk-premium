"""Create protocol-required descriptive tables and figures from private inputs.

Usage: PYTHONPATH=CHECKOUT/src python descriptive_supplement.py SPX_CSV TARGETS_CSV
"""

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
from vrp.summary import summary_statistics

OUT = Path(__file__).resolve().parent.parent
prices_path, targets_path = map(Path, sys.argv[1:])
if (
    hashlib.sha256(prices_path.read_bytes()).hexdigest()
    != "dd7838e8470a5056e99b82dba808bf9df226ced891e0826e4425d55a8d0f544e"
):
    raise ValueError("Unexpected canonical input")
prices = pd.read_csv(prices_path)
targets = pd.read_csv(targets_path, float_precision="round_trip")
returns = np.array([math.log(b / a) for a, b in zip(prices.Close, prices.Close[1:])])
return_dates = pd.to_datetime(prices.Date.iloc[1:])
keep = return_dates <= "2025-12-31"
returns, return_dates = returns[keep], return_dates[keep]
proxy = targets.vrp_x_cc_30c.to_numpy()
plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "pdf.fonttype": 42})


def save(fig, name):
    fig.savefig(
        OUT / "figures" / f"{name}.pdf",
        metadata={"CreationDate": None, "ModDate": None},
    )
    fig.savefig(OUT / "figures" / f"{name}.svg")
    plt.close(fig)


fig, axes = plt.subplots(2, 1, figsize=(6.3, 4.5), layout="constrained")
axes[0].plot(return_dates, 100 * returns, lw=0.35, color="#21536a")
axes[0].set(ylabel="Daily log return (%)", title="A   S&P 500 price-index returns")
axes[1].hist(
    100 * returns,
    bins=np.arange(-13, 12, 0.4),
    density=True,
    color="#9bb7c4",
    edgecolor="white",
    lw=0.3,
)
x = np.linspace(-8, 8, 300)
axes[1].plot(
    x,
    stats.norm.pdf(x, 100 * returns.mean(), 100 * returns.std(ddof=1)),
    color="#7b4b3b",
    lw=1,
    label="Matched Gaussian",
)
axes[1].set(
    xlabel="Daily log return (%)",
    ylabel="Density",
    title="B   Empirical histogram and Gaussian reference",
)
axes[1].legend(frameon=False)
for axis in axes:
    axis.spines[["top", "right"]].set_visible(False)
save(fig, "supplement-returns")

fig, axes = plt.subplots(2, 1, figsize=(6.3, 4.5), layout="constrained")
axes[0].plot(pd.to_datetime(targets.origin), proxy, lw=0.45, color="#21536a")
axes[0].axhline(0, color="grey", lw=0.6)
axes[0].set(
    ylabel="Annualized variance", title="A   Implied minus realized variance proxy"
)
correlation = acf(proxy, nlags=63)
axes[1].stem(
    np.arange(1, 64), correlation[1:], linefmt="#21536a", markerfmt=" ", basefmt="grey"
)
axes[1].set(
    xlabel="Origin lag (sessions)",
    ylabel="Autocorrelation",
    title="B   Primary proxy dependence",
)
for axis in axes:
    axis.spines[["top", "right"]].set_visible(False)
save(fig, "supplement-proxy")
summary = summary_statistics(proxy.tolist())
record = {
    "status": "FRESH_DESCRIPTIVE_COMPUTATION_PROVISIONAL",
    "inputs_sha256": {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [prices_path, targets_path]
    },
    "return_cutoff": "2025-12-31",
    "return_n": len(returns),
    "primary_proxy": summary,
    "primary_proxy_acf_lags_0_to_63": correlation.tolist(),
}
(OUT / "audits/descriptive-supplement.json").write_text(
    json.dumps(record, indent=2) + "\n"
)
