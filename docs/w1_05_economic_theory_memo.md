# Why implied variance can exceed realized variance

**Tracker task:** W1-05  
**Workstream:** Economic theory  
**Role:** Econometrics  
**Status:** Structured theory memo; no change to the locked empirical protocol

## Executive conclusion

A positive implied-minus-realized variance gap is compatible with rational,
arbitrage-free markets. No-arbitrage replication explains how a strip of SPX
options can reveal the price of a future-variance payoff. It does **not** imply
that the resulting risk-neutral expectation must equal either the physical
conditional expectation or the variance that is eventually realized. If high
variance tends to occur in states in which investors' marginal utility is high,
variance and especially downside options provide insurance in bad states.
Risk-averse buyers can therefore rationally accept a negative average return on
that insurance, while sellers require compensation for bearing crash and
volatility risk. In equilibrium, this can make risk-neutral expected variance
exceed physical expected variance.

For this project, the theoretical object is

\[
VRP_t^{theory}
=E_t^Q[V_{t,T}]-E_t^P[V_{t,T}],
\]

where \(V_{t,T}\) denotes future variance over the relevant horizon. The
observable primary quantity is instead

\[
VRP_t^X=IVAR_t-RVAR^{CC}_{t,30c},
\qquad IVAR_t=(VIX_t/100)^2.
\]

The latter is an **ex-post variance-risk-premium proxy**, not a direct
observation of \(VRP_t^{theory}\). A positive average proxy is consistent with
a positive price of variance or tail risk, but it does not by itself identify
preferences, prove market efficiency, or establish that every option was
priced rationally.

## 1. What no-arbitrage does and does not say

### 1.1 Replication gives a relative price

An arbitrage is a trading strategy with non-positive initial cost whose
terminal payoff is non-negative almost surely and strictly positive with
positive probability. If a derivative payoff can be
replicated exactly by traded assets, the law of one price requires the
derivative and replicating portfolio to have the same price. Otherwise, one
could buy the cheaper payoff and sell the more expensive identical payoff.

In the Black--Scholes setting, continuous delta hedging replicates a European
option. This removes the stock's physical drift from the pricing equation and
leads to valuation under a risk-neutral measure \(Q\). This is the central
no-arbitrage result in [Black and Scholes
(1973)](https://doi.org/10.1086/260062). It is a statement about internally
consistent prices conditional on the model and trading assumptions, not a
claim that investors are risk-neutral in the real world.

For variance, the corresponding model-free intuition uses a continuum of
out-of-the-money puts and calls, together with dynamic trading in the
underlying, to synthesize a variance-like payoff. Schematically, the option
component of a fair variance rate has the form

\[
\frac{2}{T}\left[
\int_0^F \frac{P_t(K)}{K^2}\,dK
+\int_F^\infty \frac{C_t(K)}{K^2}\,dK
\right],
\]

with adjustments for the forward and the precise contract definition. The
\(1/K^2\) weighting shows why prices across many strikes, including downside
puts, matter. [Carr and Wu (2009)](https://doi.org/10.1093/rfs/hhn038) develop
the variance-swap replication and variance-risk-premium interpretation.

VIX operationalizes related model-free option-strip logic using discrete SPX
strikes and interpolation to a constant 30-calendar-day maturity. It is quoted
as 100 times annualized expected volatility, so this project's variance-space
quantity is \(IVAR_t=(VIX_t/100)^2\). VIX is not the Black--Scholes implied
volatility of one option; the governing operational definition is the [Cboe
VIX methodology](https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf).

### 1.2 No-arbitrage does not equate \(Q\) and \(P\)

No-arbitrage supports the existence of positive state prices, or equivalently
a stochastic discount factor under standard regularity conditions. It does
not require those state prices to be proportional to physical probabilities.
The \(Q\) measure reweights states by their marginal value to investors.

Let \(m_{t,T}\) be a stochastic discount factor and define its normalized form

\[
M_{t,T}=\frac{m_{t,T}}{E_t^P[m_{t,T}]},
\qquad E_t^P[M_{t,T}]=1.
\]

For a payoff \(X_T\), risk-neutral and physical expectations are related by

\[
E_t^Q[X_T]=E_t^P[M_{t,T}X_T].
\]

It follows immediately that

\[
E_t^Q[X_T]-E_t^P[X_T]
=\operatorname{Cov}_t^P(M_{t,T},X_T).
\]

Applying this identity to future variance gives

\[
VRP_t^{theory}
=\operatorname{Cov}_t^P(M_{t,T},V_{t,T}).
\]

Thus a positive variance risk premium has a standard equilibrium
interpretation: high-variance outcomes occur disproportionately in states with
a high stochastic discount factor. Those are states in which an extra unit of
wealth is especially valuable. Replication pins down the price of exposure to
those states; preferences and risks determine why that price differs from the
physical mean payoff.

### 1.3 Replication is not costless insurance in actual markets

The clean replication result relies on idealizations. Actual variance exposure
is affected by discrete strikes, finite strike ranges, jumps, trading costs,
margin, funding, discrete rebalancing, and counterparty or settlement details.
Deep out-of-the-money puts can be particularly costly or difficult to hedge in
a crash. These frictions do not license arbitrary prices—static bounds and
cross-strike consistency still matter—but they can make the supply of crash
insurance costly and less than perfectly elastic.

## 2. Risk aversion and the demand for crash insurance

### 2.1 Why investors buy expensive protection

Equity-market volatility is not merely an isolated statistical fluctuation.
Large volatility realizations often coincide with falling equity wealth,
tighter financing conditions, and deteriorating investment or consumption
opportunities. A risk-averse investor values a payoff more when it arrives in
such a bad state than when it arrives in an ordinary state.

An out-of-the-money index put has exactly this insurance profile: it can pay
off sharply when the aggregate market falls. A long variance position is less
purely directional, but also tends to pay when realized variation surges,
including during market stress. The willingness to pay for these state-
contingent payoffs can exceed their undiscounted physical expected payoff.
Consequently, an insurance buyer can rationally expect to lose money on
average, just as a household can rationally pay more in an insurance premium
than its actuarially expected claim.

This does not mean every investor must be risk-averse in the same way. It is
enough that the marginal investor values wealth in high-volatility states and
that bearing the opposite exposure consumes risk-bearing capacity. The
equilibrium option price balances demand for protection against the willingness
and capacity of dealers or other investors to sell it.

### 2.2 Why option demand can affect implied variance

Options are in zero net supply once long and short positions are consolidated,
but their *price* need not equal an actuarial forecast. If end users have strong
demand for index puts or variance exposure, intermediaries take the other side.
Those intermediaries can delta-hedge ordinary directional exposure, yet remain
exposed to volatility changes, jumps, correlation, discrete hedging error, and
funding needs. Prices adjust until the marginal supplier is willing to bear
those residual risks.

Demand therefore enters the chain as follows:

\[
\text{bad-state covariance}
\longrightarrow
\text{insurance demand}
\longrightarrow
\text{high option/variance-payoff prices}
\longrightarrow
E_t^Q[V]>E_t^P[V].
\]

This is an equilibrium risk-premium account, not an arbitrage. Demand cannot
push otherwise identical payoffs to different prices without creating a trade,
but it can change the common arbitrage-free price by changing the compensation
required to hold the unhedgeable aggregate risk. Demand-based option-pricing
models formalize this mechanism; see [Gârleanu, Pedersen, and Poteshman
(2009)](https://doi.org/10.1093/rfs/hhn075).

### 2.3 The sign from the buyer's and seller's perspectives

This project defines the premium as risk-neutral minus physical expected
variance:

\[
E_t^Q[V]-E_t^P[V].
\]

Under the insurance interpretation, its expected sign is positive. A long
variance buyer pays a high swap rate or option-strip price relative to the
physical mean variance payoff. The long side therefore accepts a negative
expected excess payoff as an insurance premium; the short side earns positive
expected compensation for bearing volatility and crash exposure.

Some papers define the variance risk premium with the opposite sign,
\(E_t^P[V]-E_t^Q[V]\), and consequently call it negative. These conventions
describe the same economics when mapped correctly. This repository always
uses **implied minus realized** for the empirical proxy and \(Q-P\) for the
theoretical object.

Evidence from delta-hedged option returns is consistent with compensation for
volatility risk, although it is not identical to this project's estimand; see
[Bakshi and Kapadia
(2003)](https://doi.org/10.1093/rfs/16.2.527).

## 3. From theoretical premium to the observed `IVAR - RVAR` gap

Let \(V_{t,T}^{*}\) denote the future variance payoff that is conceptually
matched to the option-strip price. The project's observed proxy can be
decomposed schematically as

\[
\begin{aligned}
IVAR_t-RVAR^{CC}_{t,30c}
={}&\underbrace{E_t^Q[V_{t,T}^{*}]-E_t^P[V_{t,T}^{*}]}_{\text{theoretical variance risk premium}}\\
&+\underbrace{E_t^P[V_{t,T}^{*}]-V_{t,T}^{*}}_{\text{physical-measure forecast error}}\\
&+\underbrace{V_{t,T}^{*}-RVAR^{CC}_{t,30c}}_{\text{measurement/contract basis}}\\
&+\underbrace{IVAR_t-E_t^Q[V_{t,T}^{*}]}_{\text{index/replication approximation}}.
\end{aligned}
\]

The last term would vanish under an exact mapping between VIX-squared and the
matched risk-neutral variance payoff. It is retained here because the empirical
target is close-to-close realized variance, while VIX follows a specific
option-strip methodology; jumps, monitoring, truncation, timing, and other
implementation details can prevent literal equality.

This decomposition delivers four interpretation rules.

1. **One realization is not a conditional expectation.** Even if \(IVAR_t\)
   perfectly represented \(E_t^Q[V]\), the subsequent \(RVAR_t\) is one noisy
   draw, not \(E_t^P[V]\).
2. **A positive sample mean can estimate a premium only with qualifications.**
   Physical forecast errors average to zero in population under correct
   conditional measurement, but finite samples, rare disasters, and basis
   terms can materially affect the ex-post mean.
3. **Forecast bias does not establish irrationality.** A rational option price
   is a discounted state-contingent price, not necessarily an unbiased
   physical forecast. Mincer--Zarnowitz rejection is therefore evidence of
   empirical miscalibration under the stated target, not proof of inefficiency.
4. **The gap can reverse locally.** During an unexpected volatility spike,
   realized variance may exceed previously implied variance. Negative daily or
   episode-level `VRP_X` observations are entirely compatible with a positive
   conditional or unconditional insurance premium.

The empirical literature documents economically important variance-premium
behavior across equity indices. [Carr and Wu
(2009)](https://doi.org/10.1093/rfs/hhn038) is especially close to the
variance-replication interpretation, while [Bollerslev, Tauchen, and Zhou
(2009)](https://doi.org/10.1093/rfs/hhp008) provides an equilibrium-motivated
application. These studies motivate an expected sign; they do not predetermine
this project's estimates.

## 4. Why `IV > RV` is useful shorthand but not the primary estimand

Market discussion often says implied volatility exceeds realized volatility.
In this project the formal primary comparison is in variance space:

\[
IVAR_t-RVAR_t,
\]

because variance is the additive payoff connected most directly to the option
strip and variance-swap replication. The secondary communication measure is

\[
VOLGAP_t=IVOL_t-RVOL_t.
\]

The two measures have the same sign at a given observation because the square
root is increasing for non-negative inputs. Their magnitudes and averages are
generally not interchangeable because the square-root transformation is
nonlinear; in particular, \(\sqrt{E[IVAR-RVAR]}\) should not be used unless
its domain and purpose are explicitly justified.

Accordingly, this memo uses “`IV > RV`” only as intuitive shorthand. All
primary inference follows the locked variance-space definition.

## 5. Competing explanations and what the design can distinguish

A positive average `VRP_X` is consistent with several non-exclusive channels:

- compensation for covariance with bad aggregate states;
- demand for crash protection and limited intermediary risk-bearing capacity;
- jump, tail, correlation, liquidity, funding, or discrete-hedging risks borne
  by option sellers;
- differences between the VIX construction and close-to-close realized
  variance;
- finite-sample forecast errors, especially when rare crises are influential.

Behavioral beliefs, segmented demand, or mispricing are possible additional
explanations, but they are not the default inference merely because implied
variance exceeds subsequently realized variance. Distinguishing preference-
based risk compensation from intermediary constraints, beliefs, or measurement
basis requires instruments or structural restrictions beyond a mean-gap test.

The locked empirical design can establish whether the ex-post gap is robust to
horizon alignment, realized-variance estimator, overlap-aware inference,
sample period, and regimes. Calibration and out-of-sample comparisons can show
whether VIX is biased for the chosen physical realized-variance target and how
its predictive loss compares with GARCH and a naive benchmark. Those exercises
cannot, on their own, recover investor risk aversion, isolate crash-insurance
demand, or adjudicate market rationality.

## 6. Interpretation language for later results

If the estimated mean `VRP_X` is positive, an appropriate conclusion is:

> The positive implied-minus-realized variance proxy is consistent with
> compensation for volatility and tail risk: option prices weight adverse,
> high-variance states more heavily than their physical probabilities. Because
> the proxy also contains realized-variance forecast error and measurement
> basis, the estimate is not by itself a structural measure of risk aversion or
> evidence for or against market rationality.

If it is weak, unstable, or negative, an appropriate conclusion is:

> The sample does not provide robust evidence of a positive mean ex-post proxy
> under this specification. That result does not establish equality of the
> conditional \(P\)- and \(Q\)-expectations; sampling uncertainty, realized
> forecast error, regime composition, and measurement basis remain distinct
> from the theoretical premium.

For calibration or forecast comparisons, use:

> The result concerns calibration or relative predictive performance for the
> pre-specified realized-variance target. It is not a standalone test of
> arbitrage, rational expectations, or the Efficient Markets Hypothesis.

## 7. Link to the locked protocol

This memo supplies economic interpretation only. It leaves unchanged every
locked scientific choice:

- exact forward 30 calendar days remains the primary horizon;
- the next 21 S&P 500 trading days remain mandatory robustness;
- `VRP_X = IVAR - RVAR` remains the primary empirical proxy;
- `VOLGAP` remains secondary;
- no return dated \(t\) enters the forward target at \(t\);
- overlap-aware HAC/Newey--West and deterministic non-overlap remain required;
- the OOS split, common mask, formal NBER regimes, forecast-origin end, and
  target-support end are unchanged;
- no theoretical narrative licenses a result-driven specification change.

## References

- Bakshi, G., and N. Kapadia. 2003. “Delta-Hedged Gains and the Negative Market
  Volatility Risk Premium.” *Review of Financial Studies* 16 (2): 527–566.
  <https://doi.org/10.1093/rfs/16.2.527>.
- Black, F., and M. Scholes. 1973. “The Pricing of Options and Corporate
  Liabilities.” *Journal of Political Economy* 81 (3): 637–654.
  <https://doi.org/10.1086/260062>.
- Bollerslev, T., G. Tauchen, and H. Zhou. 2009. “Expected Stock Returns and
  Variance Risk Premia.” *Review of Financial Studies* 22 (11): 4463–4492.
  <https://doi.org/10.1093/rfs/hhp008>.
- Carr, P., and L. Wu. 2009. “Variance Risk Premiums.” *Review of Financial
  Studies* 22 (3): 1311–1341. <https://doi.org/10.1093/rfs/hhn038>.
- Cboe Global Indices. “VIX White Paper / Methodology.”
  <https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf>.
- Gârleanu, N., L. H. Pedersen, and A. M. Poteshman. 2009. “Demand-Based Option
  Pricing.” *Review of Financial Studies* 22 (10): 4259–4299.
  <https://doi.org/10.1093/rfs/hhn075>.
