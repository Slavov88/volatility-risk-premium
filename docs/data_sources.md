# Data-source feasibility and decision note

**Tracker task:** W1-08  
**Initial feasibility date:** 2026-08-10  
**Methodological reconciliation:** 2026-08-26  
**Technical sample-tail amendment:** 2026-08-27  
**Status:** source hierarchy and exact-index feasibility are established; final production freeze remains pending verified TLS and discrepancy review.

## Corrective access evidence (2026-09-11)

The selected sources were re-checked over a small fixed feasibility window.
Provider-shaped CSV excerpts from that check are **not version-controlled**:
the repository now keeps only code, tests, sanitized manifests/hashes, and
prose provenance so provider data cannot be accidentally redistributed.
The historical hashes and row-count notes below remain audit evidence only;
they are not production inputs.

**Decision:** Yahoo `^GSPC` is the canonical S&P 500 OHLC source. FRED `SP500` is an optional, non-blocking independent close-validation overlay when available and never overwrites Yahoo. Official Cboe history remains VIX. FRED `DGS1MO` remains the preferred one-month risk-free-rate proxy when maturity-matched.

## Locked hierarchy

| Research object | Source | Decision | Reason / caveat |
|---|---|---|---|
| VIX history | Cboe historical VIX data | **Primary** | Issuer source with public daily history from 1990 to present. Exact historical `CLOSE` timestamp convention remains a documented provenance limitation. |
| S&P 500 OHLC | Yahoo Finance `^GSPC` through pinned `yfinance`, `auto_adjust=False` | **Primary / canonical** | Exact price index rather than SPY; supplies OHLC. The persisted CSV is a deterministic normalized acquisition snapshot, not byte-identical Yahoo response data. |
| S&P 500 close validation | FRED `SP500` when available | **Optional validation only** | Independent recent close cross-check. Failure to reach FRED does not block acquisition; discrepancies are recorded and never overwrite Yahoo. |
| Engineering fallback | SPY | **Engineering-only** | ETF tracking, dividends, microstructure, and adjustment differences prevent substitution for the S&P 500 index. |
| Short risk-free rate for Track A | FRED / Federal Reserve H.15; prefer `DGS1MO` when available and maturity-matched | **Primary rate hierarchy** | One-month constant maturity is the natural first choice for approximately one-month option validation; use the nearest defensible short maturity otherwise and document conversions. |
| Legacy feasibility Treasury feed | U.S. Treasury daily yield-curve XML, three-month field | **Legacy/provisional only** | Retained for reproducibility of the initial feasibility utility; it does not override the Track A rate hierarchy. |

## Exact-index retrieval contract

The production S&P 500 acquisition must:

- request symbol exactly `^GSPC`;
- use daily interval, `auto_adjust=False`, no pre/post bars, and no automated repair;
- use an inclusive start and exclusive frozen end;
- reject any returned bar dated on or after the retrieval's current New York date;
- record the installed `yfinance` version and all request parameters;
- schema-normalize, numerically parse, date-normalize, sort, and deterministically serialize the `yfinance` DataFrame before first persistence;
- hash all local artifacts with SHA-256;
- record schema, coverage, missingness, byte counts, source URLs, request parameters, software versions, and transport/TLS state.

The confirmatory **forecast-origin** sample is frozen through 2025-12-31, but forward realized targets for the final 2025 origins require later S&P 500 returns. The primary 30-calendar-day target for a 2025-12-31 origin requires returns through 2026-01-30, while the 21-trading-day robustness target requires returns through 2026-02-02. The canonical production S&P 500 request is therefore:

```bash
vrp-download-spx --start-date 1990-01-02 --end-exclusive 2026-02-03 --validate-fred
```

The post-2025 S&P observations are **target-support outcomes only**. They do not extend the VIX forecast-origin sample, the OOS evaluation-origin window, or the confirmatory predictor information set. The target-construction code must enforce `origin_date <= 2025-12-31` even when later S&P rows are present.

## Historical FRED SP500 feasibility check

The 2026-08-10 feasibility run compared Yahoo closes with FRED `SP500`. That comparison is historical evidence only. Production acquisition does not require FRED `SP500`; the recommended production command requests the validation overlay, but transport failure is classified and non-blocking. Malformed validation responses are recorded separately from transport failure.

## Frozen feasibility result from 2026-08-10

Initial exact-index feasibility used inclusive start 1990-01-01 and exclusive end 2026-08-10.

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

Discrepancy dates and absolute differences after both sources are rounded to FRED's two-decimal precision:

- 2021-08-11: 5.29
- 2019-08-12: 1.05
- 2020-05-11: 0.13
- 2018-11-29: 0.04
- 2020-10-05: 0.03
- 2020-10-02: 0.02
- 2020-10-06: 0.02

The two largest discrepancies are material enough to require explicit investigation during cleaning. They must not be automatically averaged, overwritten, or dropped.

## TLS / transport status

The initial feasibility acquisition documented a local certificate-chain problem and used `verify=False` for Yahoo. That run remains valid only as **feasibility evidence**.

The final 1990–2025 production freeze must be reacquired with normal certificate verification enabled. Its sanitized provenance manifest must record verified TLS status and be committed under `data/manifests/`.

## Official/provider references

- Cboe VIX historical data: https://www.cboe.com/tradable_products/vix/vix_historical_data/
- Cboe VIX methodology: https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf
- Yahoo `^GSPC` history: https://finance.yahoo.com/quote/%5EGSPC/history/
- `yfinance.download`: https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html
- FRED `SP500`: https://fred.stlouisfed.org/series/SP500
- FRED one-month Treasury `DGS1MO`: https://fred.stlouisfed.org/series/DGS1MO


## Exchange-calendar reproducibility

All S&P 500 target/session completeness checks use the XNYS calendar from
`exchange-calendars==4.13.2`. The exact calendar-library version is part of
the scientific environment because historical session definitions determine
which returns enter a target. Production manifests record the calendar name,
library version, and expected session count. Changing that pinned version
requires an explicit reproducibility review before results are recomputed.


## Production VIX freeze

The official Cboe daily history is frozen independently from the S&P 500
outcome-support window:

```bash
vrp-download-vix --start-date 1990-01-02 --end-exclusive 2026-01-01
```

The VIX production validator requires finite positive OHLC, valid OHLC
ordering, unique dates, and complete XNYS-session coverage over the frozen
predictor window. The manifest records the 2014-10-06 weekly-option inclusion
transition and the historical close-timing limitation. Predictor alignment is
performed by `vrp.origin_panel.align_origin_panel`; post-2025 S&P rows remain
outcome support only and cannot enter the origin panel.
