# Theoretical framework

This section develops the continuous-time foundations used for the
Black--Scholes option-pricing exercise and fixes the distinction between
single-option implied volatility and the option-strip measure used in the
empirical analysis. The Black--Scholes model is an analytical benchmark, not
a maintained empirical model of S&P 500 returns or VIX.

## Probability and notation

Let \((\Omega,\mathcal F,\{\mathcal F_t\}_{t\geq 0},P)\) be a filtered
probability space satisfying the usual conditions. The measure \(P\) denotes
the physical, or real-world, probability measure. A standard Brownian motion
\(W^P=\{W_t^P\}_{t\geq0}\) is adapted to \(\{\mathcal F_t\}\), begins at zero,
has continuous paths, and, for every \(0\leq s<t\), its future increment is
independent of the current information \(\mathcal F_s\) and is Gaussian:

\[
W_t^P-W_s^P\sim N(0,t-s),\qquad 0\leq s<t.
\]

For an option valued at date \(t\) and expiring at \(T\), write
\(\tau=T-t>0\) for time to maturity in years, \(S_t>0\) for the underlying
price, \(K>0\) for the strike, \(r\) for the continuously compounded
risk-free rate, \(q\) for a continuous dividend yield, and \(\sigma>0\) for
annualized return volatility. The no-dividend Black--Scholes core sets
\(q=0\); retaining \(q\) below displays the standard Merton extension used to
match carrying costs in the small option-validation exercise. Rates, yields,
and volatility are decimal annual rates.

We use \(N(\cdot)\) and \(n(\cdot)\) for the standard normal cumulative
distribution function and density. The symbols \(P\) and \(Q\) without
arguments denote probability measures; \(P^{BS}(t,S)\) denotes a European put
price only when the superscript makes that meaning unambiguous.

## Stochastic processes and geometric Brownian motion

An Itô diffusion has local dynamics

\[
dX_t=a(t,X_t)\,dt+b(t,X_t)\,dW_t^P,
\]

where \(a\) is the instantaneous drift and \(b^2\) is the instantaneous
variance rate. Conditional on \(\mathcal F_t\), its short-interval behavior is
approximately

\[
X_{t+\Delta t}-X_t
\approx
a(t,X_t)\Delta t+b(t,X_t)\sqrt{\Delta t}\,Z,
\qquad Z\sim N(0,1).
\]

This local approximation is not automatically an exact discrete-time
transition equation. Exact transitions require additional structure.

In the Black--Scholes model, the underlying follows geometric Brownian motion
under \(P\):

\[
dS_t=(\mu-q)S_t\,dt+\sigma S_t\,dW_t^P,
\qquad S_0>0.
\]

Here \(\mu\) is the expected total return before the continuous dividend
yield is paid. Applying Itô's formula to \(\log S_t\) gives

\[
d\log S_t
=
\left(\mu-q-\frac12\sigma^2\right)dt+\sigma\,dW_t^P.
\]

Integration over \([t,T]\) yields

\[
S_T
=
S_t\exp\left[
\left(\mu-q-\frac12\sigma^2\right)\tau
+\sigma\left(W_T^P-W_t^P\right)
\right],
\]

so the model preserves positive prices and implies conditionally lognormal
returns. The \(-\sigma^2/2\) term distinguishes the arithmetic expected return
from expected log growth.

Brownian paths are continuous but almost surely nowhere differentiable. Their
quadratic variation over \([0,t]\) is \(t\), summarized by the Itô rules

\[
(dW_t)^2=dt,\qquad dW_t\,dt=0,\qquad (dt)^2=0.
\]

These are quadratic-variation rules, not ordinary algebraic identities. For
a continuous diffusion

\[
\frac{dS_t}{S_t}=b_t\,dt+\sigma_t\,dW_t,
\]

the quadratic variation of log price is

\[
[\log S]_{t,T}=\int_t^T\sigma_u^2\,du.
\]

For \(T>t\), define the annualized future realized variance

\[
\mathcal V_{t,T}
=
\frac{1}{T-t}[\log S]_{t,T}
=
\frac{1}{T-t}\int_t^T\sigma_u^2\,du,
\]

where \(T-t\) is measured in years. This notation is distinct from the
derivative value \(V(t,S)\).

This identity supplies the continuous-time link between variance and squared
high-frequency returns. In Black--Scholes, \(\sigma_u=\sigma\), so integrated
variance is \(\sigma^2\tau\). In the empirical analysis, by contrast,
volatility is allowed to vary and forward realized variance is measured from
subsequent S&P 500 returns.

## Itô's formula

Let \(f(t,x)\) have one continuous time derivative and two continuous state
derivatives. If \(X_t\) follows the Itô diffusion above, then

\[
\boxed{
df(t,X_t)
=
\left(
f_t+a f_x+\frac12b^2f_{xx}
\right)dt
+b f_x\,dW_t^P.}
\]

The term \(b^2f_{xx}/2\) is the Itô correction. It survives because Brownian
increments are of stochastic order \(\sqrt{dt}\), making their squares of
order \(dt\). An ordinary chain rule would omit this term and therefore give
incorrect drift and moment dynamics.

For a sufficiently smooth derivative value \(V(t,S_t)\), the stock dynamics
imply

\[
\begin{aligned}
dV(t,S_t)
={}&
\left[
V_t+(\mu-q)S_tV_S
+\frac12\sigma^2S_t^2V_{SS}
\right]dt\\
&+\sigma S_tV_S\,dW_t^P.
\end{aligned}
\]

The derivative's instantaneous exposure to the Brownian shock is therefore
\(\sigma S_tV_S\). This exposure is the term removed by a delta hedge.

## No-arbitrage replication and the Black--Scholes equation

Let the money-market account satisfy

\[
dB_t=rB_t\,dt.
\]

Consider a self-financing portfolio holding
\(\Delta_t=V_S(t,S_t)\) units of the underlying, with the remainder invested
in the money-market account. The stock position matches the derivative's
Brownian exposure. Because the underlying pays dividend yield \(q\), the
portfolio receives the associated dividend flow in addition to capital gains.
Equating the drift of the replicating portfolio with the derivative drift
eliminates both the Brownian shock and the physical expected-return parameter
\(\mu\). Absence of arbitrage then gives

\[
\boxed{
V_t+\frac12\sigma^2S^2V_{SS}
+(r-q)SV_S-rV=0,}
\qquad
V(T,S)=g(S),
\]

where \(g\) is the terminal payoff. Setting \(q=0\) recovers the
no-dividend Black--Scholes partial differential equation used for the core
derivation.

The disappearance of \(\mu\) is a replication result. It does not say that
the physical expected stock return equals the risk-free rate. Under the
risk-neutral measure \(Q\) associated with the money-market numeraire,

\[
dS_u=(r-q)S_u\,du+\sigma S_u\,dW_u^Q,
\]

and the unique no-arbitrage value of a replicable European payoff is

\[
\boxed{
V(t,S_t)=e^{-r\tau}E_t^Q[g(S_T)].}
\]

Risk-neutral probabilities are pricing weights, not estimates of real-world
event frequencies. Completeness makes the equivalent martingale measure and
the model price unique within the assumed one-factor diffusion market; it
does not imply that \(Q=P\), that actual markets are complete, or that the
model is empirically correct.

## European call and put prices

For a European call and put,

\[
g_C(S_T)=(S_T-K)^+,
\qquad
g_P(S_T)=(K-S_T)^+.
\]

Under \(Q\), terminal price is

\[
S_T
=
S_t\exp\left[
\left(r-q-\frac12\sigma^2\right)\tau
+\sigma\sqrt{\tau}\,Z
\right],
\qquad Z\sim N(0,1).
\]

Define

\[
d_1
=
\frac{\log(S_t/K)+(r-q+\tfrac12\sigma^2)\tau}
{\sigma\sqrt{\tau}},
\qquad
d_2=d_1-\sigma\sqrt{\tau}.
\]

Evaluating the discounted expectations gives the
Black--Scholes--Merton prices

\[
\boxed{
C^{BS}(t,S_t;\sigma)
=
S_te^{-q\tau}N(d_1)-Ke^{-r\tau}N(d_2)}
\]

and

\[
\boxed{
P^{BS}(t,S_t;\sigma)
=
Ke^{-r\tau}N(-d_2)-S_te^{-q\tau}N(-d_1).}
\]

They satisfy European put--call parity,

\[
C^{BS}-P^{BS}=S_te^{-q\tau}-Ke^{-r\tau},
\]

and the no-arbitrage bounds

\[
\left(S_te^{-q\tau}-Ke^{-r\tau}\right)^+
\leq C^{BS}\leq S_te^{-q\tau},
\]

\[
\left(Ke^{-r\tau}-S_te^{-q\tau}\right)^+
\leq P^{BS}\leq Ke^{-r\tau}.
\]

The call and put have the same sensitivity to volatility:

\[
\boxed{
\frac{\partial C^{BS}}{\partial\sigma}
=
\frac{\partial P^{BS}}{\partial\sigma}
=
S_te^{-q\tau}n(d_1)\sqrt{\tau}>0.}
\]

Strictly positive vega is central to implied-volatility inversion.

## Black--Scholes implied volatility

For an observed price \(O_{i,t}^{mkt}\) of option \(i\), its
Black--Scholes implied volatility is the volatility parameter that makes the
model reproduce that one price:

\[
\boxed{
\sigma_{i,t}^{BS}
=
\left\{\sigma>0:
O^{BS}(t,S_t,K_i,\tau_i,r,q;\sigma)
=O_{i,t}^{mkt}
\right\}.}
\]

It is an inversion of a pricing function, not a direct observation of the
physical conditional standard deviation. Because vega is positive whenever
\(S_t,K_i,\tau_i,\sigma>0\), the option price is strictly increasing in
\(\sigma\). Consequently, an admissible quote strictly inside the applicable
European bounds has exactly one finite positive implied volatility. A quote
at a lower bound corresponds to the zero-volatility limit, while the upper
bound is approached only as volatility diverges; neither boundary identifies
a finite strictly positive root.

The numerical implementation first verifies finite inputs and
\(S_t>0\), \(K_i>0\), and \(\tau_i>0\), then checks the option-price bounds.
It solves

\[
h(\sigma)
=
O^{BS}(t,S_t,K_i,\tau_i,r,q;\sigma)-O_{i,t}^{mkt}=0
\]

with Brent's bracketed root-finding method. The positive search interval
starts at \(10^{-8}\), begins with an upper endpoint of \(1.0\), and expands
by doubling when needed, subject to a computational cap of \(50.0\). The cap
is a guardrail, not an assertion that no mathematical root can exist above
it. Invalid prices, an unbracketed root, and solver non-convergence produce
explicit failures rather than a fabricated volatility estimate. Synthetic
price recovery, put--call parity, limiting cases, volatility monotonicity,
independent-library prices, and a small fixed SPX quote sample provide the
validation hierarchy for this calculation.

Observed index-option prices do not generally produce one common
\(\sigma_{i,t}^{BS}\) across strikes and maturities. The resulting volatility
smile or skew documents the failure of the constant-volatility lognormal model
to fit the entire option surface with one parameter. It does not invalidate
implied volatility as a quote transformation, but it prevents interpreting
one option's implied volatility as a model-free market-wide variance measure.
Bid--ask spreads, discrete dividends, rates, quote timing, exercise and
settlement conventions, and contract details are therefore material in any
real-option comparison.

## Separation from VIX and the empirical variance proxy

The empirical analysis does not use a single-option
\(\sigma_{i,t}^{BS}\) as its implied-volatility measure. Cboe VIX aggregates a
strip of SPX option prices across strikes and two maturities using model-free
variance-replication logic, interpolated to a constant 30-calendar-day
maturity. In the project's units,

\[
IVOL_t=\frac{VIX_t}{100},
\qquad
IVAR_t=IVOL_t^2.
\]

Thus VIX is quoted as 100 times the square root of an annualized,
option-implied 30-day variance quantity. It is neither the implied volatility
of one Black--Scholes option nor, in general,
\(100E_t^Q[\sqrt{\text{future variance}}]\).

The theoretical variance risk premium is a conditional difference between
pricing and physical expectations:

\[
VRP_t^{theory}
=
E_t^Q[\mathcal V_{t,T}]-E_t^P[\mathcal V_{t,T}].
\]

Neither conditional expectation is observed. The primary empirical object is
instead the ex-post variance-risk-premium proxy

\[
VRP_t^X
=
IVAR_t-RVAR^{CC}_{t,30c},
\qquad
RVAR^{CC}_{t,30c}
=
\frac{365}{30}
\sum_{d:t<d\leq t+30c}r_d^2.
\]

Here \(r_d=\log(C_d/C_{d^-})\) is the close-to-close log return ending on
exchange date \(d\), and \(d^-\) is the preceding S&P 500 exchange date.
The sign convention is always implied minus realized. The realized outcome is
one draw rather than \(E_t^P[\mathcal V_{t,T}]\), and VIX-squared is not
literally the same contract as the close-to-close realized-variance target.
The observed proxy therefore combines any underlying variance risk premium
with physical forecast error and contract, measurement, and replication
basis. The secondary volatility-space quantity

\[
RVOL^{CC}_{t,30c}
=
\sqrt{RVAR^{CC}_{t,30c}},
\qquad
VOLGAP_t=IVOL_t-RVOL^{CC}_{t,30c}
\]

is retained only for intuitive presentation. This theoretical framework
leaves the exact forward 30-calendar-day primary horizon, next-21-trading-day
robustness horizon, timing rule, annualization, overlap-aware inference, and
out-of-sample design unchanged.

## Assumptions and interpretation limits

| Assumption | Formal role | Interpretation and limitation |
|---|---|---|
| Filtered diffusion setting | Brownian shocks are adapted, every future Brownian increment is independent of the current filtration, and trading rules use current information. | Excludes anticipative strategies; does not make a sampled diffusion an exact discrete-time likelihood without a valid transition law. |
| Geometric Brownian motion | \(dS_t=(\mu-q)S_tdt+\sigma S_tdW_t^P\) with \(S_t>0\). | Implies continuous paths and lognormal returns. Actual index returns exhibit jumps, tails, and time-varying volatility. |
| Constant known parameters | \(r\), \(q\), and \(\sigma\) are constant over the option's life in the analytical model. | Useful for a benchmark price, but rates, dividends, and conditional volatility vary and must be measured in applications. |
| Traded risk-free asset | \(dB_t=rB_tdt\); borrowing and lending occur at the same rate. | Abstracts from funding spreads, collateral, margin, and rate uncertainty. |
| Frictionless continuous trading | Positions can be rebalanced continuously without transaction costs, taxes, bid--ask spreads, liquidity limits, or indivisibilities. | Makes dynamic replication exact in the model. Real hedging is discrete and costly. |
| Continuous dividend treatment | The underlying pays a known continuous yield \(q\); the no-dividend core has \(q=0\). | SPX dividends are discrete and uncertain. A fitted continuous carry is an approximation, not necessarily a literal dividend yield. |
| European payoff | The claim pays \(g(S_T)\) only at fixed maturity \(T\). | Exercise, settlement, and contract conventions must match the instrument; the formulas do not price American exercise. |
| No arbitrage and self-financing replication | Rebalancing requires no external cash and identical attainable payoffs have identical prices. | Determines a relative model price; it does not imply unbiased physical forecasts or investor risk neutrality. |
| One-factor model completeness | One nondegenerate stock diffusion and the money-market account span the model's Brownian risk. | Gives a unique model price, but actual volatility, jump, liquidity, and tail risks need not be spanned. |
| Valuation regularity | \(V\in C^{1,2}\) for \(t<T\), with suitable growth and integrability; the terminal payoff may be kinked. | Justifies Itô and Feynman--Kac arguments in the interior. The payoff kink is handled as a terminal condition. |
| Admissible synchronized quote for inversion | Inputs are positive where required, use consistent units and timing, and the option quote lies inside its European bounds. | Necessary for a meaningful finite positive implied volatility; stale, crossed, or mismatched quotes can fail even when the solver is correct. |
| Track separation | Single-option \(\sigma_{i,t}^{BS}\) belongs to Track A; \(IVAR_t=(VIX_t/100)^2\) belongs to Track B. | Prevents a parametric one-option inversion from being substituted for the model-free SPX option-strip index. |

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
