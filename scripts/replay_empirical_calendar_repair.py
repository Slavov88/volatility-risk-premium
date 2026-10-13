"""Repeat all cache verification/inference and require identical numeric outputs."""
import json
import vrp.empirical_calendar_repair as repair
from vrp.provisional_analysis import persist
from vrp.quant_extension import sha

original_path=repair.OUT/"corrected_results.json"
original=json.loads(original_path.read_bytes())
identity={}


def checked_persist(path,obj):
    if path==original_path:
        expected=dict(original);actual=dict(obj)
        old=expected.pop("implementation");new=actual.pop("implementation")
        if old["sources_sha256_lf"]!=new["sources_sha256_lf"]:
            raise ValueError("Repair producer source changed during replay")
        if expected!=actual:raise ValueError("Full corrected inference replay differs")
        identity.update({"original_commit":old["commit"],"replay_commit":new["commit"]})
        return sha(original_path)
    return persist(path,obj)


repair.persist=checked_persist
repair.run()
evidence={"status":repair.STATUS,"all_numeric_fields_exact":True,"all_forecast_JSON_and_comparison_CSV_bytes_exact":True,
          "producer_source_hashes_exact":True,"original_results_sha256":sha(original_path),**identity}
persist(repair.OUT/"deterministic_replay.json",evidence)
print(evidence)
