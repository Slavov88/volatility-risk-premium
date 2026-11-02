"""Compare fresh refit aggregates with committed aggregates, without a tolerance test.

Usage: python compare_fresh.py CHECKOUT FRESH_DIRECTORY OUTPUT
The committed manifest stores mask hashes, not origin lists. Matching hashes and
counts identify identical serialized masks, subject to the hash's assumptions.
"""

import hashlib
import json
import sys
from pathlib import Path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_leaves(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from numeric_leaves(item, f"{prefix}/{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from numeric_leaves(item, f"{prefix}/{index}")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield prefix, value


def cell_key(cell):
    return tuple(cell[k] for k in ("variant", "horizon", "family", "period", "mask"))


def main():
    root, fresh, output = map(Path, sys.argv[1:])
    historical_path = root / "data/manifests/empirical_calendar_repair_results_v1.json"
    historical = json.loads(historical_path.read_text())
    reference = {cell_key(c): c["corrected"] for c in historical["analyses"]}
    cells, changes, maxima = [], [], {}
    files = sorted(fresh.glob("*_results.json"))
    for file in files:
        run = json.loads(file.read_text())
        for cell in run["analyses"]:
            key = cell_key(cell)
            current, prior = cell["fresh_refit"], reference[key]
            # Origin lists are present only in the new run, not in the manifest.
            current_numbers = dict(
                numeric_leaves(
                    {k: v for k, v in current.items() if k != "common_origins"}
                )
            )
            prior_numbers = dict(numeric_leaves(prior))
            if current_numbers.keys() != prior_numbers.keys():
                raise ValueError(f"Numeric fields differ for {key}")
            differences = {
                p: abs(current_numbers[p] - prior_numbers[p]) for p in current_numbers
            }
            for path, difference in differences.items():
                maxima[path] = max(maxima.get(path, 0), difference)
                if "p_value" in path and (current_numbers[path] < 0.05) != (
                    prior_numbers[path] < 0.05
                ):
                    changes.append(
                        {
                            "cell": key,
                            "field": path,
                            "fresh": current_numbers[path],
                            "committed": prior_numbers[path],
                        }
                    )
            mask_match = (
                current["n_common"] == prior["n_common"]
                and current["common_origins_sha256"] == prior["common_origins_sha256"]
            )
            cells.append(
                {
                    "cell": key,
                    "n": current["n_common"],
                    "mask_hash_and_count_match": mask_match,
                    "max_absolute_numeric_difference": max(differences.values()),
                    "numeric_differences": differences,
                    "rmse": {
                        m: current["metrics"][m]["rmse"] for m in current["metrics"]
                    },
                    "primary_h3": current["tests"][0]["squared_error"]["vix_vs_garch"],
                    "primary_h4": current["tests"][0]["h4"],
                }
            )
    if len(cells) != 72 or set(map(tuple, (c["cell"] for c in cells))) != set(
        reference
    ):
        raise ValueError("Expected exactly the 72 committed cells")
    receipt = {
        "comparison_kind": "FRESH_REFIT_NUMERICAL_COMPARISON_NOT_CACHE_REPLAY",
        "historic_aggregate_sha256": sha256(historical_path),
        "fresh_files_sha256": {p.name: sha256(p) for p in files},
        "cells": cells,
        "cell_count": len(cells),
        "all_mask_hashes_and_counts_match": all(
            c["mask_hash_and_count_match"] for c in cells
        ),
        "decision_changes_5pct": changes,
        "max_abs_error_by_numeric_path": maxima,
        "fresh_fit_counts": {
            p.name: {
                k: json.loads(p.read_text())[k]
                for k in ("completed", "failed", "cache_reuse")
            }
            for p in files
        },
    }
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in receipt.items()
                if k not in ("cells", "max_abs_error_by_numeric_path")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
