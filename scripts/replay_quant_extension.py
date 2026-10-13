"""Full deterministic replay: refuse changed forecasts, scores or trade logs."""
import json
from vrp.quant_extension import OUT, source_panel, run_h6, persist, sha
from vrp.quant_variance import run_h7
from vrp.quant_portfolio import run_h8

panel = source_panel()
evidence = {}
for phase, runner in [("h6", lambda: run_h6(panel)), ("h7", lambda: run_h7(panel)), ("h8", run_h8)]:
    original = json.loads((OUT/f"{phase}.json").read_bytes())
    rerun = runner()
    old_identity = original.pop("implementation"); new_identity = rerun.pop("implementation")
    if old_identity["sources_sha256_lf"] != new_identity["sources_sha256_lf"]:
        raise ValueError(f"Replay implementation changed: {phase}")
    if original != rerun:
        raise ValueError(f"Deterministic numeric replay failed: {phase}")
    evidence[phase] = {"original_sha256": sha(OUT/f"{phase}.json"), "all_numeric_fields_identical": True,
                       "all_immutable_csv_bytes_identical": True, "source_hashes_identical": True,
                       "original_commit": old_identity["commit"], "replay_commit": new_identity["commit"]}
persist(OUT/"deterministic_replay.json", evidence)
print(evidence)
