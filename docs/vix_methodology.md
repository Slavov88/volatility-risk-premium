# VIX methodology note

**Tracker task:** W1-06  
**Status:** substantive methodology complete; exact free-history `CLOSE` timestamp remains an open provenance limitation.

## What VIX measures

Cboe defines VIX as a constant **30-calendar-day** measure of expected S&P 500 volatility derived from SPX/SPXW option prices. The methodology uses near- and next-term option strips, aggregates out-of-the-money puts and calls across strikes, computes variance quantities for the two maturities, and interpolates them to a constant 30-day maturity.

For one maturity `T`, the core variance expression is

\[
\sigma^2(T)=\frac{2}{T}\sum_i
\frac{\Delta K_i}{K_i^2}e^{RT}Q(K_i)
-\frac{1}{T}\left(\frac{F}{K_0}-1\right)^2.
\]

Here `K_i` is strike, `Delta K_i` its interval, `Q(K_i)` the methodology option quote, `R` the relevant rate, `F` the option-implied forward, and `K_0` the first strike at or below `F`. The final VIX level is 100 times the square root of the interpolated annualized variance.

Primary methodology reference:
https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf

Historical VIX data:
https://www.cboe.com/tradable_products/vix/vix_historical_data/

## Why VIX is not a single-option Black–Scholes IV

A Black–Scholes implied volatility inverts one parametric pricing equation for one option. VIX aggregates many SPX option quotes across strikes and two maturities using variance-replication logic.

“Model-free” does **not** mean assumption-free. Option selection, quote quality, strike filtering, forward construction, interest rates, maturity interpolation, and no-arbitrage replication logic remain material.

Track A's single-option Black–Scholes IV and Track B's VIX must remain separate in code, equations, figures, and prose.

## Canonical interpretation in this project

\[
IVOL_t=VIX_t/100,
\qquad
IVAR_t=IVOL_t^2.
\]

The primary empirical target is the S&P 500 variance realized over the exact forward 30-calendar-day interval:

\[
RVAR^{CC}_{t,30c}
=
\frac{365}{30}\sum_{d:t<d\le t+30c}r_d^2.
\]

Primary empirical proxy:

\[
VRP_t^X=IVAR_t-RVAR^{CC}_{t,30c}.
\]

This is called the **ex-post variance-risk-premium proxy**. The theoretical object

\[
E_t^Q[\mathrm{variance}]-E_t^P[\mathrm{variance}]
\]

is conditional and unobserved, so the ex-post proxy also contains forecast error and measurement effects.

Secondary intuitive quantity:

\[
VOLGAP_t=IVOL_t-RVOL^{CC}_{t,30c}.
\]

The fixed next-21-trading-day target is mandatory robustness because roughly one trading month is a conventional empirical approximation to VIX's 30-calendar-day horizon. It is not the primary horizon.

## Historical methodology and sample interpretation

Cboe introduced the original VIX in 1993 using S&P 100 option prices and changed the methodology in 2003 to the current broad-strike SPX option-strip approach. Cboe supplies VIX history from 1990 to present and separately identifies the older VXO series for the original methodology.

The core study therefore uses the official VIX historical series while reporting a **post-2003 sensitivity analysis** so conclusions do not depend entirely on the pre-2003/back-history portion of the series.

## Historical `CLOSE` timestamp audit

Cboe's historical-data page describes the downloadable series as daily closing values. Current VIX documentation describes repeated intraday calculation and an end-of-day/last-published value. However, the free historical CSV does not explicitly bind every `CLOSE` observation across the full history to one perfectly unchanged timestamp convention.

The S&P 500 cash close is normally around 4:00 p.m. ET, while current VIX dissemination extends beyond that point. Exact historical synchronization is therefore not assumed.

Operationally:

1. daily VIX `CLOSE` is treated as the end-of-day predictor at origin `t`;
2. the realized target begins with the first S&P 500 return ending strictly after `t`;
3. no same-date return is included in the forward target;
4. the timestamp limitation is documented rather than “solved” by an unsupported adjustment.

Cboe EOD-input reference:
https://datashop.cboe.com/vix-index-eod-calculation-inputs
