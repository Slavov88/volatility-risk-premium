# Data dictionary — planned analysis schema

This versioned schema follows `paper/method_protocol.md` version 1.0.1: substantive lock 2026-08-26, technical sample-tail amendment 2026-08-27. It describes intended variables; it is not evidence that the cleaned panel, realized-variance targets, or forecast results already exist.

## Market and return variables

| Variable | Type | Internal unit | Source / derivation | Timing | Role / caveat |
|---|---|---|---|---|---|
| `date` | date | exchange date | aligned source date | forecast origin | S&P 500 exchange calendar. |
| `sp500_open` | float | index points | Yahoo `^GSPC`, `auto_adjust=False` | same trading day | Used for Garman–Klass robustness. |
| `sp500_high` | float | index points | Yahoo `^GSPC`, `auto_adjust=False` | end-of-day | Used for range estimators. |
| `sp500_low` | float | index points | Yahoo `^GSPC`, `auto_adjust=False` | end-of-day | Used for range estimators. |
| `sp500_close` | float | index points | Yahoo `^GSPC`; FRED overlap validation | normally market close | Exact index, not SPY. Source discrepancies are investigated, not silently corrected. |
| `log_return` | float | decimal daily return | `log(close_t / close_t-1)` | known after close at `t` | First valid observation is missing. |
| `vix_close_pct` | float | annualized percentage points | Cboe VIX daily `CLOSE` | end-of-day predictor | Target begins strictly after `t`; exact historical close timestamp remains a provenance limitation. |
| `ivol` | float | annualized decimal volatility | `vix_close_pct / 100` | origin information | VIX is not a single-option Black–Scholes IV. |
| `ivar` | float | annualized decimal variance | `ivol**2` | origin information | Primary implied-side forecast quantity. |

## Forecast-origin and target-support boundary

- Confirmatory forecast origins satisfy `date <= 2025-12-31`.
- S&P 500 OHLC/return rows through **2026-02-02** may be retained solely to realize forward targets for late-2025 origins.
- Post-2025 S&P rows are never eligible VIX forecast origins, never extend the GARCH training/evaluation-origin sample, and never create standalone 2026 confirmatory observations.
- The production acquisition therefore uses `--end-exclusive 2026-02-03`.
- Target construction must keep the origin-eligibility mask separate from the availability of future outcome rows.

## Primary 30-calendar-day target

For origin `t`, the eligible return-ending exchange dates satisfy `t < d <= t + 30 calendar days`.

| Variable | Internal unit | Definition | Role |
|---|---|---|---|
| `hvar_cc_fwd_30c` | unannualized decimal variance | `sum(log_return_d**2 over eligible dates)` | Raw primary forward close-to-close variance. |
| `rvar_cc_fwd_30c` | annualized decimal variance | `(365 / 30) * hvar_cc_fwd_30c` | **Primary realized target.** |
| `rvol_cc_fwd_30c` | annualized decimal volatility | `sqrt(rvar_cc_fwd_30c)` | Primary-horizon realized volatility. |
| `vrp_x_cc_30c` | annualized decimal variance | `ivar - rvar_cc_fwd_30c` | **Primary ex-post variance-risk-premium proxy.** |
| `volgap_cc_30c` | annualized decimal volatility | `ivol - rvol_cc_fwd_30c` | Secondary intuitive gap. |
| `target_session_count_30c` | integer | number of exchange-session returns in the calendar target | Audit variable; varies by origin. |
| `target_end_date_30c` | date | `t + 30 calendar days` | Calendar-horizon audit variable. |

The primary target is missing unless the full 30-calendar-day interval is observable; it is never shortened at the sample edge. For the final allowed origin, 2025-12-31, this requires S&P 500 return support through 2026-01-30.

## Mandatory 21-trading-day horizon robustness

| Variable | Internal unit | Definition | Role |
|---|---|---|---|
| `rvar_cc_fwd_21t` | annualized decimal variance | `(252 / 21) * sum(next 21 trading-day squared returns)` | Mandatory horizon robustness target. |
| `rvol_cc_fwd_21t` | annualized decimal volatility | `sqrt(rvar_cc_fwd_21t)` | Robustness volatility. |
| `vrp_x_cc_21t` | annualized decimal variance | `ivar - rvar_cc_fwd_21t` | Robustness variance-premium proxy. |
| `volgap_cc_21t` | annualized decimal volatility | `ivol - rvol_cc_fwd_21t` | Robustness volatility gap. |

For the final allowed origin, 2025-12-31, the 21-trading-day robustness target requires S&P 500 return support through 2026-02-02.

## Range-estimator robustness

| Variable family | Internal unit | Definition / timing | Caveat |
|---|---|---|---|
| `rvar_parkinson_fwd_30c` | annualized decimal variance | sum Parkinson daily estimates over the same 30-calendar-day eligible exchange dates, annualized by `365/30` | Classic estimator excludes overnight moves and is sensitive to range data quality. |
| `rvar_gk_fwd_30c` | annualized decimal variance | sum Garman–Klass daily estimates over the same primary date set, annualized by `365/30` | Classic assumptions include no opening jumps and low drift. |
| `rvar_parkinson_fwd_21t` | annualized decimal variance | next 21 trading-day Parkinson estimates, annualized by `252/21` | Horizon robustness. |
| `rvar_gk_fwd_21t` | annualized decimal variance | next 21 trading-day Garman–Klass estimates, annualized by `252/21` | Horizon robustness. |

Equivalent `rvol_*`, `vrp_x_*`, and `volgap_*` variables are derived by square root and implied-minus-realized subtraction where needed.

## Forecast variables

| Variable | Internal unit | Definition | Information set |
|---|---|---|---|
| `gvar_vix_30c` | annualized decimal variance | `ivar` | VIX at origin `t`. |
| `gvar_garch_30c` | annualized decimal variance | `(365/30) * sum(future daily GARCH variance forecasts for exchange sessions ending within t+30c)` | Only returns available at or before `t`. |
| `gvar_naive_30c` | annualized decimal variance | `(365/30) * sum(squared returns with t-30c < d <= t)` | Backward-looking only. |
| `gvar_garch_21t` | annualized decimal variance | `(252/21) * sum(next 21 conditional-variance forecasts)` | 21-trading-day robustness. |
| `gvar_naive_21t` | annualized decimal variance | `(252/21) * sum(last 21 squared returns)` | 21-trading-day robustness. |

Formal forecast comparisons use a single common mask across VIX, GARCH, naive forecast, and realized target.

## Regime variables

| Variable | Type | Definition | Rule |
|---|---|---|---|
| `nber_recession` | boolean | NBER monthly business-cycle recession status | Each daily origin inherits its calendar month's NBER status; never used as a predictor. |
| `case_study_2008` | boolean | exact frozen window from `paper/regime_definitions.md` | Descriptive/subperiod analysis only. |
| `case_study_2020` | boolean | exact frozen window from `paper/regime_definitions.md` | Descriptive/subperiod analysis only. |
| `case_study_2022` | boolean | exact frozen window from `paper/regime_definitions.md` | Descriptive/subperiod analysis only. |

## Units and sign

- VIX raw values are percentage points; divide by 100 before analysis.
- Volatility is stored as annualized decimal standard deviation.
- Variance is stored as annualized decimal variance.
- Positive premium always means **implied minus realized**.
- `VRP_X` refers to variance space; `VOLGAP` refers to volatility space.
