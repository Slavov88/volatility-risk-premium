# Pre-Analysis Method Protocol

## The Volatility Risk Premium: An Empirical and Theoretical Investigation of the Gap Between Implied and Realized Volatility in Equity Index Markets

**File:** `paper/method_protocol.md`  
**Protocol version:** 1.0  
**Decision date:** 2026-08-23  
**Tracker task:** W1-03  
**Status:** Locked core-analysis protocol pending co-author review  
**Primary market:** S&P 500 / Cboe VIX  
**Core sample:** first common valid trading date on or after 1990-01-02 through 2025-12-31  
**Primary horizon:** 21 forward S&P 500 trading days  
**Primary significance level:** 5%, two-sided; 95% confidence intervals  
**Core rule:** no specification may be changed because a result is weak, inconvenient, or contrary to the expected sign.

---

## 1. Purpose and scope

This protocol fixes the main empirical and econometric choices before final VRP results are inspected. Its purpose is to reduce researcher degrees of freedom, prevent look-ahead bias, make the analysis reproducible, and clearly separate confirmatory analysis from exploratory extensions.

The project has two related but distinct tracks:

- **Track A — Black–Scholes derivation and small-scale validation.** Derive the Black–Scholes model, implement a European-option pricer and implied-volatility solver, and validate them against reference values and a small set of market quotes.
- **Track B — Large-sample empirical study.** Use the Cboe VIX as the market-implied volatility measure, construct forward realized-volatility targets from S&P 500 prices, estimate the implied–realized volatility gap, fit GARCH forecasts, and evaluate statistical and economic interpretations.

Track A must never be used to redefine Track B. In particular, a single-option Black–Scholes implied volatility is **not** interchangeable with the VIX.

Out of scope for the confirmatory core are trading strategies, option-surface construction, machine learning, Heston calibration, cross-market comparisons, event studies, and return-predictability extensions. These may be attempted only after the core pipeline reproduces from raw data.

---

## 2. Research question and hypotheses

### Primary research question

> Is the observed excess of implied over subsequently realized volatility in the S&P 500 statistically robust and economically explicable as compensation for volatility/tail risk, or does it weaken materially once horizon alignment, overlapping observations, non-normality, forecast design, and regime dependence are handled correctly?

### H1 — Mean implied–realized volatility gap

Let

\[
IVOL_t = \frac{VIX_t}{100}
\]

and let \(RVOL^{CC}_{t,t+21}\) be the annualized close-to-close realized volatility over the next 21 S&P 500 trading days.

Define

\[
VOLGAP_t = IVOL_t - RVOL^{CC}_{t,t+21}.
\]

Test

\[
H_0:E[VOLGAP_t]=0
\]

against the two-sided alternative

\[
H_1:E[VOLGAP_t]\neq0.
\]

The literature-motivated expected sign is positive, but the confirmatory test remains two-sided.

### H2 — VIX calibration

Estimate the Mincer–Zarnowitz regression

\[
RVOL^{CC}_{t,t+21}=\alpha+\beta IVOL_t+u_t
\]

and jointly test

\[
H_0:\alpha=0,\qquad \beta=1.
\]

Rejection is interpreted as forecast miscalibration under this empirical definition, not as proof of irrationality.

### H3 — Out-of-sample forecast accuracy

Compare VIX, GARCH(1,1), and a naive historical-volatility benchmark on identical forecast origins and against the same 21-trading-day realized-volatility target.

Primary reported losses:
- RMSE;
- MAE.

For formal loss-difference inference, squared-error loss is used because overlapping targets induce serial dependence in daily forecast losses. QLIKE may be reported as a pre-specified robustness loss if all forecasts are strictly positive and the implementation is validated.

### H4 — Forecast encompassing

Estimate

\[
RVOL^{CC}_{t,t+21}
=
\alpha+\beta IVOL_t+\gamma \widehat{RVOL}^{GARCH}_{t,t+21}+u_t.
\]

Test whether:
- \(\gamma=0\): GARCH adds no incremental predictive information conditional on VIX;
- \(\beta=0\): VIX adds no incremental predictive information conditional on GARCH.

### H5 — Regime dependence and crisis behavior

Regime dependence will be studied in two complementary ways:

1. **Formal externally defined regime comparison:** recession versus non-recession observations using a frozen external chronology, if that chronology can be acquired reproducibly before regime outputs are inspected.
2. **Pre-defined case studies:** 2008, 2020, and 2022, with exact windows recorded in `paper/regime_definitions.md` before the regime analysis is run.

No crisis window may be moved after seeing the VRP plot to strengthen a narrative.

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

Neither term is directly observed. An ex-post realized outcome is only a noisy proxy for the physical expectation. The empirical analysis must therefore avoid claiming that an ex-post difference directly measures the exact theoretical VRP.

The project uses two empirical objects:

### Primary, interpretable volatility gap

\[
VOLGAP_t=IVOL_t-RVOL_t.
\]

This is reported in annualized volatility units and is the paper's primary descriptive and inferential object because it is intuitive to communicate.

### Variance-space robustness proxy

\[
IVAR_t=IVOL_t^2,
\]

\[
VRP_t^{X}=IVAR_t-RVAR_t.
\]

This is the technically closer analogue to the theoretical variance-risk-premium concept and must be reported as a robustness result.

Terminology rule:
- `VOLGAP` means implied volatility minus realized volatility;
- `VRP^X` means implied variance minus ex-post realized variance;
- “variance risk premium” may be used for the literature concept, but the paper must state clearly which empirical proxy is being reported.

The sign convention is always **implied minus realized**, so positive values mean the market-implied measure exceeded the subsequently realized measure.

---

## 4. Data and provenance

### 4.1 VIX

Primary source: official Cboe historical daily VIX data.

Required field:
- daily VIX close.

Operationally, the daily VIX close at forecast origin \(t\) is treated as the end-of-day predictor. The target begins strictly after \(t\); no same-date S&P 500 return enters the forward realized-volatility target.

The paper will acknowledge a timestamp limitation: the historical daily VIX close and the S&P 500 cash close are not assumed to be perfectly synchronized to the same instant. This is a provenance limitation, not a reason to use same-day future information.

### 4.2 S&P 500

The target asset is the **S&P 500 price index**, not SPY and not a total-return index.

Required fields:
- date;
- open;
- high;
- low;
- close.

Preferred free-source candidate for the exact index is Yahoo Finance `^GSPC` retrieved through a pinned software environment. FRED S&P 500 close data may be used as an overlapping-period validation source. A source discrepancy is reported and investigated; it is never silently replaced by the source that produces a preferred result.

If reliable OHLC coverage begins later than reliable close coverage, the close-to-close core sample may be longer than the Parkinson/Garman–Klass robustness samples. Those sample differences must be explicit.

### 4.3 Risk-free rate

A short Treasury rate is required mainly for Track A option validation. The preferred source is FRED / Federal Reserve H.15. Use the nearest defensible short maturity for the option date and document any transformation to decimal or continuously compounded units.

### 4.4 Raw-data freeze

Every acquisition must record:
- source and endpoint;
- retrieval date;
- request parameters;
- coverage;
- schema;
- missingness summary;
- software version where applicable;
- SHA-256 hash of the stored artifact where practical.

Raw acquisition artifacts are immutable. They are stored under `data/raw/`; all transformations occur in code and produce new files under `data/processed/`.

A current New York trading-date bar must be rejected from any frozen historical acquisition if the session is not complete.

---

## 5. Cleaning, dates, and units

1. Normalize dates to `YYYY-MM-DD` and sort ascending.
2. Use the S&P 500 exchange trading calendar; do not invent observations for weekends or holidays.
3. Duplicate dates must be resolved explicitly.
4. Market prices and VIX are never forward-filled or interpolated.
5. Crisis/extreme observations are never removed merely for being extreme.
6. A row may be removed only for an identified data error, with the reason recorded.
7. OHLC rows must satisfy:
   \[
   High_t\ge\max(Open_t,Close_t),\qquad
   Low_t\le\min(Open_t,Close_t),\qquad
   High_t\ge Low_t,
   \]
   with all prices strictly positive.
8. The cleaning pipeline must produce a row-loss report.

Daily log return:

\[
r_t=\ln(C_t/C_{t-1}).
\]

Canonical annualization:

\[
A=252.
\]

All comparable volatility series are stored in code as **annualized decimals**. Multiplication by 100 is presentation-only.

Canonical constants must live in one shared configuration source; notebooks may not redefine horizon, annualization, sample dates, units, or sign conventions independently.

---

## 6. Primary horizon and realized-volatility targets

### 6.1 Primary target: next 21 trading days

For a valid forecast origin \(t\), the target uses the next 21 S&P 500 trading-day returns only:

\[
t+1,\ldots,t+21.
\]

This alignment is non-negotiable. Today's VIX may never be paired with backward-looking realized volatility.

Primary close-to-close realized variance:

\[
RVAR^{CC}_{t,t+21}
=
\frac{252}{21}
\sum_{j=1}^{21}r_{t+j}^2.
\]

Primary realized volatility:

\[
RVOL^{CC}_{t,t+21}
=
\sqrt{RVAR^{CC}_{t,t+21}}.
\]

The final usable forecast origin must have the complete forward target; targets are never shortened.

### 6.2 Exact 30-calendar-day robustness target

Because the VIX is a constant-maturity approximately 30-calendar-day measure, a pre-specified robustness target uses squared returns whose return-ending exchange dates satisfy

\[
t<d\le t+30\text{ calendar days}.
\]

Define

\[
HVAR_{t,30c}=\sum_{d:t<d\le t+30c}r_d^2,
\]

\[
RVAR_{t,30c}=\frac{365}{30}HVAR_{t,30c},
\]

\[
RVOL_{t,30c}=\sqrt{RVAR_{t,30c}}.
\]

The primary conclusion is based on the fixed 21-trading-day design. The 30-calendar-day design is a robustness check and may not replace it after results are observed.

---

## 7. Alternative realized-volatility estimators

Close-to-close is primary. Parkinson and Garman–Klass are mandatory robustness estimators.

### Parkinson

For day \(s\),

\[
v_s^P=
\frac{1}{4\ln2}
\left[\ln(H_s/L_s)\right]^2.
\]

For the next 21 trading days,

\[
RVAR^P_{t,t+21}
=
\frac{252}{21}
\sum_{j=1}^{21}v^P_{t+j},
\qquad
RVOL^P_{t,t+21}=\sqrt{RVAR^P_{t,t+21}}.
\]

### Garman–Klass

For day \(s\),

\[
v_s^{GK}
=
\frac12\left[\ln(H_s/L_s)\right]^2
-
(2\ln2-1)\left[\ln(C_s/O_s)\right]^2.
\]

Then

\[
RVAR^{GK}_{t,t+21}
=
\frac{252}{21}
\sum_{j=1}^{21}v^{GK}_{t+j},
\qquad
RVOL^{GK}_{t,t+21}=\sqrt{RVAR^{GK}_{t,t+21}}.
\]

Their assumptions and sensitivity to opening jumps, overnight moves, and range errors must be discussed. Disagreement among estimators is an empirical result; it is not grounds for selecting the estimator that supports the preferred conclusion.

---

## 8. Primary inference and overlapping observations

Adjacent 21-day forward targets share 20 of 21 returns. Ordinary i.i.d. standard errors are therefore invalid for the daily overlapping sample.

### 8.1 Mean gap

Estimate an intercept-only regression:

\[
VOLGAP_t=\mu+u_t.
\]

Primary covariance estimator:
- Newey–West / HAC;
- Bartlett kernel;
- `maxlags = 20`;
- finite-sample correction where supported.

Report:
- mean;
- HAC standard error;
- t-statistic;
- exact two-sided p-value;
- 95% confidence interval;
- sample size.

Pre-specified bandwidth sensitivity:
- 10;
- 21;
- 42.

No bandwidth may be selected by significance.

### 8.2 Non-overlapping robustness sample

Construct a deterministic non-overlapping sequence beginning with the earliest eligible forecast origin. After an origin \(t\), choose the earliest later origin whose 21-day target shares no return with the previous selected target.

Report the mean gap and uncertainty on this sample and compare sign/magnitude with the HAC result. Alternative phase offsets may be appendix-only sensitivity checks.

### 8.3 Exact 30-calendar-day HAC robustness

For the 30-calendar-day target, derive the overlap bandwidth from the exchange calendar before outcomes are inspected: \(L_0\) is the greatest origin lag for which two target return-date sets overlap. Report the result at \(L_0\) and additional wider bandwidths such as 42 and 63.

---

## 9. Descriptive diagnostics

Before fitting GARCH, document why constant unconditional volatility and Gaussian i.i.d. returns are inadequate.

Required outputs:
- mean, standard deviation, skewness, excess kurtosis, quantiles;
- return time series;
- histogram/density;
- normal Q–Q plot;
- ACF of returns and squared returns;
- Jarque–Bera test;
- Ljung–Box diagnostics for returns and squared returns;
- ARCH-LM diagnostic;
- a documented leverage-effect diagnostic.

For `VOLGAP`, also report:
- median;
- proportion positive;
- minimum and maximum with dates;
- ACF;
- a stationarity diagnostic such as ADF, interpreted cautiously.

Diagnostics characterize the data; they are not automatic pass/fail switches.

---

## 10. Mincer–Zarnowitz calibration test

Estimate

\[
RVOL^{CC}_{t,t+21}
=
\alpha+\beta IVOL_t+u_t.
\]

Use OLS point estimates with HAC covariance and `maxlags = 20`.

Report:
- \(\hat\alpha\);
- \(\hat\beta\);
- HAC standard errors;
- 95% confidence intervals;
- \(R^2\);
- joint Wald test of \(\alpha=0,\beta=1\).

A rejection does not establish irrationality. It may be consistent with a risk premium, measurement error, or forecast bias under the chosen target definition.

---

## 11. GARCH(1,1)

Primary return model:

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

Primary innovation distribution:
- Gaussian.

Pre-specified robustness:
- Student-\(t\).

Report:
- \(\omega,\alpha,\beta\);
- persistence \(\alpha+\beta\);
- convergence status;
- log likelihood;
- standardized-residual diagnostics;
- remaining ARCH effects.

If persistence is near or above one, or convergence is poor, this must be reported rather than hidden by silently replacing the model.

EGARCH/GJR-GARCH are extensions, not substitutes for the primary GARCH(1,1).

---

## 12. Out-of-sample design

The forecast comparison is genuinely out of sample.

### Initial estimation sample

Use all available return data through the **last S&P 500 trading day of 2006**.

### Evaluation period

Begin on the **first S&P 500 trading day of 2007** and end at the last forecast origin in 2025 with a complete forward target.

### Estimation window

Primary:
- expanding window;
- model re-estimated recursively using only information available at each forecast origin.

Robustness:
- rolling five-year window.

No future return, future VIX value, realized target, or test-period forecast loss may influence a predictor at origin \(t\).

A unit test must demonstrate the leakage invariant:

> changing any observation dated after \(t\) cannot change any predictor constructed for \(t\).

---

## 13. Forecast construction and common evaluation mask

### 13.1 GARCH forecast

At origin \(t\), let \(\widehat{\sigma}_{t+h|t}^2\) be the daily conditional-variance forecast.

Construct the 21-trading-day annualized forecast:

\[
\widehat{RVAR}^{GARCH}_{t,t+21}
=
\frac{252}{21}
\sum_{h=1}^{21}\widehat{\sigma}_{t+h|t}^2,
\]

\[
\widehat{RVOL}^{GARCH}_{t,t+21}
=
\sqrt{\widehat{RVAR}^{GARCH}_{t,t+21}}.
\]

If returns are scaled by 100 for estimation, forecasts must be converted back correctly before evaluation.

### 13.2 Naive benchmark

Primary naive forecast:

\[
\widehat{RVAR}^{Naive}_{t,t+21}
=
\frac{252}{21}\sum_{j=0}^{20}r_{t-j}^2,
\]

\[
\widehat{RVOL}^{Naive}_{t,t+21}
=
\sqrt{\widehat{RVAR}^{Naive}_{t,t+21}}.
\]

### 13.3 Common-mask rule

Every formal comparison among VIX, GARCH, and the naive benchmark must use:
- identical forecast origins;
- identical realized target;
- identical units;
- identical missing-value mask.

No model may appear superior because it was evaluated on an easier subset.

---

## 14. Forecast evaluation and encompassing

For model \(m\),

\[
e_{m,t}=RVOL^{CC}_{t,t+21}-\widehat{RVOL}_{m,t,t+21}.
\]

Report:

\[
RMSE_m=
\sqrt{\frac1N\sum_t e_{m,t}^2},
\]

\[
MAE_m=
\frac1N\sum_t |e_{m,t}|.
\]

For formal pairwise inference, compare mean squared-error loss differentials with HAC covariance that accounts for the 21-day overlap. A naive Diebold–Mariano test is prohibited.

QLIKE may be reported as a robustness loss if all forecasts are positive and its implementation is validated.

The encompassing regression is

\[
RVOL^{CC}_{t,t+21}
=
\alpha+\beta IVOL_t+\gamma\widehat{RVOL}^{GARCH}_{t,t+21}+u_t,
\]

using the common out-of-sample mask and HAC inference.

Interpretation is limited to **incremental predictive information**. Forecast superiority is not equivalent to full market efficiency.

---

## 15. Regime analysis

Before any regime output is calculated, `paper/regime_definitions.md` must record:
- exact dates or chronology source;
- the economic rationale;
- the mapping rule from chronology to daily forecast origins;
- whether a regime variable is descriptive or used in a formal test.

The 2008, 2020, and 2022 episodes remain separate case studies. Required outputs include sample size, VIX, realized volatility, mean/median `VOLGAP`, and forecast losses where the sample is sufficient.

Crisis observations are never trimmed or winsorized simply because they dominate the distribution.

---

## 16. Track A: Black–Scholes validation rules

The authors will implement the Black–Scholes European call/put pricer themselves.

Core assumptions must be stated explicitly, including the initial no-dividend simplification.

The implied-volatility solver uses Brent's method and must:
- validate \(S>0,K>0,T>0\);
- check economically admissible option-price bounds;
- use a defensible positive volatility bracket;
- fail explicitly when no root is bracketed.

Validation hierarchy:
1. analytical sanity checks;
2. put–call parity;
3. limiting cases;
4. monotonicity in volatility;
5. comparison with a trusted reference implementation;
6. small real-option sample with bid/ask, dividends, rates, timing, and contract caveats documented.

Reference libraries may validate the authors' implementation but never replace it.

Track A single-option implied volatility remains separate from Track B VIX throughout code and prose.

---

## 17. Mandatory robustness hierarchy

The following are pre-specified and must be reported without selecting only favorable results:

1. close-to-close vs Parkinson vs Garman–Klass;
2. daily overlapping HAC result vs deterministic non-overlapping sample;
3. HAC bandwidth 20 vs 10, 21, and 42;
4. 21-trading-day primary horizon vs exact 30-calendar-day robustness horizon;
5. volatility-space `VOLGAP` vs variance-space `VRP^X`;
6. full historical sample vs post-2003 VIX-methodology-era sensitivity;
7. Gaussian vs Student-\(t\) GARCH(1,1);
8. expanding vs five-year rolling GARCH window, if computationally feasible;
9. full-sample results vs pre-defined regimes.

Extensions may not replace weak core findings.

---

## 18. Reproducibility, testing, and audit

The core pipeline must reproduce from raw data to final tables and figures without manual editing.

Minimum repository structure:

```text
data/
    raw/
    processed/
src/
notebooks/
tests/
paper/
    method_protocol.md
    regime_definitions.md
README.md
requirements.txt or pyproject.toml
```

Core tests must cover:
- forward-window indexing;
- no same-day return in the target;
- correct 21-day horizon;
- annualization and units;
- non-negative variance outputs;
- no look-ahead in GARCH forecasts;
- common evaluation mask;
- premium sign convention;
- Black–Scholes parity and monotonicity;
- implied-volatility recovery from synthetic prices.

Before results are accepted, audit:
- source provenance and hashes;
- row losses;
- date alignment;
- units;
- HAC settings;
- OOS split;
- target equality across models;
- generated-table traceability.

Every number quoted in the final paper must be traceable to code output or a documented external source.

---

## 19. Reporting and interpretation discipline

1. Exact p-values, effect sizes, confidence intervals, and sample sizes take precedence over binary significance language.
2. A failure to reject is not proof of equality.
3. Expected signs from prior literature are never presented as findings.
4. Null, negative, unstable, or regime-specific results remain in the paper.
5. A positive `VOLGAP` is not by itself proof of irrationality.
6. VIX outperforming GARCH is consistent with useful option-market information but does not prove full market efficiency.
7. GARCH matching or beating VIX does not by itself prove option-market inefficiency; a risk premium may make VIX a biased physical-volatility forecast.
8. The S&P 500/VIX result cannot automatically be generalized to all markets.
9. Ex-post realized variance is not the same object as expected physical variance.
10. Statistical significance and economic importance must be discussed separately.

---

## 20. Protocol deviations and lock rule

If a genuine data or implementation constraint requires a change, record it in:

`paper/protocol_deviations.md`

with:
1. original rule;
2. reason for change;
3. replacement rule;
4. whether relevant results had already been viewed;
5. likely direction of any resulting bias, if known.

If a specification is changed after relevant results have been viewed, the modified analysis is exploratory unless the original pre-specified result is also retained.

No original protocol history may be deleted.

---

## 21. Locked implementation defaults

```yaml
sample_start: "1990-01-02"
sample_end: "2025-12-31"

annualization_days: 252
primary_horizon_trading_days: 21
robustness_horizon_calendar_days: 30

primary_rv: "close_to_close"
robustness_rv:
  - "parkinson"
  - "garman_klass"

primary_empirical_object: "VOLGAP = implied_volatility - realized_volatility"
variance_robustness_object: "VRP_X = implied_variance - realized_variance"

primary_hac_kernel: "bartlett"
primary_hac_maxlags: 20
hac_sensitivity_maxlags:
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

naive_forecast_window: 21
random_seed: 42
```

Changing a locked default requires the deviation procedure above.

---

## 22. Final lock statement

By adopting this protocol, the authors commit to five non-negotiable principles:

1. **Correct time alignment:** VIX at \(t\) is compared only with volatility realized after \(t\).
2. **Overlap-aware inference:** rolling forward targets require HAC or non-overlapping robustness.
3. **Genuine out-of-sample forecasting:** no future information enters any forecast.
4. **Conceptual precision:** VIX, Black–Scholes implied volatility, volatility gaps, and variance-risk-premium proxies remain distinct.
5. **Reproducibility over storytelling:** specifications are not changed to manufacture significance, and inconvenient results are retained.

If later code, notebooks, tables, figures, or prose conflict with this protocol, the protocol controls unless the conflict is transparently documented as an approved deviation.
