"""Build the paper's exhibits from versioned public numerical evidence."""
from pathlib import Path
import csv
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DOC = ROOT / "docs/h1_results.md"
CORRECTED = ROOT / "data/manifests/empirical_calendar_repair_results_v1.json"

def verify(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Changed source: {path}")

def save_table(name, rows):
    with (OUT / "tables" / name).open("w", newline="") as handle:
        table = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        table.writeheader()
        table.writerows(rows)

def mean_estimates():
    rows = []
    for line in DOC.read_text().splitlines():
        fields = [field.strip() for field in line.strip("|").split("|")]
        if len(fields) != 10 or fields[3] != "vrp_x":
            continue
        subset, family, horizon, _, count, lag, mean, se, ci, p = fields
        lo, hi = json.loads(ci)
        rows.append(dict(subset=subset, estimator=family, horizon=horizon,
                         n=int(count), lag=int(lag), mean=float(mean),
                         se=float(se), lo=lo, hi=hi, p=float(p)))
    if len(rows) != 72:
        raise ValueError(f"Unexpected H1 rows: {len(rows)}")
    return rows

def loss_estimates():
    rows, encompassing = [], []
    for cell in json.loads(CORRECTED.read_text())["analyses"]:
        meta = {key: cell[key] for key in ("family", "horizon", "mask", "period", "variant")}
        result = cell["corrected"]
        for test in result["tests"]:
            for pair, loss in test["squared_error"].items():
                first, second = pair.split("_vs_")
                m = result["metrics"]
                assert abs(m[first]["rmse"]**2 - m[second]["rmse"]**2 - loss["mean"]) < 1e-12
                rows.append(dict(**meta, n=result["n_common"], lag=test["lag"], pair=pair,
                    mean=loss["mean"], se=loss["standard_error"],
                    lo=loss["ci_lower"], hi=loss["ci_upper"], p=loss["p_value"],
                    holm_p=loss.get("holm_p_value", "")))
            h4 = test["h4"]
            for index, term in enumerate(("intercept", "vix", "garch")):
                encompassing.append(dict(**meta, n=result["n_common"], lag=test["lag"], term=term,
                    coefficient=h4["coefficients"][index], se=h4["se"][index],
                    lo=h4["ci95"][index][0], hi=h4["ci95"][index][1],
                    p=h4["p_values"][index], r_squared=h4["r_squared"]))
    return rows, encompassing

def interval_plot(rows, labels, centers, xlabel, name, scale=1):
    fig, ax = plt.subplots(figsize=(6.1, 0.43*len(rows)+1.05))
    for i, (row, key) in enumerate(zip(rows, centers)):
        y = len(rows) - i - 1
        if y % 2 == 0:
            ax.axhspan(y - 0.48, y + 0.48, color="#f1f4f5", zorder=0)
        center, lo, hi = [scale * row[k] for k in (key, "lo", "hi")]
        ax.errorbar(center, y, xerr=[[center-lo], [hi-center]], fmt="o",
                    color="#21536a", elinewidth=1.6, capsize=3, markersize=5.4)
    ax.set_yticks(range(len(labels)), labels[::-1])
    ax.set_ylim(-0.55, len(labels)-0.45)
    ax.axvline(0, color="#676767", ls="--", lw=0.9)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.set_xlabel(xlabel, labelpad=6)
    fig.tight_layout()
    fig.savefig(OUT / "figures" / (name + ".pdf"),
                metadata={"CreationDate": None, "ModDate": None, "Creator": "VRP research integration"})
    plt.close(fig)

def match(rows, **criteria):
    matches = [r for r in rows if all(r[k] == v for k,v in criteria.items())]
    if len(matches) != 1:
        raise ValueError(f"Expected a unique match: {criteria}")
    return matches[0]

def main():
    verify(DOC, "f24b52bde2911c4eb14b8e13864f525ec93286a70a91aaba0f20a55fcd5e4e8f")
    verify(CORRECTED, "67287e3c9e572ec3583dd43b0b45f16658d61a65452a8a97bd8158e432b2ae6b")
    (OUT / "tables").mkdir(exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":9, "pdf.fonttype":42})
    h1 = mean_estimates()
    losses, h4 = loss_estimates()
    save_table("h1-robustness.csv", h1)
    save_table("corrected-h3-contrasts.csv", losses)
    save_table("corrected-h4-encompassing.csv", h4)
    choices = [("full","30c",21),("post2003","30c",21),("post2014","30c",21),
               ("post2014","30c_nonoverlap",0),("full","21t",20)]
    rows = [match(h1, estimator="cc", subset=s, horizon=h, lag=l) for s,h,l in choices]
    interval_plot(rows, ["Full sample • 30 calendar days", "From 2004 • 30 calendar days",
                    "From Oct. 2014 • 30 calendar days", "From Oct. 2014 • non-overlapping",
                    "Full sample • 21 trading days"], ["mean"]*len(rows),
                    "Mean implied minus realized variance (annualized decimal units)", "mean-premium")
    rows = []
    for period in ("full", "post2014"):
        for variant in ("normal_expanding","t_expanding","normal_rolling5y"):
            rows.append(match(losses, period=period, variant=variant, horizon="30c", family="cc",
                              mask="overlapping", lag=21, pair="vix_vs_garch"))
    interval_plot(rows, ["2007–25 • Gaussian expanding","2007–25 • Student-t expanding",
                    "2007–25 • Gaussian rolling","Oct. 2014–25 • Gaussian expanding",
                    "Oct. 2014–25 • Student-t expanding","Oct. 2014–25 • Gaussian rolling"],
                    ["mean"]*len(rows), "VIX minus GARCH squared loss (× 1,000)", "forecast-loss", scale=1000)

if __name__ == "__main__":
    main()
