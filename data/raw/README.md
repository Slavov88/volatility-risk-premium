# Raw data

This directory contains immutable, date-stamped source downloads created by
`vrp-download-samples`. Raw files are ignored by Git because redistribution and
licensing conditions differ by provider.

Each retrieval directory contains a `manifest.json` with source URL, timestamp,
SHA-256 digest, byte count, raw schema, coverage, and missingness. Never edit a
raw file in place. Cleaning belongs in `data/interim/` and must retain a row-loss
and transformation log.

Current source roles:

- Cboe VIX history: primary official VIX source.
- Yahoo Finance `^GSPC`: primary long-history exact-index OHLC candidate,
  acquired with pinned `yfinance` and `auto_adjust=False` by
  `vrp-download-spx`.
- FRED `SP500`: recent close validation for the Yahoo index snapshot. FRED
  discrepancies are reported in `gspc_manifest.json` and never silently used to
  modify Yahoo OHLC.
- U.S. Treasury daily yield curve: primary official rate source, provisional
  three-month tenor choice.
- Nasdaq SPY OHLC: provisional engineering proxy only; it is not final S&P 500
  index OHLC data.

The exact-index command uses an inclusive start and exclusive frozen end. It
rejects any bar dated on or after the retrieval's current New York date. A run
creates these ignored raw files beneath its UTC retrieval timestamp:

```text
YYYY-MM-DDTHHMMSSZ/yahoo/gspc_ohlc_unadjusted.csv
YYYY-MM-DDTHHMMSSZ/fred/sp500_close.csv
YYYY-MM-DDTHHMMSSZ/gspc_manifest.json
```
