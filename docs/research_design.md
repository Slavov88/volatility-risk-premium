# Research design — current pre-analysis specification

**Authoritative protocol:** `paper/method_protocol.md`  
**Decision date:** 2026-08-26  
**Status:** locked before empirical VRP, forecast-ranking, or regime results; coauthor review pending.

This file is a concise research-design summary. If it conflicts with `paper/method_protocol.md`, the protocol controls.

## Central question

Is the excess of option-implied over subsequently realized S&P 500 variance statistically robust, economically interpretable, and stable once the VIX horizon, overlapping observations, volatility dynamics, forecast evaluation, and regimes are handled carefully?

The theoretical variance risk premium is

\[
E_t^Q[\mathrm{variance}]-E_t^P[\mathrm{variance}],
\]

which is unobserved. The empirical study therefore uses an ex-post proxy rather than claiming direct observation of the conditional physical expectation.

## Canonical objects

\[
IVOL_t=VIX_t/100,
\qquad
IVAR_t=IVOL_t^2.
\]

For the exact 30-calendar-day interval after origin `t`,

\[
RVAR^{CC}_{t,30c}
=
\frac{365}{30}
\sum_{d:t<d\le t+30c}r_d^2.
\]

Primary empirical proxy:

\[
VRP_t^X=IVAR_t-RVAR^{CC}_{t,30c}.
\]

Secondary intuitive gap:

\[
VOLGAP_t=IVOL_t-\sqrt{RVAR^{CC}_{t,30c}}.
\]

The sign is always implied minus realized.

## Why 30 calendar days is primary

VIX is a constant 30-calendar-day expected-volatility measure. The primary realized target therefore holds the calendar horizon fixed and allows the number of exchange sessions inside the interval to vary. This is the closest empirical match to the economic object represented by VIX.

The next 21 trading days are retained as a mandatory one-trading-month robustness approximation:

\[
RVAR^{CC}_{t,21t}
=
\frac{252}{21}\sum_{j=1}^{21}r_{t+j}^2.
\]

Both designs are forward-looking: no return ending on or before the forecast origin enters the target.

## Hypotheses

- **H1:** mean primary `VRP_X` equals zero versus a two-sided alternative; literature-motivated expected sign is positive.
- **H2:** variance-space Mincer–Zarnowitz calibration, jointly testing `alpha=0, beta=1` in `RVAR = alpha + beta*IVAR + u`.
- **H3:** genuinely OOS forecast comparison of VIX, GARCH(1,1), and a naive historical-variance benchmark on a common mask.
- **H4:** encompassing regression testing incremental predictive content of VIX and GARCH conditional on one another.
- **H5:** formal NBER recession/non-recession comparison plus separate pre-defined 2008, 2020, and 2022 case studies.

## Inference and robustness

- Primary rolling 30c targets use Newey–West/HAC with lag `L0` derived mechanically from actual target-set overlap before outcomes are viewed; 42 and 63 are bandwidth sensitivities.
- A deterministic non-overlapping 30c sample is mandatory.
- Fixed 21-trading-day robustness uses HAC `maxlags=20`, with 10/21/42 sensitivity.
- Close-to-close realized variance is primary; Parkinson and Garman–Klass are robustness estimators.
- Variance-space results are primary; volatility-space gaps are secondary communication aids.
- Post-2003, Student-t GARCH, and five-year rolling GARCH analyses are mandatory robustness checks.

## Out-of-sample forecast design

Initial estimation uses all valid returns through the last S&P 500 trading day of 2006. Evaluation begins on the first trading day of 2007. The primary GARCH model is recursively re-estimated on an expanding window; a five-year rolling window is robustness.

For each primary origin, GARCH daily conditional variances are summed over the future exchange sessions whose return-ending dates fall strictly after `t` and no later than `t+30` calendar days, then annualized by `365/30`.

The naive primary benchmark is the corresponding backward-looking 30-calendar-day realized variance. All forecasts use identical targets and evaluation dates.

## Interpretation discipline

A positive ex-post proxy does not itself prove irrationality. VIX can contain useful forward-looking information and still be systematically above subsequently realized variance because option prices can include compensation for volatility/tail risk. Forecast ranking is evidence about relative predictive performance, not a standalone test of the Efficient Markets Hypothesis.
