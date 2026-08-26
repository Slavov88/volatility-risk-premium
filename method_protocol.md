# Pre-Analysis Method Protocol

## The Volatility Risk Premium: An Empirical and Theoretical Investigation of the Gap Between Implied and Realized Volatility in Equity Index Markets

**File:** `paper/method_protocol.md`  
**Protocol version:** 1.0  
**Decision date:** 2026-08-26  
**Tracker task:** W1-03  
**Status:** Locked core-analysis protocol pending co-author review  
**Primary market:** S&P 500 / Cboe VIX  
**Core sample:** first common valid trading date on or after 1990-01-02 through 2025-12-31  
**Primary horizon:** exact forward 30 calendar days  
**Mandatory horizon robustness:** next 21 S&P 500 trading days  
**Primary significance level:** 5%, two-sided; 95% confidence intervals  
**Core rule:** no specification may be changed because a result is weak, inconvenient, or contrary to the expected sign.

---

## 1. Purpose and scope

This protocol fixes the main empirical and econometric choices before any empirical variance-risk-premium or forecast-ranking result is inspected. Its purpose is to reduce researcher degrees of freedom, prevent look-ahead bias, make the analysis reproducible, and separate confirmatory analysis from exploratory extensions.

The project has two related but distinct tracks:

- **Track A — Black–Scholes theory and small-scale validation.** Derive the Black–Scholes model, implement a European-option pricer and implied-volatility solver, and validate them against reference values and a small set of market quotes.
- **Track B — Large-sample empirical study.** Use the Cboe VIX as the market-implied volatility measure, construct forward realized-variance targets from S&P 500 prices, estimate the implied–realized variance gap, fit GARCH forecasts, and evaluate statistical and economic interpretations.

Track A must never redefine Track B. In particular, a single-option Black–Scholes implied volatility is not interchangeable with the VIX.

Out of scope for the confirmatory core are trading strategies, large-scale option-surface construction, machine learning, Heston calibration, cross-market comparisons, event studies, and equity-return predictability. These may be attempted only after the core pipeline reproduces from raw data and the authors pass the extension scope gate.

---

## 2. Research question and confirmatory hypotheses

### Primary research question

> Is the observed excess of option-implied over subsequently realized S&P 500 variance statistically robust and economically explicable as compensation for volatility/tail risk, or does it weaken materially once horizon alignment, overlapping observations, non-normality, forecast design, and regime dependence are handled correctly?

### H1 — Mean ex-post variance-premium proxy

Let

\[
IVOL_t = VIX_t/100,
\qquad
IVAR_t = IVOL_t^2.
\]

Let \(RVAR^{CC}_{t,30c}\) be the annualized close-to-close realized variance over the exact forward 30-calendar-day interval defined in Section 6.

Define the primary empirical proxy

\[
VRP_t^X = IVAR_t - RVAR^{CC}_{t,30c}.
\]

Test

\[
H_0:E[VRP_t^X]=0
\]

against the two-sided alternative

\[
H_1:E[VRP_t^X]\neq0.
\]

The literature-motivated expected sign is positive, but the confirmatory test remains two-sided.

### H2 — VIX variance calibration

Estimate

\[
RVAR^{CC}_{t,30c}=\alpha+\beta IVAR_t+u_t
\]

and jointly test

\[
H_0:\alpha=0,\qquad \beta=1.
\]

Rejection is interpreted as forecast miscalibration under this empirical definition, not as proof of irrationality or market inefficiency.

### H3 — Out-of-sample forecast accuracy

Compare three forecasts of the same forward realized-variance target:

1. VIX implied variance, \(IVAR_t\);
2. GARCH(1,1) variance forecast;
3. a naive backward-looking historical-variance benchmark.

All models must use identical forecast origins, target dates, units, and missing-value masks.

Primary reported loss metrics are RMSE and MAE. For formal pairwise loss-difference inference, squared-error loss is used with overlap-aware HAC covariance. QLIKE may be reported as a pre-specified robustness loss if all forecasts are strictly positive and the implementation passes tests.

### H4 — Forecast encompassing

Estimate on the common out-of-sample mask

\[
RVAR^{CC}_{t,30c}
=
\alpha+\beta IVAR_t+\gamma \widehat{GVAR}^{GARCH}_{t,30c}+u_t.
\]

Test whether:

- \(\gamma=0\): GARCH adds no incremental predictive information conditional on VIX;
- \(\beta=0\): VIX adds no incremental predictive information conditional on GARCH.

### H5 — Regime dependence and crisis behavior

The formal external regime classification is the **NBER U.S. Business Cycle Dating Committee monthly chronology**. A daily forecast origin inherits the NBER status of its calendar month. Under the NBER convention, recession months begin in the month after a business-cycle peak and include the trough month. The classification is used ex post only and is never a predictor.

In addition, 2008, 2020, and 2022 are studied as separate pre-defined case studies. Exact case-study windows must be frozen in `paper/regime_definitions.md` before regime outputs are calculated.

No regime or crisis window may be moved after seeing the premium series in order to strengthen a narrative.

---

## 3. Theoretical VRP versus empirical proxies

The theoretical variance risk premium is a conditional expectation object:

\[
VRP_t^{theory}
=
E_t^Q[\text{future variance}]
-
E_t^P[\text{future variance}],
\]

where \(Q\) denotes the risk-neutral measure and \(P\) the physical measure.

Neither term is directly observed. Ex-post realized variance is a noisy outcome, not the physical conditional expectation itself. The empirical proxy therefore contains forecast error and measurement effects as well as any underlying risk premium.

The project uses two distinct empirical quantities:

### Primary variance-space proxy

\[
VRP_t^X = IVAR_t - RVAR_t.
\]

This is the primary inferential object and the quantity referred to as the **ex-post variance-risk-premium proxy**.

### Secondary intuitive volatility gap

\[
VOLGAP_t = IVOL_t - RVOL_t.
\]

This is reported because volatility percentage points are easier to interpret, but it is not labelled the variance risk premium.

The sign convention is always **implied minus realized**.

---

## 4. Data and provenance

### 4.1 VIX

Primary source: official Cboe historical daily VIX data.

Required field:
- daily VIX close.

VIX is treated as a model-free, option-strip measure of expected S&P 500 volatility with constant 30-calendar-day maturity. It is not the Black–Scholes implied volatility of one option.

Operationally, the daily VIX close at origin \(t\) is treated as an end-of-day predictor. The realized target begins strictly after \(t\); no same-date S&P 500 return enters the target.

The paper must acknowledge that the free historical VIX `CLOSE` field is not documented as being perfectly synchronized to the S&P 500 cash close for every historical date. This is a provenance limitation, not permission to use same-date future information.

### 4.2 S&P 500

The empirical underlying is the **S&P 500 price index**, not SPY and not a total-return index.

Required fields:
- date;
- open;
- high;
- low;
- close.

Primary long-history free-source candidate: Yahoo Finance `^GSPC` through a pinned `yfinance` environment with `auto_adjust=False`.

FRED `SP500` close data are used to validate the overlapping recent period. A discrepancy is reported and investigated; neither source is silently overwritten by the other.

If reliable OHLC coverage begins later than reliable close coverage, the close-to-close core sample may be longer than the Parkinson/Garman–Klass robustness samples. Sample differences must be explicit.

### 4.3 Risk-free rate

A short Treasury yield is needed primarily for Track A option validation. Preferred source: the Federal Reserve H.15 series distributed through FRED. Use the one-month constant-maturity Treasury series when it is available and reasonably maturity-matched; otherwise use the nearest defensible short maturity and document the choice.

Rates quoted in annual percentage points must be converted explicitly before entering pricing code.

### 4.4 Core sample and raw-data freeze

The confirmatory sample ends at 2025-12-31, the last complete calendar year before protocol lock. Data from 2026 do not enter the confirmatory core.

Every acquisition must record:
- source and endpoint;
- retrieval timestamp;
- request parameters;
- coverage;
- schema;
- missingness summary;
- software version where applicable;
- SHA-256 hash;
- transport/TLS status;
- validation summary.

Raw acquisition artifacts are immutable and live under `data/raw/`. Sanitized manifests containing provenance metadata but no restricted market data are version-controlled under `data/manifests/`.

The final core acquisition must use normal certificate verification. The earlier feasibility run performed with disabled Yahoo TLS verification remains historical evidence only and must not become the final frozen production snapshot.

---

## 5. Cleaning, dates, and units

1. Normalize dates to `YYYY-MM-DD` and sort ascending.
2. Use the S&P 500 exchange calendar; do not manufacture weekend or holiday observations.
3. Resolve duplicate dates explicitly.
4. Never forward-fill or interpolate S&P 500 prices or VIX.
5. Never delete crisis observations merely because they are extreme.
6. Remove a row only for an identified data error, recording the reason.
7. Require all prices to be positive and OHLC rows to satisfy
   \[
   High_t\ge\max(Open_t,Close_t),\qquad
   Low_t\le\min(Open_t,Close_t),\qquad
   High_t\ge Low_t.
   \]
8. Produce a row-loss and transformation report.
9. Investigate the material Yahoo/FRED close discrepancies identified during feasibility before the cleaned panel is frozen.

Daily close-to-close log return:

\[
r_t=\ln(C_t/C_{t-1}).
\]

Internal units:
- returns: decimal;
- volatility: annualized decimal;
- variance: annualized decimal variance;
- percentages: presentation only.

Canonical constants and definitions must live in one shared configuration source; notebooks may not redefine them independently.

---

## 6. Primary and robustness horizons

### 6.1 Primary target — exact forward 30 calendar days

Cboe defines VIX as a constant 30-calendar-day expected-volatility measure. The primary ex-post target therefore holds the **calendar horizon** constant rather than forcing every origin to contain the same number of exchange sessions.

For origin \(t\), include each close-to-close return whose return-ending exchange date \(d\) satisfies

\[
t<d\le t+30\text{ calendar days}.
\]

Define

\[
HVAR^{CC}_{t,30c}
=
\sum_{d:t<d\le t+30c} r_d^2,
\]

\[
RVAR^{CC}_{t,30c}
=
\frac{365}{30}HVAR^{CC}_{t,30c},
\]

\[
RVOL^{CC}_{t,30c}
=
\sqrt{RVAR^{CC}_{t,30c}}.
\]

The number of exchange-session returns inside the 30-calendar-day interval may vary across origins. This is intentional. The target is missing unless the full calendar interval is observed; end-of-sample targets are never shortened.

### 6.2 Mandatory robustness — next 21 trading days

The conventional one-trading-month approximation uses exactly the next 21 S&P 500 trading-day returns:

\[
RVAR^{CC}_{t,21t}
=
\frac{252}{21}\sum_{j=1}^{21}r_{t+j}^2,
\]

\[
RVOL^{CC}_{t,21t}
=
\sqrt{RVAR^{CC}_{t,21t}}.
\]

This is a mandatory robustness design, not the primary target. It tests whether the result is sensitive to exact calendar matching versus a fixed-session approximation.

For both horizons, the first target return must end strictly after \(t\).

---

## 7. Alternative realized-variance estimators

Close-to-close squared log returns are primary. Parkinson and Garman–Klass are mandatory robustness estimators.

For day \(s\), Parkinson variance is

\[
v_s^P=
\frac{1}{4\ln2}
\left[\ln(H_s/L_s)\right]^2.
\]

Garman–Klass variance is

\[
v_s^{GK}
=
\frac12\left[\ln(H_s/L_s)\right]^2
-
(2\ln2-1)\left[\ln(C_s/O_s)\right]^2.
\]

For the primary 30-calendar-day target, sum the daily estimator over the same eligible exchange dates as the close-to-close target and annualize by \(365/30\). For the fixed 21-trading-day robustness target, sum exactly the next 21 daily estimates and annualize by \(252/21\).

Their assumptions and sensitivity to opening jumps, overnight moves, and range errors must be discussed. Disagreement among estimators is a result, not a reason to select whichever estimator supports a preferred conclusion.

---

## 8. Overlap-aware inference

Rolling forward targets overlap heavily. Ordinary i.i.d. standard errors are invalid.

### 8.1 Primary 30-calendar-day HAC rule

Estimate the primary mean using

\[
VRP_t^X=\mu+u_t.
\]

Before outcomes are analyzed, derive the primary HAC lag \(L_0\) mechanically from the exchange calendar and eligible forecast-origin sequence: \(L_0\) is the greatest ordered origin lag for which two primary target return-date sets overlap.

Use Newey–West/HAC covariance with a Bartlett kernel and `maxlags=L0`. Report additional sensitivity at lags 42 and 63. No bandwidth is selected by significance.

Report:
- mean \(VRP^X\);
- HAC standard error;
- t-statistic;
- exact two-sided p-value;
- 95% confidence interval;
- sample size.

### 8.2 Non-overlapping primary robustness sample

Starting with the earliest eligible origin, repeatedly select the earliest later origin strictly after the previous target's 30-calendar-day end. Report the mean and uncertainty on this deterministic non-overlapping sample. Alternative phase offsets are appendix-only.

### 8.3 Fixed 21-trading-day inference

For the 21-trading-day robustness design, adjacent targets share 20 of 21 returns. The pre-specified HAC setting is `maxlags=20`, with sensitivity at 10, 21, and 42.

---

## 9. Descriptive diagnostics

Before fitting GARCH, document the relevant properties of S&P 500 returns.

Required outputs:
- mean, standard deviation, skewness, excess kurtosis, selected quantiles;
- return time series;
- histogram/density;
- normal Q–Q plot;
- ACF of returns and squared returns;
- Jarque–Bera test;
- Ljung–Box diagnostics for returns and squared returns;
- ARCH-LM diagnostic;
- a documented leverage-effect diagnostic.

For the primary \(VRP^X\), also report the median, proportion positive, selected quantiles, minimum/maximum with dates, and ACF. Stationarity diagnostics may be reported, but they are not automatic pass/fail rules.

---

## 10. Mincer–Zarnowitz calibration

Primary regression:

\[
RVAR^{CC}_{t,30c}
=
\alpha+\beta IVAR_t+u_t.
\]

Use OLS point estimates with the same overlap-aware HAC rule as the primary target.

Report \(\hat\alpha\), \(\hat\beta\), robust standard errors, 95% confidence intervals, \(R^2\), and the joint Wald test of \(\alpha=0,\beta=1\).

A rejection is a calibration result, not a direct test of rationality.

---

## 11. GARCH(1,1)

Daily return model:

\[
r_t=\mu+\epsilon_t,
\qquad
\epsilon_t=\sigma_t z_t,
\]

\[
\sigma_t^2
=
\omega+\alpha\epsilon_{t-1}^2+\beta\sigma_{t-1}^2.
\]

Primary innovation distribution: Gaussian.  
Mandatory distributional robustness: Student-\(t\).

Report:
- \(\omega,\alpha,\beta\);
- persistence \(\alpha+\beta\);
- convergence status;
- log likelihood;
- standardized-residual diagnostics;
- remaining ARCH effects.

If persistence is near or above one, convergence is poor, or residual ARCH remains material, report it rather than silently replacing the model.

EGARCH, GJR-GARCH, stochastic volatility, HAR-RV, or machine-learning models are extensions rather than substitutes for the core GARCH(1,1).

---

## 12. Out-of-sample design

The primary forecast comparison is genuinely out of sample.

### Initial estimation sample

Use all available valid daily returns through the last S&P 500 trading day of 2006.

### Evaluation period

Begin on the first S&P 500 trading day of 2007 and end at the last 2025 forecast origin with a complete primary target.

### Estimation window

Primary: expanding window, recursively re-estimated using only information available at each origin.  
Mandatory robustness: rolling five-year estimation window.

No future return, future realized target, future VIX observation, or test-period loss may affect any predictor constructed at origin \(t\).

A unit test must establish the leakage invariant: changing any observation after \(t\) cannot change any predictor at \(t\).

---

## 13. Forecast construction and common mask

### 13.1 VIX forecast

The VIX variance forecast is simply

\[
\widehat{GVAR}^{VIX}_{t,30c}=IVAR_t.
\]

### 13.2 GARCH forecast for the primary horizon

Let \(\mathcal D_t\) be the set of future S&P 500 exchange sessions whose return-ending dates satisfy \(t<d\le t+30c\). The exchange calendar is deterministic and may be known at the forecast origin.

If \(\widehat\sigma^2_{t,h|t}\) denotes the daily GARCH conditional-variance forecast for the session corresponding to horizon step \(h\), then

\[
\widehat{GVAR}^{GARCH}_{t,30c}
=
\frac{365}{30}
\sum_{h=1}^{|\mathcal D_t|}
\widehat\sigma^2_{t,h|t}.
\]

The implementation must map forecast horizon steps to exchange dates explicitly and test the mapping before forecast rankings are inspected.

### 13.3 Naive benchmark

The primary naive benchmark mirrors the calendar horizon using only past information:

\[
\widehat{GVAR}^{Naive}_{t,30c}
=
\frac{365}{30}
\sum_{d:t-30c<d\le t} r_d^2.
\]

The fixed 21-trading-day trailing historical variance may be reported with the fixed-21 robustness analysis.

### 13.4 Common-mask rule

Every formal comparison among VIX, GARCH, and the naive benchmark uses:
- identical forecast origins;
- identical realized target;
- identical units;
- identical missing-value mask.

A model may not appear superior because it is evaluated on an easier subset.

---

## 14. Forecast evaluation and encompassing

For model \(m\), define variance forecast error

\[
e_{m,t}=RVAR^{CC}_{t,30c}-\widehat{GVAR}_{m,t,30c}.
\]

Report

\[
RMSE_m=
\sqrt{\frac1N\sum_t e_{m,t}^2},
\]

and

\[
MAE_m=
\frac1N\sum_t |e_{m,t}|.
\]

For formal pairwise inference, compare mean squared-error loss differentials using overlap-aware HAC covariance. A naive Diebold–Mariano test that ignores overlapping targets is prohibited.

QLIKE is a pre-specified robustness loss if every forecast is strictly positive and its implementation is validated.

The encompassing regression is

\[
RVAR^{CC}_{t,30c}
=
\alpha+\beta IVAR_t+\gamma\widehat{GVAR}^{GARCH}_{t,30c}+u_t,
\]

using the common out-of-sample mask and overlap-aware HAC inference.

Forecast superiority is interpreted as relative predictive performance, not as proof or rejection of the Efficient Markets Hypothesis.

---

## 15. Regime analysis

`paper/regime_definitions.md` must be completed and committed before any regime output is calculated.

Formal regime analysis uses the NBER monthly U.S. recession chronology. Each daily origin inherits the status of its calendar month. The regime indicator is ex-post descriptive/classification information only and never enters a forecast.

The 2008, 2020, and 2022 episodes are separate case studies. Required outputs include sample size, VIX/IVAR, realized variance, mean/median \(VRP^X\), and forecast losses where sample size permits.

Crisis observations are not trimmed or winsorized simply because they are extreme.

---

## 16. Track A — Black–Scholes validation rules

The authors implement the European Black–Scholes call/put pricer themselves.

The initial core model may use the no-dividend simplification, but any real SPX option validation must explicitly address dividends, rates, bid/ask spreads, timing, and contract details.

The implied-volatility solver uses Brent's method and must:
- validate \(S>0,K>0,T>0\);
- check economically admissible option-price bounds;
- use a defensible positive volatility bracket;
- fail explicitly if no root is bracketed.

Validation hierarchy:
1. analytical sanity checks;
2. put–call parity;
3. limiting cases;
4. monotonicity in volatility;
5. trusted reference implementation;
6. small real-option sample with caveats documented.

Reference libraries validate the authors' code but never replace it. Track A single-option implied volatility remains conceptually and computationally separate from Track B VIX.

---

## 17. Mandatory robustness hierarchy

The following are pre-specified and must be reported without selecting only favorable results:

1. exact 30-calendar-day primary horizon vs fixed 21-trading-day approximation;
2. close-to-close vs Parkinson vs Garman–Klass realized variance;
3. daily overlapping HAC result vs deterministic non-overlapping sample;
4. primary HAC bandwidth \(L_0\) vs 42 and 63 for the 30-calendar-day target;
5. fixed-21 HAC(20) vs 10, 21, and 42;
6. variance-space \(VRP^X\) vs volatility-space `VOLGAP`;
7. full historical sample vs post-2003 sensitivity;
8. Gaussian vs Student-\(t\) GARCH(1,1);
9. expanding vs five-year rolling GARCH window;
10. full-sample results vs NBER regimes and pre-defined case studies.

Extensions may not replace weak core findings.

---

## 18. Reproducibility, testing, and audit

The core pipeline must reproduce from raw data to final tables and figures without manual editing.

Minimum repository structure:

```text
data/
    raw/
    manifests/
    processed/
src/
notebooks/
tests/
paper/
    method_protocol.md
    regime_definitions.md
    protocol_deviations.md
README.md
pyproject.toml
```

Core tests must cover:
- primary 30-calendar-day date-set construction;
- no same-date return in any forward target;
- complete-target rejection at the sample edge;
- fixed 21-trading-day robustness indexing;
- annualization and units;
- non-negative variance outputs;
- no look-ahead in GARCH or naive forecasts;
- GARCH exchange-calendar horizon mapping;
- common evaluation mask;
- premium sign convention;
- Black–Scholes parity, limiting cases, and monotonicity;
- implied-volatility recovery from synthetic prices.

Before results are accepted, audit:
- source provenance and hashes;
- verified TLS for the final core acquisition;
- row losses and data corrections;
- material Yahoo/FRED discrepancies;
- date alignment;
- units;
- HAC settings;
- OOS split;
- common masks;
- generated-table traceability.

Every number quoted in the final paper must be traceable to code output or a documented external source.

---

## 19. Reporting and interpretation discipline

1. Exact p-values, effect sizes, confidence intervals, and sample sizes take precedence over binary significance language.
2. Failure to reject is not proof of equality.
3. Expected signs from prior literature are never presented as project findings.
4. Null, negative, unstable, or regime-specific results remain in the paper.
5. Positive \(VRP^X\) is not by itself proof of irrationality.
6. VIX outperforming GARCH is consistent with useful option-market information but does not prove full market efficiency.
7. GARCH matching or beating VIX does not by itself prove option-market inefficiency; a risk premium can make a useful option-implied measure a biased forecast of physical variance.
8. S&P 500/VIX results cannot automatically be generalized to all markets.
9. Ex-post realized variance is not the same object as expected physical variance.
10. Statistical significance and economic importance are discussed separately.

---

## 20. Protocol deviations and decision history

A genuine data or implementation constraint may require an amendment. Record every post-lock change in `paper/protocol_deviations.md` with:

1. original rule;
2. reason for change;
3. replacement rule;
4. whether relevant results had already been viewed;
5. likely direction of any resulting bias, if known.

If a specification changes after relevant results have been viewed, the modified analysis is exploratory unless the original pre-specified result is also retained.

Earlier August 10 and August 23 protocol drafts remain part of Git history. `docs/methodology_decisions.md` records how the design evolved before empirical VRP or forecast-ranking results were generated. The present August 26 protocol is authoritative.

---

## 21. Locked implementation defaults

```yaml
protocol_version: "1.0"
protocol_decision_date: "2026-08-26"

sample_start: "1990-01-02"
sample_end: "2025-12-31"

primary_horizon: "30_calendar_days"
primary_calendar_days: 30
primary_calendar_annualization_days: 365

robustness_horizon: "21_trading_days"
robustness_trading_days: 21
trading_days_per_year: 252

primary_empirical_object: "VRP_X = implied_variance - realized_variance"
secondary_empirical_object: "VOLGAP = implied_volatility - realized_volatility"
sign_convention: "implied_minus_realized"

primary_hac_rule: "derive_L0_from_calendar_target_overlap"
primary_hac_sensitivity_maxlags:
  - 42
  - 63
fixed_21_hac_maxlags: 20
fixed_21_hac_sensitivity_maxlags:
  - 10
  - 21
  - 42

significance_level: 0.05
confidence_level: 0.95
test_direction: "two_sided"

garch_model: "GARCH(1,1)"
garch_mean: "constant"
garch_primary_distribution: "normal"
garch_robustness_distribution: "student_t"
garch_primary_window: "expanding"
garch_robustness_window: "5_year_rolling"

oos_initial_estimation_end: "last_trading_day_2006"
oos_start: "first_trading_day_2007"

formal_regime_chronology: "NBER_monthly_business_cycle"
random_seed: 42
```

Changing a locked default requires the deviation procedure above.

---

## 22. Final lock statement

By adopting this protocol, the authors commit to five non-negotiable principles:

1. **Match the economic horizon:** primary realized variance covers the exact forward 30-calendar-day interval targeted by VIX; 21 trading days is mandatory robustness.
2. **Correct time alignment:** VIX at \(t\) is compared only with variance realized after \(t\).
3. **Overlap-aware inference:** rolling forward targets require HAC or non-overlapping robustness.
4. **Genuine out-of-sample forecasting:** no future information enters any forecast.
5. **Conceptual and reproducibility discipline:** VIX, Black–Scholes IV, volatility gaps, variance-risk-premium proxies, and forecast targets remain distinct; inconvenient results are retained.

If later code, notebooks, tables, figures, or prose conflict with this protocol, the protocol controls unless the conflict is transparently documented as an approved deviation.
