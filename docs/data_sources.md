# Data-source feasibility and decision note

**Tracker task:** W1-08
**Decision date:** 2026-08-10
**Status:** Hierarchy, feasibility, and exact-index acquisition are complete.
The acquisition layer remains in review because validation discrepancies and
the local TLS workaround require review rather than silent acceptance.

## Locked hierarchy

| Research object | Source | Decision | Reason / caveat |
|---|---|---|---|
| VIX history | Cboe historical CSV | Primary | Issuer source with long public history. The exact daily `CLOSE` timestamp across the free history remains an open provenance limitation, not a construction blocker. |
| S&P 500 OHLC | Yahoo Finance `^GSPC` through pinned `yfinance`, `auto_adjust=False` | Primary long-history candidate | Exact price index rather than SPY; supplies OHLC. The persisted CSV is an immutable normalized acquisition snapshot produced from the returned `yfinance` DataFrame, not a byte-identical Yahoo response. Yahoo/yfinance is not an exchange-authoritative feed, so provenance and validation are mandatory. |
| S&P 500 close validation | FRED `SP500` | Validation | S&P Dow Jones-sourced daily market close, limited by FRED to ten years; not used to silently overwrite Yahoo. |
| Engineering fallback | SPY | Engineering-only | ETF tracking, dividends, microstructure, and adjustment differences prevent silent substitution for the index. |
| Short risk-free rate | Undecided | Separate, non-blocking | No tenor or series is locked; this is not required for exact-index OHLC acquisition. |

## Exact-index retrieval contract

- Symbol is exactly `^GSPC`; `auto_adjust=False`, daily interval, no pre/post
  bars, no automated repair, and an inclusive start/exclusive frozen end.
- The executable records the installed `yfinance` version and all request
  parameters. The project pins the reviewed release in `pyproject.toml`.
- A bar whose exchange date equals the current New York date is rejected even
  if the provider returns it. The requested exclusive end cannot be after the
  retrieval's current New York date.
- The returned Yahoo `yfinance` DataFrame is schema-normalized, numerically
  parsed, date-normalized and sorted, then deterministically serialized before
  first persistence. FRED response bytes are persisted as fetched. Both
  artifact types are stored under the UTC retrieval timestamp, written
  immutably, and hashed with SHA-256; the manifest distinguishes them and
  records schema, coverage, missingness, byte counts, source URLs, and
  validation statistics.
- FRED overlap is matched by date. Values differing by more than one index-point
  cent are counted and sampled in the manifest; persisted Yahoo values remain
  unchanged after normalization.
- Acquisition artifacts stay ignored by Git because redistribution rights
  differ. Code, documentation, and compact metadata are the reproducible
  deliverables.

Official/provider documentation:

- Yahoo history page: https://finance.yahoo.com/quote/%5EGSPC/history/
- `yfinance.download`: https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html
- FRED `SP500`: https://fred.stlouisfed.org/series/SP500
- Cboe VIX history: https://www.cboe.com/tradable_products/vix/vix_historical_data/

## Validation boundary

FRED describes `SP500` as the daily index value at market close, normally
4:00 p.m. ET, and supplies ten years of history. Agreement therefore validates
recent Yahoo closes but cannot authenticate pre-overlap Yahoo OHLC. Any
discrepancy is evidence for source review; it is not permission to edit
persisted acquisition values. A licensed index feed remains the escalation
path if validation exposes material inconsistencies.

## Frozen feasibility result

Run at 2026-08-10 17:39:25 UTC with inclusive start 1990-01-01 and exclusive
end 2026-08-10:

| Check | Result |
|---|---|
| Yahoo symbol / software | `^GSPC`; `yfinance==1.5.2`; `auto_adjust=False` |
| Yahoo normalized-snapshot coverage | 9,217 rows, 1990-01-02 through 2026-08-07 |
| Yahoo missingness | 0 missing in Open, High, Low, Close, Adj Close, or Volume |
| Yahoo SHA-256 | `21c3445c8a6db1a09dec9784074defcf58443beba27f8b7333b9f0494854ce51` |
| FRED raw coverage | 2,610 weekday rows, 2016-08-08 through 2026-08-07; 96 missing/holiday close entries |
| FRED usable overlap | 2,514 date-matched non-missing closes |
| Within one-cent tolerance | 2,507 closes |
| Reported discrepancies | 7 closes; maximum absolute difference 5.29 index points; mean absolute difference across all overlap 0.002625 points |
| FRED SHA-256 | `c9f4dfb545c74a81b686ac89f65bb70378b8ceec8f7925d579d0cfbf554c72c7` |

Discrepancy dates and absolute differences after both sources are rounded to
FRED's two-decimal precision: 2021-08-11 (5.29), 2019-08-12 (1.05),
2020-05-11 (0.13), 2018-11-29 (0.04), 2020-10-05 (0.03), 2020-10-02
(0.02), and 2020-10-06 (0.02). These rows remain unchanged in the immutable
Yahoo normalized acquisition snapshot and must be reviewed during data
cleaning; the two largest are
material enough to preclude automatic acceptance.

The final ignored manifest is
`data/raw/2026-08-10T173925Z/gspc_manifest.json`. The local `curl_cffi`
transport could not validate the machine's issuer chain, so this feasibility
acquisition used `verify=False` for Yahoo and records that fact in the ignored
manifest; FRED was fetched with Windows curl and its certificate/revocation handling.
Production refresh should use verified TLS after the local certificate store is
fixed. The code's default transport remains verification-on.
