"""Independent arithmetic audit of committed SPX aggregates. Run from any directory.

Usage: python audit_core_results.py PATH_TO_CHECKOUT
No downloads, provider data, estimation code, or third-party packages are used.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist


def check(actual, expected):
    if not math.isclose(actual, expected, abs_tol=2e-14, rel_tol=2e-11):
        raise ValueError(f"Expected {expected!r}, obtained {actual!r}")


def normal_inference(mean, se, bounds, p):
    z = NormalDist().inv_cdf(0.975)
    check(bounds[0], mean - z * se)
    check(bounds[1], mean + z * se)
    check(p, math.erfc(abs(mean / se) / math.sqrt(2)))


def mean_inference(result):
    normal_inference(
        result["mean"],
        result["standard_error"],
        [result["ci_lower"], result["ci_upper"]],
        result["p_value"],
    )
    check(result["mean"] / result["standard_error"], result["t_statistic"])


def regression(result):
    for values in zip(
        result["coefficients"],
        result["se"],
        result["ci95"],
        result["p_values"],
        strict=True,
    ):
        normal_inference(*values)


def audit(root):
    manifests = root / "data" / "manifests"

    def load(name):
        return json.loads((manifests / (name + ".json")).read_bytes())

    base = load("2026-10-13_h1_h5_execution_v2")["primary_results"]
    corrected = load("empirical_calendar_repair_results_v1")
    descriptive = load("2026-10-13_descriptive_statistics")["subsets"]
    full = descriptive["full_sample"]
    iv, rv, gap = (full[k] for k in ("ivar", "rvar_cc_fwd_30c", "vrp_x_cc_30c"))
    h1, h2, h5 = (base[k] for k in ("h1", "h2", "h5"))
    check(h1["n_obs"], gap["n_obs"])
    check(h1["mean"], iv["mean"] - rv["mean"])
    check(h1["median"], gap["median"])
    check(h1["proportion_positive"], gap["proportion_positive"])
    mean_inference(h1)
    covariance = (iv["std"] ** 2 + rv["std"] ** 2 - gap["std"] ** 2) / 2
    slope = covariance / iv["std"] ** 2
    intercept = rv["mean"] - slope * iv["mean"]
    r_squared = (covariance / (iv["std"] * rv["std"])) ** 2
    for value, expected in zip(
        [intercept, slope, r_squared],
        [*h2["coefficients"], h2["r_squared"]],
        strict=True,
    ):
        check(value, expected)
    regression(h2)
    check(math.exp(-h2["wald"]["statistic"] / 2), h2["wald"]["p_value"])
    expansion, recession = (h5["regimes"][name] for name in ("expansion", "recession"))
    check(expansion["mean"], h5["coefficients"][0])
    check(recession["mean"] - expansion["mean"], h5["coefficients"][1])
    check(expansion["n"] + recession["n"], h1["n_obs"])
    check(
        (expansion["mean"] * expansion["n"] + recession["mean"] * recession["n"])
        / h1["n_obs"],
        h1["mean"],
    )
    regression(h5)
    check((h5["coefficients"][1] / h5["se"][1]) ** 2, h5["wald"]["statistic"])

    counts = {
        "corrected_cells": 0,
        "fixed21_identical_cells": 0,
        "lag_cells": 0,
        "classification_comparisons": 0,
    }
    seen = set()
    changes = 0
    for cell in corrected["analyses"]:
        descriptor = tuple(
            cell[key] for key in ("variant", "family", "horizon", "period", "mask")
        )
        if descriptor in seen:
            raise ValueError(f"Duplicate cell {descriptor}")
        seen.add(descriptor)
        counts["corrected_cells"] += 1
        old, new = cell["original_control"], cell["corrected"]
        if new["common_origins_sha256"] != old["common_origins_sha256"]:
            raise ValueError(f"Common mask differs in {descriptor}")
        if cell["horizon"] == "21t":
            if new != old:
                raise ValueError(f"Changed fixed-horizon result in {descriptor}")
            counts["fixed21_identical_cells"] += 1
        metrics = new["metrics"]
        n = new["n_common"]
        for metric in metrics.values():
            check(metric["n"], n)
        if cell["mask"] == "overlapping":
            subset = descriptive[
                "oos_from_2007" if cell["period"] == "full" else "post_2014_10_06"
            ]
            prefix = f"{cell['family']}_{cell['horizon']}"
            vix_gap = subset["vrp_x_" + prefix]
            target = subset[f"rvar_{cell['family']}_fwd_{cell['horizon']}"]
            check(n, vix_gap["n_obs"])
            check(metrics["vix"]["bias_forecast_minus_actual"], vix_gap["mean"])
            check(
                metrics["vix"]["rmse"] ** 2,
                vix_gap["mean"] ** 2 + (n - 1) / n * vix_gap["std"] ** 2,
            )
            # Engineering check from OLS normal equations with an intercept.
            a, b, g = new["tests"][0]["h4"]["coefficients"]
            gbar = target["mean"] + metrics["garch"]["bias_forecast_minus_actual"]
            check(target["mean"], a + b * subset["ivar"]["mean"] + g * gbar)
        expected_lags = (
            [0]
            if cell["mask"] == "nonoverlap"
            else [21, 42, 63] if cell["horizon"] == "30c" else [20, 10, 21, 42]
        )
        if [row["lag"] for row in new["tests"]] != expected_lags:
            raise ValueError(f"Incorrect lag family in {descriptor}")
        for original, test in zip(old["tests"], new["tests"], strict=True):
            counts["lag_cells"] += 1
            results = test["squared_error"]
            for pair, loss in results.items():
                first, second = pair.split("_vs_")
                check(loss["n_obs"], n)
                check(
                    loss["mean"],
                    metrics[first]["rmse"] ** 2 - metrics[second]["rmse"] ** 2,
                )
                mean_inference(loss)
            secondary = sorted(
                (results[p] for p in ("vix_vs_naive", "garch_vs_naive")),
                key=lambda x: x["p_value"],
            )
            smaller = min(1.0, 2 * secondary[0]["p_value"])
            check(smaller, secondary[0]["holm_p_value"])
            check(max(smaller, secondary[1]["p_value"]), secondary[1]["holm_p_value"])
            qlike = test["qlike_vix_vs_garch"]
            check(qlike["mean"], metrics["vix"]["qlike"] - metrics["garch"]["qlike"])
            mean_inference(qlike)
            regression(test["h4"])

            def decision_pvalues(row):
                return [
                    row["squared_error"]["vix_vs_garch"]["p_value"],
                    *(
                        row["squared_error"][pair]["holm_p_value"]
                        for pair in ("vix_vs_naive", "garch_vs_naive")
                    ),
                    row["qlike_vix_vs_garch"]["p_value"],
                    *row["h4"]["p_values"],
                ]

            for p_old, p_new in zip(
                decision_pvalues(original), decision_pvalues(test), strict=True
            ):
                counts["classification_comparisons"] += 1
                changes += (p_old < 0.05) != (p_new < 0.05)
    decision = load("empirical_calendar_repair_decision_audit_v1")
    check(changes, len(decision["changed_decisions"]))
    check(counts["classification_comparisons"], decision["comparisons_checked"])
    if (len(seen), counts["fixed21_identical_cells"]) != (72, 36):
        raise ValueError("Incomplete registered cells")
    inputs = (
        "2026-10-13_h1_h5_execution_v2",
        "2026-10-13_descriptive_statistics",
        "empirical_calendar_repair_results_v1",
        "empirical_calendar_repair_decision_audit_v1",
    )
    return {
        "audit": "Committed aggregates and report arithmetic; freeze and observations not replayed",
        "inputs_sha256": {
            name: hashlib.sha256(
                (manifests / (name + ".json")).read_bytes()
            ).hexdigest()
            for name in inputs
        },
        "h1_mean_from_moments": iv["mean"] - rv["mean"],
        "h2_from_moments": {
            "intercept": intercept,
            "slope": slope,
            "r_squared": r_squared,
        },
        "h5_recession_difference_from_groups": recession["mean"] - expansion["mean"],
        **counts,
        "changed_classifications": changes,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    print(json.dumps(audit(parser.parse_args().checkout), sort_keys=True, indent=2))
