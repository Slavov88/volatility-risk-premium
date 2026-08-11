# Pre-analysis method protocol - current specification

**Decision record date:** 2026-08-10
**Tracker task:** W1-03
**Status:** Methodological content locked and recorded by the protocol-freeze
commit before construction of realized-variance targets or inspection of
empirical VRP results. Coauthor review remains pending.

## 1. Scope

The core study uses the S&P 500 price index and Cboe VIX. Track A's
single-option Black-Scholes implied volatility remains distinct from Track B's
model-free option-strip VIX. Other markets, intraday models, Heston calibration,
and return prediction remain outside the core specification.

The theoretical conditional object is

\[
E_t^Q[\mathrm{variance}]-E_t^P[\mathrm{variance}],
\]

which is not directly observed. The empirical design uses an ex-post proxy and
does not equate a realized outcome with a conditional physical expectation.

## 2. Canonical notation and sign

| Symbol | Definition | Unit / interpretation |
|---|---|---|
| \(IVOL_t\) | \(VIX_t/100\) | Annualized decimal implied volatility. |
| \(IVAR_t\) | \(IVOL_t^2\) | Annualized decimal implied variance. |
| \(HVAR_{t,30c}\) | \(\sum_{d:\,t<d\leq t+30c} r_d^2\) | Unannualized forward variance; \(d\) is the return-ending exchange date. |
| \(RVAR_{t,30c}\) | \((365/30)HVAR_{t,30c}\) | Primary annualized forward realized variance. |
| \(RVOL_{t,30c}\) | \(\sqrt{RVAR_{t,30c}}\) | Annualized forward realized volatility. |
| \(VRP^X_t\) | \(IVAR_t-RVAR_{t,30c}\) | Primary ex-post variance-risk-premium proxy. |
| \(VOLGAP_t\) | \(IVOL_t-RVOL_{t,30c}\) | Secondary volatility gap, not a VRP. |

All code, equations, figures, and tables use the positive convention **implied
variance minus realized variance**. Percentage conversion is presentation-only.

## 3. Data, timestamp, and freeze rules

- VIX history comes from Cboe. The exact-index OHLC candidate is Yahoo Finance
  `^GSPC` retrieved through pinned `yfinance` with `auto_adjust=False`. FRED
  `SP500` close validates the overlapping period. SPY remains engineering-only.
- Retrievals use a declared inclusive start and exclusive frozen end. The
  Yahoo `yfinance` DataFrame is normalized and deterministically serialized
  into an immutable acquisition snapshot; it is not persisted provider-response
  bytes. Cboe and FRED source responses may be persisted as fetched bytes.
  Acquisition artifacts are date-stamped, hashed with SHA-256, and accompanied
  by schema, coverage, missingness, request parameters, software versions, and
  artifact-type metadata.
- A current New York trading-date bar is rejected even if returned. The final
  empirical sample ends at the last origin with a complete primary target; no
  forward target is shortened.
- FRED discrepancies are reported, never used to silently replace Yahoo values.
- Cboe calls its history daily closing values; current methodology disseminates
  RTH VIX through approximately 4:15 p.m. ET, and its EOD-input product describes
  the last published value. The free historical CSV does not explicitly state
  that `CLOSE` is the 4:15 p.m. value for every historical date. This remains
  an open provenance limitation, not an implementation blocker. Operationally,
  daily VIX `CLOSE` is the end-of-day predictor at origin \(t\), and the target
  begins with the first return ending strictly after \(t\), with no same-date
  return. SPX cash close is normally 4:00 p.m. ET, so exact synchronization is
  not assumed.

## 4. Primary and robustness horizons

For a forecast origin dated \(t\), the primary close-to-close target includes
exactly the squared log returns whose return-ending dates meet
\(t<d\leq t+30\) calendar days on the actual exchange calendar:

\[
HVAR_{t,30c}=\sum_{d:\,t<d\leq t+30c}r_d^2,
\qquad
RVAR_{t,30c}=\frac{365}{30}HVAR_{t,30c}.
\]

The target is missing unless the complete 30-calendar-day interval is observed.
Robustness targets use the next 21 trading-day return-ending dates with
annualization \((252/21)\sum r_d^2\), plus fixed 20- and 22-day sensitivities.
The horizon is never selected from results.

## 5. Realized-variance estimators

Close-to-close squared log returns are primary. Parkinson and Garman-Klass use
the same origin, target horizon, and eligible-date mask as robustness
estimators. Their assumptions and sensitivity to overnight moves, opening
jumps, and price-range errors will be documented with implementation. Any
disagreement is reported and explained; it does not become a fifth hypothesis
and does not invalidate otherwise correct inference.

## 6. Exact H1-H4

### H1 - Mean variance premium

\[
H_0:E[VRP^X_t]=0
\quad\text{versus}\quad
H_1:E[VRP^X_t]\neq0.
\]

Primary inference is a two-sided 95% HAC confidence interval. Before analysis,
the literature-motivated expected sign is recorded as positive. A one-sided
positive-premium test may appear only as secondary evidence.

### H2 - VIX calibration

\[
RVAR_{t,H}=\alpha+\beta IVAR_t+u_t,
\qquad H_0:\alpha=0,\;\beta=1.
\]

Use robust covariance and a joint Wald test. The joint null is a calibration
benchmark, not a condition theory requires to hold.

### H3 - Relative out-of-sample forecast accuracy

VIX and GARCH use the same variance target and evaluation dates. Define

\[
d_t=(RVAR_{t,H}-IVAR_t)^2
-(RVAR_{t,H}-\widehat{GVAR}_t)^2,
\qquad H_0:E[d_t]=0.
\]

MSE is the primary loss; RMSE is also reported and preserves the MSE ranking.
QLIKE is a robustness loss if all forecasts are strictly positive and its
implementation passes tests. MAE is descriptive only. Formal loss-difference
inference must account for overlapping-target serial dependence; a naive
Diebold-Mariano implementation is prohibited.

Open decision O-002 must be locked and tested before H3: daily GARCH
conditional variances will be summed for exchange sessions whose return-ending
dates satisfy \(t<d\leq t+30\) calendar days, then annualized by \(365/30\) to
match the variable-session realized-variance target. The timing, exchange
calendar, and missing-session behavior must be frozen before comparison. No
GARCH estimator is implemented in this protocol-foundation pass.

### H4 - Regime dependence

The formal comparison is NBER recession versus non-recession observations:

\[
H_0:E[VRP^X_t\mid R_t=1]=E[VRP^X_t\mid R_t=0],
\]

The regime label attaches to forecast origin \(t\), is used ex post only, and
is never a predictor. Every eligible daily origin deterministically inherits
the external monthly chronology value for its calendar month; the chronology
version and mapping must be recorded before H4. The equality is tested with
robust covariance. The Global Financial Crisis/2008, COVID/2020, and
inflation/monetary-tightening/2022 remain three separate case studies. No common
directional prediction is imposed.

## 7. HAC and non-overlap

- Fixed 21-trading-day target: Newey-West `maxlags=20`.
- Primary 30-calendar-day target: order eligible origins by exchange date and
  set \(L_0\) to the greatest origin lag for which two target return-date sets
  overlap. This is computed from the calendar before outcomes are analyzed.
- Report bandwidths \(L_0\), 42, and 63. No bandwidth is selected by its
  significance.
- The predetermined non-overlapping sample starts with the earliest eligible
  origin and then selects the earliest origin strictly after the prior target's
  calendar end. Alternative phase offsets are appendix-only.

## 8. Out-of-sample design

The first ten complete calendar years with a fully aligned predictor/target
panel form the initial estimation sample. Forecasting starts at the first
eligible origin immediately afterward. Every primary forecast origin re-fits
the model on an expanding window containing only data available at that origin.

Robustness uses (i) a rolling ten-year estimation window, (ii) a post-2003 OOS-
start sensitivity, and (iii) a 2010+ late-sample sensitivity. No split or window
may change after forecast rankings are viewed.

## 9. Common-mask and leakage rules

- VIX and GARCH comparisons use an identical origin, target, and missing-value
  mask.
- Predictors at \(t\) cannot change when any observation after \(t\) changes.
- Date-labelled unit tests must prove that the first primary target return ends
  after \(t\), while the last ends no later than \(t+30\) calendar days.
- All target losses and sample exclusions are logged.

## 10. Reporting discipline

Effect sizes, uncertainty, sample sizes, and estimator disagreement take
precedence over binary significance. Negative, zero, mixed, or regime-specific
results remain valid. Expected signs from prior literature are never presented
as findings, and no empirical result is produced during protocol lock.
