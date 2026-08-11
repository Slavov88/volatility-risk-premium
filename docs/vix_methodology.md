# VIX methodology note

**Tracker task:** W1-06
**Status:** In review; the exact free-history `CLOSE` timestamp remains an open
provenance limitation, not an implementation blocker.

## What VIX measures

Cboe defines VIX as a constant 30-calendar-day measure of expected S&P 500
volatility conveyed by SPX/SPXW option mid-quotes. It selects near- and
next-term expirations, aggregates out-of-the-money puts and calls over strikes,
computes a variance quantity for each term, and interpolates to 30 days.

For one maturity \(T\), the core variance expression is

\[
\sigma^2(T)=\frac{2}{T}\sum_i
\frac{\Delta K_i}{K_i^2}e^{RT}Q(K_i)
-\frac{1}{T}\left(\frac{F}{K_0}-1\right)^2.
\]

Here \(K_i\) is a strike, \(\Delta K_i\) its strike interval, \(Q(K_i)\) the
methodology quote, \(R\) the relevant rate, \(F\) the option-implied forward,
and \(K_0\) the first strike at or below \(F\). After interpolation, VIX is 100
times the square root of annualized variance.

Primary methodology (version 6.0, revised 2026-02-26):
https://cdn.cboe.com/resources/indices/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf

## Why VIX is not a single-option Black-Scholes IV

A Black-Scholes implied volatility inverts one pricing equation for one option
under a parametric model. VIX aggregates many option quotes across strikes and
two maturities using variance-replication logic. “Model-free” means that it does
not require a constant-volatility Black-Scholes surface; it does not mean
assumption-free. Quote quality, strike filtering, forward/rate construction,
interpolation, and no-arbitrage replication remain material.

## Canonical interpretation in this project

- \(IVOL_t=VIX_t/100\) and \(IVAR_t=IVOL_t^2\).
- The primary empirical object is
  \(VRP^X_t=IVAR_t-RVAR_{t,30c}\), called an **ex-post variance-risk-premium
  proxy** when precision matters.
- \(VOLGAP_t=IVOL_t-RVOL_{t,30c}\) is secondary and is never labelled VRP.
- The theoretical object \(E_t^Q[\mathrm{variance}]-E_t^P[\mathrm{variance}]\)
  is conditional and unobserved. The ex-post proxy also contains forecast error
  and measurement effects.
- The primary realized target uses actual calendar dates; a fixed 21-trading-day
  target and 20/22-day variants are robustness checks.

## Historical `CLOSE` timestamp audit

Primary-source evidence checked on 2026-08-10:

1. Cboe's historical-data page labels the downloadable observations “daily
   closing values.”
2. Current VIX methodology states that RTH calculation and dissemination occur
   approximately every 15 seconds from 09:31 a.m. to 4:15 p.m. ET, adjusted for
   shortened sessions.
3. Cboe's VIX EOD Calculation Inputs notice describes the product as containing
   inputs for the “last published value” on each trading day.

Sources:

- https://www.cboe.com/tradable_products/vix/vix_historical_data/
- https://cdn.cboe.com/resources/indices/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf
- https://cdn.cboe.com/resources/trader_news/2022/Trader-E-News-7-8-22.pdf

Together these documents support treating current end-of-day VIX as the last
RTH spot value, normally near 4:15 p.m. ET. However, the free-history page and
CSV schema do not explicitly state that every `CLOSE` observation, including
back-calculated history, uses that exact timestamp or an unchanged convention.
That final field-to-timestamp mapping remains open. SPX `SP500` cash close is
normally 4:00 p.m. ET, so exact synchronization will not be silently assumed.

Operationally, daily VIX `CLOSE` is treated as the end-of-day predictor at
origin \(t\). The forward target begins with the first return ending strictly
after \(t\) and includes no same-date return. The exact historical timestamp
mapping should be resolved and documented before final analysis, but it does
not block target construction. No exact synchronization with the normally
4:00 p.m. SPX cash close is assumed.

Historical VIX CSV:
https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv
