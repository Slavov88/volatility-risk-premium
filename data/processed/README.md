# Processed data

This directory contains reproducibly generated cleaned panels, return series, realized-variance targets, forecast panels, and analysis-ready datasets.

Generated data files are ignored by Git. They must be rebuildable from immutable local acquisitions plus version-controlled code and manifests.

Every processing stage must log row losses, transformations, source-artifact hashes, and any identified data corrections. Manual spreadsheet editing of processed research data is prohibited.


## Mandatory production origin-panel gate

Do not call the lightweight alignment helper on unverified provider data for
confirmatory research. Build the origin panel only from accepted, immutable
acquisitions with locked windows and verified hashes:

```bash
vrp-build-verified-panel \
  --raw-root data/raw \
  --spx-manifest <SPX_manifest_path_relative_to_raw_root> \
  --vix-manifest <VIX_manifest_path_relative_to_raw_root> \
  --processed-root data/processed
```

The builder independently recomputes XNYS source-quality checks, replays VIX
normalization from the verified raw Cboe bytes, rejects changed source hashes,
and writes a reproducible immutable panel plus a row-loss/provenance manifest.
It excludes 2026 support rows from forecast origins and does not compute
returns, realized variance, volatility risk premia, or forecast results.
