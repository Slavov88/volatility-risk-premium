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

Writing \(b=\sigma\sqrt{\tau}\), the exercise threshold is \(Z>-d_2\).
Completing the square in the Gaussian density gives
\[
E[e^{bZ}\mathbf1_{Z>a}]=e^{b^2/2}N(b-a).
\]
Therefore \(Q(S_T>K)=N(d_2)\) and
\(E_t^Q[S_T\mathbf1_{S_T>K}]=S_te^{(r-q)\tau}N(d_1)\).
Subtraction of the discounted strike leg gives the call formula; parity gives
the put. The Black--Scholes--Merton prices are

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

## Variance swaps, the log contract, and the option strip

A variance swap pays \(N_{var}(\mathcal V_{t,T}-K_{var})\) at maturity. With deterministic discounting, zero inception value implies
\[
K_{var}=E_t^Q[\mathcal V_{t,T}].
\]
With stochastic discounting the corresponding ratio is
\(E_t^Q[D_{t,T}\mathcal V]/E_t^Q[D_{t,T}]\), or a forward-measure expectation, rather than an unrestricted money-market-measure expectation. The distinction matters when identifying an index formula with a particular OTC payoff.

For a continuous positive semimartingale with deterministic carry, Itô's formula gives the pathwise identity
\[
\int_t^T\sigma_u^2du
=2\int_t^T\frac{dS_u}{S_u}-2\log(S_T/S_t).
\]
The first term is generated by a dynamic position of \(2/S_u\) in the underlying, with dividends and financing included in the gains account. Under \(Q\), the expected return integral is \((r-q)\tau\), assuming the stochastic integral is a true martingale. Hence, writing \(F=S_te^{(r-q)\tau}\),
\[
K_{var}=-\frac2\tau E_t^Q[\log(S_T/F)].
\]
This equality allows stochastic volatility; it requires neither lognormal terminal prices nor a common Black–Scholes volatility across strikes. It does require the continuous-path, integrability and trading assumptions stated here (Demeterfi et al., 1999; Carr and Wu, 2009).

The static option component follows directly from the second-derivative payoff identity. For any positive anchor \(a\) and suitable twice-differentiable payoff \(f\),
\[
f(x)=f(a)+f'(a)(x-a)
+\int_0^a f''(K)(K-x)^+dK
+\int_a^\infty f''(K)(x-K)^+dK.
\]
Choose \(f(x)=-\log(x/F)\), \(a=F\), and note \(f''(K)=1/K^2\). Then
\[
-\log(S_T/F)=-\frac{S_T-F}{F}
+\int_0^F\frac{(K-S_T)^+}{K^2}dK
+\int_F^\infty\frac{(S_T-K)^+}{K^2}dK.
\]
Taking risk-neutral expectations cancels the linear forward term. If \(p_t(K,T)\) and \(c_t(K,T)\) denote discounted European put and call prices,
\[
\boxed{K_{var}=\frac{2e^{r\tau}}{\tau}
\left[\int_0^F\frac{p_t(K,T)}{K^2}dK
+\int_F^\infty\frac{c_t(K,T)}{K^2}dK\right].}
\]
The factor \(e^{r\tau}\) reverses discounting and \(1/\tau\) annualizes integrated variance. Strikes, prices and the forward share the same index-point unit, leaving annualized decimal variance. Put–call parity determines the forward independently of an assumed dividend yield. Exact replication presumes a continuum of strikes extending to zero and infinity; actual data offer a finite, irregular, noisy grid. “Model-free” therefore describes the absence of a parametric volatility model in this representation, not the absence of assumptions or measurement error.

### Jumps and monitoring limits

For a jump \(x_u=\Delta S_u/S_{u-}>-1\), the same log-hedging argument generates the jump term \(2[x_u-\log(1+x_u)]\). The quadratic variation of log price instead contains \([\log(1+x_u)]^2\). Thus the replicated log payoff differs from log-price quadratic variation by
\[
\sum_{t<u\le T}\left\{2[x_u-\log(1+x_u)]-[\log(1+x_u)]^2\right\}.
\]
Its local Taylor expansion starts at cubic order in the jump size. It cannot be set to zero for an arbitrary crash. This is why the continuous-path variance-strip identity is exact while its mapping to a general jump-variance swap is an approximation. Carr and Wu explicitly study jump and discretization errors; their numerical findings under chosen models are not a universal bound.

At a finite daily frequency, a sum of squared log returns also includes sampling effects and drift contributions. It misses variation inside a close-to-close interval that cancels before the next close; refining the grid converges to quadratic variation under the usual semimartingale conditions, but daily sampling is not that limit. The project's calendar rule includes return-ending dates strictly after the origin and at most 30 calendar days ahead. If the calendar endpoint is a non-trading day, its unobserved partial interval is not synthesized. Close timestamps, overnight returns, discrete monitoring and the endpoint convention remain basis relative to the ideal continuous contract. Parkinson and Garman–Klass robustness targets add intraday-range information under diffusion assumptions but do not restore overnight jumps automatically.

## VIX construction and historical comparability

For each eligible maturity \(\tau_j\), Cboe implements a discrete approximation of the strip:
\[
v_j=\frac{2e^{R_j\tau_j}}{\tau_j}
\sum_i\frac{\Delta K_i}{K_i^2}Q_j(K_i)
-\frac1{\tau_j}\left(\frac{F_j}{K_{0j}}-1\right)^2.
\]
Here \(Q_j(K_i)\) is an option bid–ask midpoint, not a probability measure; puts enter below \(K_{0j}\), calls above, and their average at \(K_{0j}\). The forward is inferred using put–call parity and \(K_{0j}\) is the first strike at or below it. Interior strike increments use half the distance between neighboring strikes, with one-sided endpoint increments. Quote eligibility, zero-bid truncation, rate construction, and index filtering are additional rules. The forward correction is part of the finite-grid index formula; it does not make an arbitrary finite strip identical to every variance-swap contract.

For a target year fraction \(\tau_*=30/365\) between two maturities,
\[
w_1=\frac{\tau_2-\tau_*}{\tau_2-\tau_1},\quad
w_2=\frac{\tau_*-\tau_1}{\tau_2-\tau_1},\qquad
IVAR_t=\frac{w_1\tau_1v_1+w_2\tau_2v_2}{\tau_*},
\qquad VIX_t=100\sqrt{IVAR_t}.
\]
Cboe implements the corresponding clock using minutes. It interpolates total variance before annualizing and taking the square root; it does not interpolate two quoted volatilities. This motivates the exact 30-calendar-day empirical horizon. Jensen's inequality also implies \(\sqrt{E^Q[\mathcal V]}\ge E^Q[\sqrt{\mathcal V}]\); a VIX level is not a volatility-swap strike.

Historical comparability requires three distinctions. Cboe introduced the original OEX-based, near-the-money VIX in 1993. The redesigned broad-strike SPX index launched on September 22, 2003, with a retrospective history beginning in January 1990; the original calculation is associated with VXO. The current VIX history must not be described as a splice of pre-2003 OEX observations with later SPX observations. On October 6, 2014, eligible SPX Weeklys entered spot VIX, tightening the maturity bracket to more than 23 and less than 37 days. The monthly-only legacy measure continued as VIXMO (Cboe IC14-075). That 2014 computational transition is not retrospectively removed from the observed spot series. The locked full sample, post-2003 sample beginning 2004-01-01, and post-2014-10-06 sample address different comparability concerns.

The publicly accessible methodology consulted for this manuscript is version 6.0, revised February 26, 2026. It documents present index rules and is not evidence that each operational detail applied unchanged throughout 1990–2025. The contemporaneous 2014 circular anchors the weekly-option transition. Current RTH spot-index dissemination extends to 16:15 ET, later than the usual 16:00 cash-index close; the historical daily CLOSE field does not establish exact synchronization throughout the sample. No unsupported 16:00 VIX reconstruction is substituted. Spot VIX closes also differ from the special opening quotation used for derivative settlement (Cboe methodology, sections 3–5).

## Economic interpretation and related literature

Let \(M_{t,T}>0\) be a stochastic discount factor and assume deterministic discounting for the following comparison. Pricing implies
\[
E_t^Q[\mathcal V]=\frac{E_t^P[M_{t,T}\mathcal V]}{E_t^P[M_{t,T}]},\qquad
VRP_t^{theory}=\frac{\operatorname{Cov}_t^P(M_{t,T},\mathcal V)}{E_t^P[M_{t,T}]}.
\]
Variance that is high in states where marginal value of wealth is high commands a positive price relative to its physical expected payoff. Under this paper's \(Q-P\) convention, the long variance buyer then has expected payoff \(E_t^P[\mathcal V]-K_{var}=-VRP_t^{theory}\); the short side receives compensation for bearing adverse-state exposure. This covariance identity explains a possible sign, rather than imposing one. In a constant-volatility Black–Scholes economy, variance is deterministic and this variance premium is zero even though equity itself can carry a risk premium.

Carr and Wu (2009) provide the closest replication-based empirical antecedent. Their realized-minus-synthetic-swap-rate convention is the **opposite** of this paper's implied-minus-realized convention. Their negative index premia therefore correspond to positive premia here after sign reversal; their raw findings must not be cited as evidence of an economic disagreement. Their option-strip evidence also covers other indices and individual stocks, whereas the present core concerns the S&P 500 alone.

Bakshi and Kapadia (2003) infer volatility-risk compensation from delta-hedged option gains. This supports an insurance interpretation but uses a different payoff and does not equate an option's vega-weighted return with a VIX-minus-daily-variance proxy. Bollerslev, Tauchen and Zhou (2009) connect model-free variance measures to equilibrium uncertainty and equity-return predictability using high-frequency realized variation. Their results motivate the distinction between physical and pricing expectations; they neither validate this project's daily target by substitution nor imply its forecast ranking. Equity-return predictability is outside the confirmatory core. Gârleanu, Pedersen and Poteshman (2009) show how demand and imperfect hedging affect option prices, offering a complementary channel to frictionless representative-investor compensation. These channels can coexist; a mean-gap regression does not identify their separate contributions.

To make the observational limit explicit, let \(\mathcal V^*\) be a matched latent variance payoff. The exact additive accounting identity is
\[
\begin{aligned}
IVAR_t-RVAR_t={}&[E_t^Q\mathcal V^*-E_t^P\mathcal V^*]
+[E_t^P\mathcal V^*-\mathcal V^*]\\
&+[\mathcal V^*-RVAR_t]+[IVAR_t-E_t^Q\mathcal V^*].
\end{aligned}
\]
The four terms are the theoretical premium, physical forecast error, realized-measurement basis, and index-replication basis. Under an integrable correctly specified physical conditional expectation the second term has conditional mean zero; a finite sample with rare crises need not realize that mean. The remaining basis terms need not average to zero. Consequently neither a positive ex-post mean nor rejection of \((\alpha,\beta)=(0,1)\) in a calibration regression proves irrationality. Unexpected crises can yield negative realized gaps even when insurance commands a positive expected premium.

Variance and volatility gaps have the same observation-level sign, since
\[
IVAR_t-RVAR_t=(IVOL_t-RVOL_t)(IVOL_t+RVOL_t).
\]
Their sample averages can weight observations differently and need not share a ranking or even a sign. This is why variance is the primary inferential unit and volatility percentage points are secondary presentation.

## Track A numerical evidence

The deterministic validation report reproduced in `option_replay.md` compares six calls/puts with QuantLib 1.43. Maximum absolute price and IV errors are respectively \(1.862\times10^{-14}\) index-price units and \(3.065\times10^{-13}\) annualized decimal volatility. An additional independent Gaussian-payoff quadrature gives maximum price error \(5.151\times10^{-14}\) across those six cases. Log-strike integration of the continuous strip at volatilities 0.12, 0.30 and 0.60 and maturities 30/365 and one year recovers \(\sigma^2\) with maximum annualized-variance error \(1.110\times10^{-16}\) across six cases. These are numerical checks within a diffusion model, not empirical evidence that jumps or replication basis are immaterial.

The fixed market exercise uses six European AM-settled SPX contracts observed on 2022-09-15, expiring 2022-10-21, at strikes 3850, 3900 and 3950. The source-convention maturity is 35/365, rate 0.027946575342, forward 3916.093068610 and spot 3901.35. Equivalent continuous carry is −0.011388364485. It reproduces the source's parity-based Black-76 pricing through the algebraically equivalent Black–Scholes–Merton form; it is not an independent estimate of a literal negative dividend yield. Maximum absolute midpoint-IV discrepancy is \(8.604\times10^{-7}\); repricing source IV differs from midpoints by at most \(4.137\times10^{-4}\) index points, with all six values inside bid–ask spreads. Published IV rounding, par-yield approximation, AM settlement and asynchronous quotes limit interpretation. No option timestamps exist in the 2022 sample. This small exercise verifies implementation consistency only; it neither tests an entire option surface nor supplies Track B's VIX series.

## References

- Black, F., and M. Scholes. 1973. “The Pricing of Options and Corporate
  Liabilities.” *Journal of Political Economy* 81 (3): 637--654.
  <https://doi.org/10.1086/260062>.
- Carr, P., and L. Wu. 2009. “Variance Risk Premiums.” *Review of Financial
  Studies* 22 (3): 1311--1341.
  <https://doi.org/10.1093/rfs/hhn038>.
- Harrison, J. M., and S. R. Pliska. 1981. “Martingales and Stochastic
  Integrals in the Theory of Continuous Trading.” *Stochastic Processes and
  Their Applications* 11 (3): 215--260.
  <https://doi.org/10.1016/0304-4149(81)90026-0>.
- Merton, R. C. 1973. “Theory of Rational Option Pricing.” *Bell Journal of
  Economics and Management Science* 4 (1): 141--183.
  <https://doi.org/10.2307/3003143>.
- Bakshi, G., and N. Kapadia. 2003. “Delta-Hedged Gains and the Negative Market Volatility Risk Premium.” *Review of Financial Studies* 16 (2): 527–566. <https://doi.org/10.1093/rfs/16.2.527>. [Author-hosted article](https://people.umass.edu/~nkapadia/docs/Bakshi_and_Kapadia_2003_RFS.pdf).
- Bollerslev, T., G. Tauchen, and H. Zhou. 2009. “Expected Stock Returns and Variance Risk Premia.” *Review of Financial Studies* 22 (11): 4463–4492. <https://doi.org/10.1093/rfs/hhp008>. [Author institutional record](https://scholars.duke.edu/publication/732839).
- Cboe. 2014. “Indicative (Spot) VIX Index Value to Include SPX Weeklys Beginning October 6, 2014.” Information Circular IC14-075, September 22. <https://res-certification.cboe.com/resources/regulation/circulars/general/IC-CBOE-2014-075.pdf>.
- Cboe Global Indices. 2026. *Cboe Volatility Index Methodology*, version 6.0, February 26. <https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf>.
- Cboe. “Historical Data for Cboe VIX Index and Other Volatility Indices.” <https://www.cboe.com/tradable_products/vix/vix_historical_data>.
- Demeterfi, K., E. Derman, M. Kamal, and J. Zou. 1999. “More Than You Ever Wanted to Know About Volatility Swaps.” Goldman Sachs Quantitative Strategies Research Notes, March. [Author-hosted research note and download](https://emanuelderman.com/more-than-you-ever-wanted-to-know-about-volatility-swaps-the-journal-of-der/).
- Gârleanu, N., L. H. Pedersen, and A. M. Poteshman. 2009. “Demand-Based Option Pricing.” *Review of Financial Studies* 22 (10): 4259–4299. <https://doi.org/10.1093/rfs/hhp005>.
- HistoricalData.net. “Historical US Options Data — End-of-Day Chains.” <https://historicaldata.net/options.html>. Provider documentation and fixed sample provenance, rather than a source of the theoretical derivations.
