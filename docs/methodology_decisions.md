# Methodology decision ledger

**Initial protocol freeze:** 2026-08-10  
**Expanded draft:** 2026-08-23  
**Final pre-analysis methodological review:** 2026-08-26  
**Technical sample-tail amendment:** 2026-08-27  
**Authoritative protocol:** `paper/method_protocol.md`  
**Result state at final review:** no empirical VRP, forecast-ranking, or regime result had been generated or inspected.

This file preserves the evolution of the design rather than pretending that earlier drafts never existed. Earlier decisions remain visible in Git history. The August 26 protocol is authoritative for all subsequent implementation.

## Current locked decisions

| ID | Current decision | Status / history | Rationale / consequence |
|---|---|---|---|
| M-001 | Primary empirical proxy is `VRP_X = IVAR - RVAR`; `VOLGAP = IVOL - RVOL` is secondary. | **Locked 2026-08-26; retains Aug-10 variance-space design.** | Keeps the primary object in variance units while preserving an intuitive volatility-space presentation. |
| M-002 | Store returns, volatility, and variance as decimals; convert VIX by `IVOL=VIX/100`, then `IVAR=IVOL**2`. | **Retained.** | Prevents factors-of-100/10,000 errors. |
| M-003 | Primary horizon is the exact forward **30-calendar-day** interval, annualized by `365/30`; the exact next **21 trading days** is mandatory robustness, annualized by `252/21`. | **Locked 2026-08-26.** Aug-10 used 30c primary; the Aug-23 draft temporarily reversed the hierarchy; the final review restored 30c primary after checking the VIX economic horizon. | Matches the VIX constant-calendar-maturity object while directly testing the conventional fixed-session approximation. |
| M-004 | Close-to-close squared log returns are the primary realized-variance estimator; Parkinson and Garman–Klass are mandatory robustness estimators. | **Retained.** | Estimator disagreement is reported, not optimized away. |
| M-005 | Confirmatory structure: H1 mean `VRP_X`; H2 VIX variance calibration; H3 OOS VIX/GARCH/naive accuracy; H4 VIX–GARCH encompassing; H5 formal NBER regime comparison plus separate 2008/2020/2022 case studies. | **Expanded 2026-08-26; supersedes Aug-10 four-hypothesis version.** | Makes forecast benchmarking and encompassing explicit while keeping regime analysis externally defined. |
| M-006 | Primary 30c HAC lag `L0` is derived mechanically from actual target-set overlap before outcomes are analyzed; report 42/63 sensitivity. Fixed-21 robustness uses HAC `maxlags=20`, with 10/21/42 sensitivity. | **Locked.** | Handles induced serial dependence without bandwidth selection on significance. |
| M-007 | Primary OOS training uses all valid returns through the last trading day of 2006; evaluation begins on the first trading day of 2007; GARCH uses expanding recursive re-estimation. Five-year rolling estimation is mandatory robustness. | **Locked 2026-08-26; supersedes Aug-10 first-ten-years / ten-year-rolling rule.** | Leaves the GFC, COVID shock, and 2022 episode out of the initial training sample while giving GARCH a long estimation history. |
| M-008 | Formal regime chronology is the NBER monthly U.S. business-cycle chronology. Each daily origin inherits its calendar-month status; the variable is never a predictor. | **Locked 2026-08-26; clarifies Aug-10 NBER choice.** | Removes discretion over the formal regime definition. |
| M-009 | Primary long-history S&P 500 OHLC candidate is Yahoo Finance `^GSPC` with `auto_adjust=False`; FRED `SP500` validates recent closes; SPY remains engineering-only. | **Retained.** | Exact index is required; validation discrepancies remain visible. |
| M-010 | VIX is a model-free SPX option-strip measure and is never treated as a single-option Black–Scholes IV. | **Required invariant.** | Core conceptual requirement. |
| M-011 | Primary GARCH 30c forecast sums daily conditional-variance forecasts for known exchange sessions whose return-ending dates satisfy `t < d <= t+30c`, then annualizes by `365/30`. | **Closed 2026-08-26; resolves former O-002.** | Gives GARCH exactly the same calendar target as VIX and realized variance. |
| M-012 | Primary naive forecast is trailing 30-calendar-day realized variance using only returns ending at or before `t`; fixed trailing 21 trading days accompanies the 21t robustness design. | **Locked 2026-08-26.** | Keeps the benchmark horizon symmetric without future information. |
| M-013 | Final **forecast-origin** sample ends 2025-12-31. Later S&P 500 observations may be retained only as outcome support needed to realize forward targets for late-2025 origins; they never become 2026 forecast origins or extend the predictor/training information set. | **Clarified 2026-08-27; substantive sample lock unchanged.** | Preserves the last-complete-calendar-year origin sample while avoiding mechanical truncation of valid forward targets at the boundary. |
| M-014 | Final core data must be reacquired with verified TLS; the prior `verify=False` Yahoo feasibility run cannot be the production freeze. | **Locked 2026-08-26.** | Separates feasibility evidence from final provenance. |
| M-015 | Sanitized acquisition manifests are committed under `data/manifests/`; provider/raw market data remain ignored. | **Locked 2026-08-26.** | Makes hashes, source parameters, and validation state auditable from Git without redistributing market data. |

## Open issues before empirical analysis

### O-001 — Exact historical VIX `CLOSE` timestamp

The free Cboe history describes daily closing values, while current methodology/dissemination documents support treating end-of-day VIX as the last RTH value. The free historical schema does not bind every observation to a perfectly synchronized timestamp with the normally 4:00 p.m. ET S&P 500 cash close.

**Operational rule:** VIX `CLOSE` is an end-of-day predictor at origin `t`; the target begins with the first return ending strictly after `t`; no exact same-instant synchronization is assumed.

### O-002 — Yahoo/FRED close discrepancies

The feasibility comparison found seven discrepancies above one cent, including two material cases. These must be investigated during cleaning using source documentation and, if needed, a third independent source. No automatic replacement rule is permitted.

### O-003 — Final production acquisition

The final production snapshot must be reacquired under normal certificate verification and recorded in a sanitized version-controlled manifest. Forecast origins remain 1990-01-02 through 2025-12-31, while S&P 500 outcome-support rows extend through 2026-02-02 (`--end-exclusive 2026-02-03`) solely to complete late-2025 forward targets.

## Non-negotiable implementation tests

- Primary date-labelled targets include only return-ending dates `t < d <= t+30c` and reject shortened final targets.
- Fixed-21 robustness includes exactly the next 21 trading-day returns and no same-date return.
- Altering data after origin `t` cannot change any predictor at `t`.
- GARCH forecast steps map deterministically to the exchange sessions inside the 30c target.
- Competing forecasts use an identical target/date/missingness mask.
- Dimensional checks distinguish variance, volatility, percentage points, and decimals.
- Raw acquisition hashes, software versions, coverage, missingness, validation statistics, and row-loss reports are generated rather than hand-written.
