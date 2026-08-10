# Data dictionary - planned analysis schema

This versioned schema describes the locked definitions. It is not evidence that
the cleaned panel or any realized-variance estimate exists; W2-07/W2-08 and
Week 3 implementation remain separate tasks.

| Variable | Type | Internal unit | Source / derivation | Timing | Caveat |
|---|---|---|---|---|---|
| `date` | date | exchange date | aligned source date | forecast origin | Exchange calendars and holidays require explicit joins. |
| `sp500_open` | float | index points | Yahoo `^GSPC`, `auto_adjust=False` | observed after open | Exact index, not SPY; provider values remain uncorrected raw inputs. |
| `sp500_high` | float | index points | Yahoo `^GSPC`, `auto_adjust=False` | end-of-day | Used only when range-estimator robustness is implemented. |
| `sp500_low` | float | index points | Yahoo `^GSPC`, `auto_adjust=False` | end-of-day | Used only when range-estimator robustness is implemented. |
| `sp500_close` | float | index points | Yahoo `^GSPC` unadjusted close; FRED `SP500` overlap validation | normally 4:00 p.m. ET | Discrepancies are reported, not silently corrected. |
| `log_return` | float | decimal daily return | `log(sp500_close_t / sp500_close_t-1)` | after close at `t` | First valid observation is missing. |
| `vix_close_pct` | float | annualized percentage points | Cboe VIX daily `CLOSE` | end-of-day | Exact free-history close timestamp remains open. |
| `ivol` | float | annualized decimal volatility | `vix_close_pct / 100` | origin information | VIX is not a single-option Black-Scholes IV. |
| `ivar` | float | annualized decimal variance | `ivol**2` | origin information | Primary implied-side empirical variable. |
| `hvar_cc_fwd_30c` | float | decimal variance over 30 calendar days | sum of squared log returns with `t < return_end_date <= t + 30c` | target after `t` | No shortened end targets. |
| `rvar_cc_fwd_30c` | float | annualized decimal variance | `(365 / 30) * hvar_cc_fwd_30c` | target after `t` | Primary realized target. |
| `rvol_cc_fwd_30c` | float | annualized decimal volatility | `sqrt(rvar_cc_fwd_30c)` | target after `t` | Used for secondary intuitive gap only. |
| `vrp_x_cc` | float | annualized decimal variance | `ivar - rvar_cc_fwd_30c` | forecast evaluation | Primary ex-post variance-risk-premium proxy; positive is implied minus realized. |
| `volgap_cc` | float | annualized decimal volatility | `ivol - rvol_cc_fwd_30c` | forecast evaluation | Secondary; never labelled VRP. |
| `rvar_cc_fwd_21t` | float | annualized decimal variance | `(252 / 21) * sum(next 21 trading-day squared returns)` | robustness target | 20/22 trading-day sensitivities are also pre-specified. |
| `rvar_parkinson_fwd_*` | float | annualized decimal variance | forward high-low ranges on the matching date set | robustness target | Sensitive to microstructure and excludes overnight moves in the classic form. |
| `rvar_gk_fwd_*` | float | annualized decimal variance | forward OHLC on the matching date set | robustness target | Classic assumptions include zero drift and no opening jumps. |
