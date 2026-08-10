# Research design - current pre-analysis specification

**Protocol decision date:** 2026-08-10
**Status:** Substantively locked and recorded in version control before analysis;
coauthor review remains pending.

## Question and empirical objects

The central question is whether the excess of option-implied variance at date
\(t\) over S&P 500 variance realized after \(t\) is statistically robust,
economically interpretable, and stable across estimators and market regimes.
The theoretical conditional variance risk premium is
\(E_t^Q[\mathrm{variance}]-E_t^P[\mathrm{variance}]\); it is not directly
observed by this design.

| Symbol | Definition | Unit and role |
|---|---|---|
| \(IVOL_t\) | \(VIX_t/100\) | Annualized decimal implied volatility. |
| \(IVAR_t\) | \(IVOL_t^2\) | Annualized decimal implied variance. |
| \(HVAR_{t,30c}\) | Sum of squared close-to-close log returns whose return-ending dates satisfy \(t<d\leq t+30\) calendar days | Unannualized forward variance over the actual exchange calendar. |
| \(RVAR_{t,30c}\) | \((365/30)HVAR_{t,30c}\) | Primary annualized forward realized variance. |
| \(RVOL_{t,30c}\) | \(\sqrt{RVAR_{t,30c}}\) | Annualized forward realized volatility. |
| \(VRP^X_t\) | \(IVAR_t-RVAR_{t,30c}\) | Primary **ex-post variance-risk-premium proxy**. Positive means implied minus realized variance. |
| \(VOLGAP_t\) | \(IVOL_t-RVOL_{t,30c}\) | Secondary intuitive volatility gap; never called a variance risk premium. |

The primary horizon is an actual 30-calendar-day forward window with no
shortened end-of-sample targets. Fixed 21-trading-day targets are robustness
checks, with 20- and 22-day sensitivities pre-specified.

## Pre-specified hypotheses

| ID | Exact null and alternative | Primary specification and decision rule |
|---|---|---|
| H1 - Mean variance premium | \(H_0:E[VRP^X_t]=0\) versus \(H_1:E[VRP^X_t]\neq0\). The literature-predicted sign is recorded as positive before analysis. | Estimate the mean and a two-sided 95% HAC confidence interval. A one-sided positive-premium test is secondary only. |
| H2 - VIX calibration | \(RVAR_{t,H}=\alpha+\beta IVAR_t+u_t\), with joint \(H_0:\alpha=0,\beta=1\). | Use robust covariance and a joint Wald test. This is a forecast-calibration null, not a restriction that theory must satisfy. |
| H3 - Relative OOS accuracy | With VIX and GARCH evaluated on identical dates and targets, \(d_t=(RVAR_{t,H}-IVAR_t)^2-(RVAR_{t,H}-\widehat{GVAR}_t)^2\), and \(H_0:E[d_t]=0\). | MSE is the primary loss and RMSE is reported because it preserves the ranking. QLIKE is a robustness loss if cleanly implemented; MAE is descriptive only. No naive Diebold-Mariano test is used without overlap-aware dependence handling. |
| H4 - Regime dependence | \(H_0:E[VRP^X_t\mid\text{NBER recession}]=E[VRP^X_t\mid\text{non-recession}]\). | Compare NBER recession and non-recession means with robust covariance. The 2008, 2020, and 2022 episodes are separate case studies with no forced common sign. |

## Robustness and reporting requirements

- Close-to-close squared log returns are the primary realized-variance
  estimator. Parkinson and Garman-Klass are robustness estimators on identical
  dates. Estimator disagreement must be reported and explained; agreement of
  all three confidence intervals is not a validity requirement.
- For fixed 21-trading-day targets, Newey-West `maxlags=20`. For the calendar
  target, derive \(L_0\) mechanically as the greatest ordered forecast-origin
  lag whose target return-date sets overlap. Report bandwidth sensitivities at
  \(L_0\), 42, and 63 without selecting on significance.
- The predetermined non-overlapping sample starts at the earliest eligible
  origin and repeatedly selects the earliest next origin strictly after the
  preceding target end. Phase offsets are appendix-only.
- The primary OOS design uses the first ten complete aligned calendar years for
  initial estimation and then re-estimates an expanding window at every origin.
  Robustness uses a rolling ten-year window, a post-2003 start, and a 2010+
  start. Splits cannot change after rankings are inspected.
- Forecast construction uses only information available at the origin. A
  negative, null, or regime-specific estimate is a valid result.
- No empirical claim enters the paper until generated reproducibly and audited
  by the other coauthor.
