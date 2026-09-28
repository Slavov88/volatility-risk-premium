# Raw data

This directory contains local immutable acquisition artifacts. Raw/provider data are ignored by Git because redistribution and licensing conditions differ by provider. The only tracked data exception is the small W1-08 access-test set under `samples/w1_08/`; those files are feasibility evidence, not a production freeze.

## Canonical source roles

- **Cboe VIX history:** primary official VIX source.
- **Yahoo Finance `^GSPC`:** sole S&P 500 price-index OHLC source, acquired through pinned `yfinance` with `auto_adjust=False`. FRED `SP500` is not a validation source.
- **FRED / Federal Reserve H.15 short Treasury yields:** Track A rate source. The one-month constant-maturity series `DGS1MO` is preferred when it is available and maturity-matched.
- **Nasdaq SPY:** legacy engineering proxy only. It is not final S&P 500 index data.

The old feasibility utility's three-month Treasury choice is provisional and does not override the final Track A rate rule.

## Storage contract

A production acquisition directory should contain immutable artifacts such as:

```text
YYYY-MM-DDTHHMMSSZ/yahoo/gspc_ohlc_unadjusted.csv
YYYY-MM-DDTHHMMSSZ/gspc_manifest.json
```

The Yahoo CSV is a deterministic project-level acquisition snapshot created from the `yfinance` DataFrame after schema/numeric/date normalization; it is not a byte-identical Yahoo network response.

Never edit an acquisition artifact in place. Cleaning and target construction belong in code and produce data under `data/processed/`.

## Production-freeze requirements

The final core acquisition must:

1. cover forecast origins through 2025-12-31 and retain S&P 500 target-support observations through 2026-02-02 (`--end-exclusive 2026-02-03`);
2. mark post-2025 S&P observations as outcome support only and prevent them from becoming forecast origins or predictor/training observations;
3. use verified TLS/certificate checking;
4. record retrieval time, source URLs, request parameters, software versions, schema, coverage, missingness, byte counts, and hashes;
5. copy a sanitized manifest into `data/manifests/` for version control.

The earlier feasibility run that required `verify=False` for Yahoo remains historical evidence only and must not become the final core-data freeze.
