# Raw data

This directory contains local immutable acquisition artifacts. Raw/provider data are ignored by Git because redistribution and licensing conditions differ by provider.

## Canonical source roles

- **Cboe VIX history:** primary official VIX source.
- **Yahoo Finance `^GSPC`:** primary long-history S&P 500 price-index OHLC candidate, acquired through pinned `yfinance` with `auto_adjust=False`.
- **FRED `SP500`:** recent close validation for the Yahoo index snapshot. Discrepancies are reported and never silently used to overwrite Yahoo OHLC.
- **FRED / Federal Reserve H.15 short Treasury yields:** Track A rate source. The one-month constant-maturity series is preferred when it is available and maturity-matched; otherwise use the nearest defensible short maturity.
- **Nasdaq SPY:** legacy engineering proxy only. It is not final S&P 500 index data.

The old feasibility utility's three-month Treasury choice is provisional and does not override the final Track A rate rule.

## Storage contract

A production acquisition directory should contain immutable artifacts such as:

```text
YYYY-MM-DDTHHMMSSZ/yahoo/gspc_ohlc_unadjusted.csv
YYYY-MM-DDTHHMMSSZ/fred/sp500_close.csv
YYYY-MM-DDTHHMMSSZ/gspc_manifest.json
```

The Yahoo CSV is a deterministic project-level acquisition snapshot created from the `yfinance` DataFrame after schema/numeric/date normalization; it is not a byte-identical Yahoo network response. FRED response bytes are preserved as fetched.

Never edit an acquisition artifact in place. Cleaning and target construction belong in code and produce data under `data/processed/`.

## Production-freeze requirements

The final core acquisition must:

1. cover forecast origins through 2025-12-31 and retain S&P 500 target-support observations through 2026-02-02 (`--end-exclusive 2026-02-03`);
2. mark post-2025 S&P observations as outcome support only and prevent them from becoming forecast origins or predictor/training observations;
3. use verified TLS/certificate checking;
4. record retrieval time, source URLs, request parameters, software versions, schema, coverage, missingness, byte counts, hashes, and validation statistics;
5. investigate the material Yahoo/FRED close discrepancies documented in `docs/data_sources.md` before the cleaned panel is frozen;
6. copy a sanitized manifest into `data/manifests/` for version control.

The earlier feasibility run that required `verify=False` for Yahoo remains historical evidence only and must not become the final core-data freeze.
