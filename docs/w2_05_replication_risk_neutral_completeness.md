# Replication, risk-neutral pricing, and market completeness

**Tracker task:** W2-05

**Workstream:** Economic theory

**Role:** Econometrics

**Dependency:** W2-01

**Status:** Paper-ready subsection; no change to the locked empirical protocol

## Economic meaning

No-arbitrage pricing is a statement about the relative prices of traded
payoffs. Suppose a self-financing strategy in traded assets produces exactly
the same date-\(T\), state-by-state payoff as a derivative. The law of one
price then requires the derivative and the replicating strategy to have the
same date-\(t\) value. If their values differed, an investor could buy the
cheaper payoff, sell the more expensive identical payoff, and lock in the
price difference without retaining terminal risk. The replication cost, not
an estimate of the payoff's physical mean, is therefore the derivative's
no-arbitrage price.

This argument explains the Black--Scholes result in W2-01. In that model, the
stock and money-market account dynamically replicate a European claim. Delta
hedging removes the single Brownian shock from the combined position, and a
locally riskless self-financing position must earn the risk-free rate. The
stock's physical drift \(\mu\) consequently drops out of the pricing PDE.
That cancellation is a property of the hedge; it is not evidence that the
stock or the unhedged option has a physical expected return equal to the
risk-free rate.

## Risk-neutral valuation is not a real-world forecast

The distinction can be written with a stochastic discount factor. Let
\(m_{t,T}>0\) price a payoff \(X_T\), and let \(P(t,T)\) be the price of a
default-free zero-coupon bond paying one at \(T\). Then

\[
\pi_t(X_T)
=E_t^P[m_{t,T}X_T]
=P(t,T)E_t^{Q^T}[X_T],
\]

where the \(T\)-forward measure \(Q^T\) is defined by

\[
\frac{dQ^T}{dP}\bigg|_{\mathcal F_T}
=M_{t,T}
\equiv
\frac{m_{t,T}}{E_t^P[m_{t,T}]},
\qquad
E_t^P[M_{t,T}]=1.
\]

Under \(Q^T\), traded asset prices normalized by the \(T\)-bond price are
martingales. This normalization does not in general make prices discounted by
the money-market account martingales when interest rates are stochastic. If
\(B_t\) denotes the money-market account, its associated risk-neutral measure
\(Q^B\) instead gives

\[
\pi_t(X_T)=B_tE_t^{Q^B}\!\left[\frac{X_T}{B_T}\right],
\]

and money-market-discounted traded prices are martingales under \(Q^B\). The
two measures coincide for the fixed horizon when interest rates are
deterministic, as in the constant-rate Black--Scholes model used above; the
constant-rate formulas below denote this common measure by \(Q\).

The terms *risk-neutral* and *forward measure* describe changes of probability
weights, not investors' preferences or beliefs. Under the physical measure
\(P\), states retain their real-world probabilities; under \(Q^T\), states are
reweighted by their marginal value for pricing. Hence

\[
E_t^{Q^T}[X_T]-E_t^P[X_T]
=\operatorname{Cov}_t^P(M_{t,T},X_T).
\]

A payoff concentrated in bad states, where the discount factor is high, can
therefore have a risk-neutral expectation above its physical expectation.
Its high price is compatible with a low or negative physical expected excess
return because investors value its insurance payoff. No arbitrage determines
the price of a replicated exposure; equilibrium preferences and the joint
distribution of payoffs and marginal utility determine why its price can
differ from its physical mean payoff.

The separation is also visible directly in the Black--Scholes model. Combining
the physical stock dynamics with the pricing PDE gives the option dynamics

\[
dV_t
=\left[rV_t+(\mu-r)S_tV_S(t,S_t)\right]dt
+\sigma S_tV_S(t,S_t)\,dW_t^P.
\]

Thus the unhedged option's physical expected dollar return generally differs
from \(rV_t\,dt\). It inherits the physical risk premium of its stock
exposure, scaled by its delta. Only the correctly financed delta-hedged
combination is locally riskless and restricted to the risk-free return. A
risk-neutral valuation formula and a non-risk-neutral physical expected
return are therefore simultaneous implications of the same model.

## What market completeness adds

A market is complete, relative to a specified probability model and
information set, if every admissible contingent claim can be replicated by
trading the available securities. Under standard regularity conditions:

- no arbitrage implies the existence of an equivalent martingale measure;
- conditional on no arbitrage, the market is complete if and only if its
  equivalent martingale measure is unique; and
- uniqueness makes the no-arbitrage price unique for every admissible claim.

The Black--Scholes market is complete because one risky stock with nonzero
volatility spans the model's one Brownian source of uncertainty, while the
money-market account carries value through time. This is a model-relative
spanning statement. It does not mean that actual securities markets span
every economically relevant risk.

Completeness is stronger than is necessary to price a particular derivative.
Even in an incomplete market, a claim that happens to be replicable has the
unique price of its replicating strategy. For an unspanned claim, by contrast,
no arbitrage alone generally permits multiple equivalent martingale measures
and therefore does not select one price. It may still impose bounds and
cross-security restrictions, but a unique valuation then requires additional
structure, such as preferences, an equilibrium model, a hedging criterion, or
a convention for selecting a pricing measure.

Completeness also does **not** imply that \(Q=P\), that all expected returns
equal the risk-free rate under \(P\), that markets are informationally
efficient, or that a model is empirically correct. It supplies uniqueness of
arbitrage-free prices within the assumed market; it does not eliminate risk
premia.

## Limits of exact replication

The clean results rely on the trading opportunities and state space assumed
by the model. Black--Scholes replication requires continuous paths and
trading, known diffusion volatility, frictionless rebalancing, unrestricted
borrowing and short selling at the stated rate, and no unmodelled source of
risk. Actual index-option markets contain stochastic volatility, jumps,
discrete trading, bid--ask spreads, transaction costs, funding and margin
constraints, position limits, finite liquidity, and parameter uncertainty.
Dividends, rates, exercise rules, settlement, and quote timing must also match
the contract being valued. These features can make a theoretically complete
diffusion model an incomplete or costly-to-hedge description of the traded
market.

Variance replication has related qualifications. In idealized theory, a
continuum of options across strikes can statically replicate a log payoff,
which, together with dynamic trading in the underlying, produces a
variance-like payoff under the required path assumptions. In practice, listed
strikes are discrete and bounded, deep-tail quotes may be sparse, and jumps
and monitoring conventions affect the mapping from the log contract to
realized variance. Option filters, interpolation, rates, forward-price
construction, stale or asynchronous quotes, and bid--ask spreads create
further approximation. “Model-free” option-strip valuation is therefore free
of a particular parametric option-pricing model, not free of no-arbitrage,
integrability, contract, data, or implementation assumptions.

For this project, VIX is the Cboe index derived from the model-free SPX option
strip and quoted as 100 times annualized 30-calendar-day expected volatility.
The variance-space quantity is

\[
IVAR_t=(VIX_t/100)^2.
\]

It is not the Black--Scholes implied volatility of one option. Nor should
\(IVAR_t\) be described without qualification as an exact frictionless
replication cost for the project's close-to-close realized-variance target:
the Cboe index construction, finite option strip, and empirical target are
not literally the same contract.

## Implication for the variance-risk-premium evidence

Let \(V_{t,T}^{*}\) denote a future variance payoff conceptually matched to
the option-strip price. The observed gap can be organized as

\[
\begin{aligned}
IVAR_t-RVAR^{CC}_{t,30c}
={}&
\underbrace{E_t^Q[V_{t,T}^{*}]-E_t^P[V_{t,T}^{*}]}
_{\text{theoretical variance risk premium}}\\
&+
\underbrace{E_t^P[V_{t,T}^{*}]-V_{t,T}^{*}}
_{\text{physical forecast error}}\\
&+
\underbrace{V_{t,T}^{*}-RVAR^{CC}_{t,30c}
+IVAR_t-E_t^Q[V_{t,T}^{*}]}
_{\text{contract, measurement, and replication basis}}.
\end{aligned}
\]

The first term is a difference between conditional expectations under two
measures. The second arises because subsequently realized variance is one
outcome, not the physical conditional expectation. The final terms allow for
the fact that VIX-squared and close-to-close realized variance are not an
identical frictionlessly replicated payoff.

Accordingly, a positive average
\(VRP_t^X=IVAR_t-RVAR^{CC}_{t,30c}\) is consistent with compensation for
variance and tail risk, but it is not created by no arbitrage alone and is not
a direct observation of \(E_t^Q[V]-E_t^P[V]\). Likewise, rejection of
physical-forecast calibration does not reject no-arbitrage pricing: a
risk-neutral price need not be an unbiased forecast under \(P\). Forecast
accuracy, physical expected returns, and no-arbitrage valuation are distinct
economic questions.

This interpretation leaves unchanged the locked primary proxy, exact
30-calendar-day horizon, mandatory robustness over the next 21 S&P 500
trading days, timing rule, overlap-aware inference, out-of-sample design,
common mask, sample endpoints, and specification rule.

## References

- Black, F., and M. Scholes. 1973. “The Pricing of Options and Corporate
  Liabilities.” *Journal of Political Economy* 81 (3): 637--654.
  <https://doi.org/10.1086/260062>.
- Carr, P., and L. Wu. 2009. “Variance Risk Premiums.” *Review of Financial
  Studies* 22 (3): 1311--1341.
  <https://doi.org/10.1093/rfs/hhn038>.
- Cboe Global Indices. “VIX White Paper / Methodology.”
  <https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf>.
- Harrison, J. M., and S. R. Pliska. 1981. “Martingales and Stochastic
  Integrals in the Theory of Continuous Trading.” *Stochastic Processes and
  Their Applications* 11 (3): 215--260.
  <https://doi.org/10.1016/0304-4149(81)90026-0>.
- Merton, R. C. 1973. “Theory of Rational Option Pricing.” *Bell Journal of
  Economics and Management Science* 4 (1): 141--183.
  <https://doi.org/10.2307/3003143>.
- Project dependency:
  [`w2_01_black_scholes_pde_derivation.md`](w2_01_black_scholes_pde_derivation.md).
- Authoritative project protocol:
  [`../paper/method_protocol.md`](../paper/method_protocol.md), Sections 3, 4,
  6, 16, and 19.
