"""Attempt exact, TLS-verified recovery of the pinned NDX/VXN snapshots.

Run with the research environment's requests installed. Raw vendor observations
are written only in the chosen output directory and must not be committed. Appended rows
may be removed only when the retained byte prefix has the original SHA-256.
Revised histories are rejected rather than relabeled as an exact recovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Avoid bytecode writes to the supplied checkout or dependency locations.
sys.dont_write_bytecode = True

import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True, help="cross-market source checkout")
    parser.add_argument("--output", type=Path, required=True, help="directory for recovered CSVs and receipt")
    args = parser.parse_args()
    results = []
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    for name in ("cross_market_sources_v1", "cross_market_volatility_v2"):
        manifest = args.checkout / "data/manifests" / (name + ".json")
        for spec in json.loads(manifest.read_bytes())["sources"]:
            if spec.get("series") not in ("NASDAQ100", "VXNCLS"):
                continue
            result = dict(series=spec["series"], url=spec["url_requested"],
                          expected_sha256=spec["raw_sha256"], expected_bytes=spec["raw_bytes"])
            try:
                response = requests.get(spec["url_requested"], timeout=20)
                response.raise_for_status()
                raw = response.content
                result.update(http_status=response.status_code, received_bytes=len(raw),
                              received_sha256=hashlib.sha256(raw).hexdigest())
                prefix = raw[:spec["raw_bytes"]]
                if hashlib.sha256(prefix).hexdigest() != spec["raw_sha256"]:
                    result["status"] = "REJECTED_NONEXACT_CURRENT_HISTORY"
                else:
                    out.mkdir(exist_ok=True)
                    destination = out / (spec["series"] + "_exact.csv")
                    destination.write_bytes(prefix)
                    result.update(status="RECOVERED_EXACT_HASH", path=str(destination),
                                  appended_bytes_removed=len(raw)-len(prefix))
            except requests.RequestException as error:
                result.update(status="TRANSPORT_UNAVAILABLE", error_type=type(error).__name__,
                              error=str(error))
            results.append(result)
    receipt = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(), tls_verification=True,
                   policy="Accept original SHA-256 only; no vintage substitution or inference from unavailable inputs",
                   sources=results)
    destination = out / "source_recovery_receipt.json"
    destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
