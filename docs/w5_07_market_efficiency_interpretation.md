# W5-07 — Interpreting VIX versus GARCH forecast rankings

**Workstream:** Market efficiency

**Role:** Econometrics

**Dependency:** W5-04

**Status:** pre-results interpretation decision tree; no change to the locked
empirical protocol

This note fixes the language used if VIX beats, statistically ties, or loses to
GARCH in the full out-of-sample period or in pre-defined subperiods. It does
not predict a ranking. All statements concern forecasts of the locked realized-
variance target, not the quality of option prices for every economic purpose.

## What is being compared

At forecast origin \(t\), the two primary forecasts are

\[
\widehat{GVAR}^{VIX}_{t,30c}=IVAR_t=(VIX_t/100)^2
\]

and the recursively estimated Gaussian GARCH(1,1) forecast summed over the
exchange sessions in the same exact forward 30-calendar-day interval. Both are
evaluated against

\[
RVAR^{CC}_{t,30c}
=\frac{365}{30}\sum_{d:t<d\le t+30c}r_d^2.
\]

The comparison uses the common out-of-sample mask beginning in 2007. Squared-
error loss is the locked basis for formal pairwise inference. Define

\[
d_t
=\left(RVAR_t-\widehat{GVAR}^{VIX}_t\right)^2
-\left(RVAR_t-\widehat{GVAR}^{GARCH}_t\right)^2.
\]

Thus \(\bar d<0\) favors VIX and \(\bar d>0\) favors GARCH. Inference for
\(\bar d\) uses the locked overlap-aware HAC covariance. RMSE and MAE are also
reported, but MAE has no pre-specified pairwise significance test. QLIKE, the
21-trading-day horizon, Student-\(t\) innovations, and the five-year rolling
window remain robustness results and cannot replace the primary classification.

## Decision tree

Use the tree separately for the full evaluation sample, NBER recession and
non-recession origins, and each pre-defined case study where the comparison and
its HAC covariance are estimable. Always report the estimate, HAC confidence
interval, exact two-sided p-value, and sample size; otherwise report that no
ranking can be estimated.

```text
1. Is the comparison valid and its HAC covariance estimable?
   ├─ No common target, units, origins, mask, complete horizon, or adequate data
   │  └─ Stop: no economic ranking is interpretable.
   └─ Yes
      │
      2. Was the subperiod fixed without using forecast losses?
      ├─ No
      │  └─ Label exploratory; do not use it to qualify the confirmatory result.
      └─ Yes: NBER chronology or frozen 2008/2020/2022 window
         │
         3. Where is the HAC 95% CI for mean squared-loss difference d?
         ├─ Entirely below zero
         │  └─ "VIX beats GARCH under squared-error loss."
         ├─ Contains zero
         │  └─ "The ranking is statistically unresolved."
         │     Do not claim equality or equivalence.
         └─ Entirely above zero
            └─ "GARCH beats VIX under squared-error loss."
               │
               4. Do RMSE, MAE, or robustness results point differently?
               ├─ Yes
               │  └─ Report loss/specification sensitivity; retain the
               │     squared-error primary classification.
               └─ No
                  └─ Describe directional consistency, not universal dominance.
```

“Tie” is therefore shorthand for **failure to distinguish mean squared losses
at the pre-specified significance level**. It is not an equivalence result.
The protocol contains neither an equivalence margin nor an equivalence test.
Likewise, statistical dominance can be economically small, while an
economically sizable estimated difference can remain imprecise. The loss
difference and its confidence interval must accompany either statement.

## If VIX beats GARCH

### What the result supports

- For the specified origins, target, and squared-error loss, the option-implied
  measure has lower average loss than the recursively estimated GARCH(1,1)
  benchmark.
- The result is consistent with SPX option prices aggregating forward-looking
  information beyond the historical-return dynamics represented by that
  GARCH specification.
- If VIX also has a nonzero coefficient in the encompassing regression
  conditional on GARCH, the evidence for incremental VIX predictive content is
  stronger than a loss ranking alone.
- If the advantage appears in several pre-defined subperiods with similar
  effect sizes, it indicates stability of this relative ranking within the
  observed sample. A recession- or crisis-specific advantage is consistent
  with option prices adapting faster than a backward-looking GARCH model when
  volatility conditions change abruptly.

### What the result does not support

- It does not prove that VIX is calibrated or unbiased for physical realized
  variance. VIX may have lower loss while retaining a positive average
  implied-minus-realized gap.
- It does not prove that GARCH contains no useful information. That is a
  separate encompassing question, and failure to reject its coefficient is
  not proof that the coefficient is zero.
- It does not establish that VIX is the best available forecast. GARCH(1,1) is
  one restricted benchmark, not the entire public information set or the set
  of feasible forecasting models.
- It does not prove arbitrage-free pricing, rational expectations, semi-strong
  efficiency, or “full” market efficiency. Forecast accuracy is not a test of
  whether a feasible trading strategy earns abnormal risk-adjusted returns
  after costs.

## If the ranking is statistically unresolved

### What the result supports

- The sample does not distinguish the two models' mean squared losses with the
  locked overlap-aware test.
- Similar point estimates may be consistent with both forecasts using common
  information, while offsetting strengths across dates can also generate a
  small average difference.
- In short or volatile subperiods, wide intervals may reflect limited effective
  information from overlapping targets rather than genuine similarity.
- Encompassing results can still show incremental information even when
  average losses are not distinguishable. Conversely, both encompassing
  coefficients may be imprecisely estimated because the forecasts are highly
  correlated.

### What the result does not support

- It does not prove equal predictive accuracy, economic equivalence, or equal
  information content.
- It does not prove that option and return markets process information equally
  efficiently.
- It does not show that the variance risk premium is zero. Forecast ranking and
  the mean `VRP_X` test answer different questions.
- It does not justify selecting whichever model has the numerically lower RMSE
  or whichever robustness result is more convenient.

The preferred wording is “statistically unresolved” or “not distinguishable
under the pre-specified squared-error test,” not “the models are the same.”

## If GARCH beats VIX

### What the result supports

- For the specified origins, target, and squared-error loss, the historical-
  return GARCH benchmark has lower average loss than unadjusted VIX variance.
- The result is consistent with GARCH tracking physical conditional variance
  more closely over that sample or subperiod.
- It is also consistent with time-varying variance-risk compensation, option
  demand, intermediary constraints, or measurement/contract basis adding
  variation to VIX that is relevant to option pricing but penalized by a
  physical-variance loss function.
- If GARCH has incremental encompassing power conditional on VIX, that supports
  information in return dynamics not fully represented by unadjusted VIX.

### What the result does not support

- It does not by itself prove option-market inefficiency or irrationality.
  VIX is an option-price-based risk-neutral variance measure, not a definitionally
  unbiased forecast of \(E_t^P[V]\). A rational risk premium can make it a worse
  forecast of subsequently realized physical variance.
- It does not show that VIX contains no information. VIX may lose on average
  yet retain incremental encompassing power, or perform better under absolute
  loss or in another pre-specified regime.
- It does not identify whether the loss disadvantage comes from risk
  compensation, beliefs, market frictions, index construction, realized-
  variance measurement, or finite-sample shocks.
- It does not imply a profitable trade. Turning a forecast difference into an
  investment claim requires a traded payoff, position rule, transaction and
  funding costs, and adjustment for systematic and tail risk, none of which is
  tested here.

## How to read subperiod reversals

Subperiod rankings are conditional descriptions, not independent verdicts on
market efficiency.

| Pattern | Defensible interpretation | Prohibited shortcut |
|---|---|---|
| VIX wins overall and in most subperiods | Relatively stable superiority to this GARCH benchmark under the stated loss. | “Options markets are fully efficient.” |
| VIX wins overall but loses in a crisis year | Average superiority masks episode-specific weakness; abrupt realized shocks, a changing premium, or model dynamics may matter. | Dropping the crisis or moving its boundaries. |
| GARCH wins in expansions; VIX wins in recessions | Relative performance is state-dependent in sample and is consistent with faster option-market adjustment in stress. | Claiming an implementable regime-switching forecast, because NBER labels are ex post. |
| VIX wins in expansions; GARCH wins in recessions | VIX's physical-forecast loss may rise when risk premia, option demand, or tail realizations change sharply. | Treating this as proof of crisis mispricing. |
| Results are unresolved in one or more regimes | Precision is insufficient to rank the models there; small subperiods and overlap may be important. | Calling the models equivalent. |
| Rankings differ by RMSE, MAE, or robustness design | Relative performance depends on which forecast errors are emphasized or on the pre-specified alternative design. | Choosing the favorable loss or promoting robustness to primary. |

NBER status is assigned after the fact and never enters a forecast. The annual
2008, 2020, and 2022 windows each contain one historical episode and are
descriptive even though their boundaries were frozen before results. A ranking
reversal across them can motivate a mechanism for future research, but it
cannot establish a repeatable state-contingent rule. Multiple reported
subperiods also create opportunities for chance differences; interpretation
must consider the full pattern rather than elevate one isolated p-value.

## Encompassing, calibration, and the mean premium are separate axes

The economic reading must combine results without collapsing distinct tests:

1. **Loss ranking:** Which forecast has lower average loss?
2. **Encompassing:** Does either forecast add conditional predictive content
   beyond the other?
3. **Calibration:** Does VIX satisfy \(\alpha=0,\beta=1\) for the specified
   physical realized-variance target?
4. **Mean ex-post proxy:** Is average \(IVAR-RVAR\) different from zero?

A VIX loss win can coexist with calibration rejection and a positive mean
`VRP_X`: a risk-premium-bearing measure may be biased yet more informative
than GARCH. A GARCH loss win can coexist with significant incremental VIX
content: one forecast may improve the average prediction while the other still
contains orthogonal information. These combinations are not contradictions.

In the encompassing regression

\[
RVAR_t=\alpha+\beta IVAR_t+\gamma\widehat{GVAR}^{GARCH}_t+u_t,
\]

rejection of \(\gamma=0\) supports incremental GARCH content conditional on
VIX, while rejection of \(\beta=0\) supports incremental VIX content
conditional on GARCH. Failure to reject either restriction is absence of
strong evidence, not proof of no incremental content. Coefficients and their
confidence intervals take precedence over binary labels.

## The market-efficiency boundary

This design can support a narrow statement about **relative predictive
information**. It cannot deliver a general market-efficiency verdict, for four
reasons:

1. VIX is a traded-option price transform under the risk-neutral measure,
   whereas the target is an ex-post physical-measure outcome.
2. GARCH(1,1) is only one public-information benchmark; beating it does not
   show that all available information is in prices, and losing to it does not
   identify a pricing error.
3. Forecast loss is not investor utility or abnormal return. No implementable
   strategy, costs, risk exposure, or equilibrium expected return is evaluated.
4. Any claim of mispricing is joint with a model of the time-varying variance
   risk premium and the mapping from VIX to the traded payoff and realized
   target.
5. Predictability of a conditional second moment is not, by itself,
   predictability of abnormal equity or option returns. Market efficiency does
   not require volatility to be constant or unpredictable.

Accordingly, the strongest permissible conclusion is:

> The evidence ranks VIX and GARCH as forecasts of a pre-specified realized-
> variance target and may reveal incremental or regime-dependent predictive
> content. It does not, by itself, prove or reject full market efficiency.

## Reporting templates

**VIX beats:**

> VIX variance had lower mean squared forecast loss than GARCH in [period],
> with a HAC mean loss difference of [estimate] (95% CI [lower, upper],
> \(p=[p]\), \(N=[N]\)). This supports relative predictive content in the
> option-implied measure against the specified GARCH benchmark; it is not a
> test of full market efficiency.

**Statistically unresolved:**

> The mean squared-loss difference in [period] was not distinguishable from
> zero under overlap-aware inference ([estimate], 95% CI [lower, upper],
> \(p=[p]\), \(N=[N]\)). This is an unresolved ranking, not evidence that the
> forecasts are equivalent.

**GARCH beats:**

> GARCH had lower mean squared forecast loss than VIX variance in [period],
> with a HAC mean loss difference of [estimate] (95% CI [lower, upper],
> \(p=[p]\), \(N=[N]\)). This supports superior physical-variance forecasting
> by this benchmark in the stated sample; it does not establish option-market
> inefficiency because VIX can rationally include risk compensation and other
> pricing components.

## Protocol boundary

This decision tree leaves unchanged the exact 30-calendar-day primary target,
21-trading-day robustness, variance units, annualization, OOS split, common
mask, overlap-aware HAC inference, deterministic non-overlap robustness,
GARCH specifications, formal NBER regimes, and frozen case-study windows. No
ranking may be used to alter those choices, redefine a case-study boundary, or
promote a favorable robustness result.
