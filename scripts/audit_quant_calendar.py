"""Precomparison audit of corrected forward-calendar information sets."""
import json
from datetime import date
from collections import Counter
from vrp.quant_extension import ROOT, OUT, persist, sha
from vrp.quant_calendar import scheduled_forward_sessions, reaggregate_garch
from vrp.calendar import forward_30c_sessions

p = ROOT/"outputs/empirical_h1_h5/v1/garch/normal_expanding/7c3d01aecf3e612f/forecasts.json"
records = json.loads(p.read_bytes())["records"]
changes = []
max_error = 0.
extended_vectors = 0
for r in records:
    scheduled = scheduled_forward_sessions(r["origin"])
    actual = forward_30c_sessions(date.fromisoformat(r["origin"]))
    corrected = reaggregate_garch(r)
    extended_vectors += int(len(r["daily_decimal_variances"]) < len(scheduled))
    if scheduled != actual:
        changes.append({"origin": r["origin"], "extra_scheduled_sessions": [d.isoformat() for d in scheduled if d not in actual],
                        "actual_count": len(actual), "scheduled_count": len(scheduled), "v1": r["garch_30c"], "v2": corrected})
    else:
        max_error = max(max_error, abs(corrected-r["garch_30c"]))
assert max_error < 1e-14
result = {"status": "PASSED_SCHEDULED_CALENDAR_PRECOMPARISON_AUDIT", "cached_sha256": sha(p),
          "origins": len(records), "changed_origins": len(changes),
          "analytically_extended_vectors": extended_vectors,
          "extra_future_dates": dict(Counter(d for c in changes for d in c["extra_scheduled_sessions"])),
          "unaffected_mapping_max_error": max_error, "changes": changes}
persist(OUT/"calendar_audit.json", result)
print({k:v for k,v in result.items() if k != "changes"})
