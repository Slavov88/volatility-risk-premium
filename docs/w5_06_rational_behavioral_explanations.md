# W5-06 — Rational and behavioral explanations of the variance premium

**Workstream:** Literature synthesis

**Dependency:** W1-07

**Status:** balanced literature subsection; no change to the locked empirical protocol

**Coverage rule:** purposive synthesis of directly relevant theory and evidence,
not a systematic or exhaustive review

The literature results summarized below are not findings of this project and
do not predetermine its empirical results.

## Interpretation before classification

The empirical regularity to be explained is that option-implied variance often
exceeds subsequently realized variance. For this project, however, the observed
quantity is specifically

\[
VRP_t^X=IVAR_t-RVAR^{CC}_{t,30c},
\qquad IVAR_t=(VIX_t/100)^2,
\]

with the exact forward 30-calendar-day target defined in the locked protocol.
This ex-post proxy is not the theoretical conditional variance risk premium,

\[
E_t^Q[V_{t,T}]-E_t^P[V_{t,T}].
\]

The distinction matters for comparing explanations. Realized variance is one
noisy outcome rather than the physical conditional expectation, and the
observed gap also includes measurement and contract-basis differences. A
positive sample mean can therefore motivate economic explanations without
identifying any one of them.

## Risk compensation and rational equilibrium

The standard risk-premium account begins with state prices rather than forecast
bias. If variance rises in states in which wealth is scarce and marginal
utility is high, claims that pay in those states are valuable insurance.
Risk-averse investors may rationally pay more for variance or downside
protection than its physical expected payoff, while sellers require
compensation for volatility, jump, and crash exposure. Under this account,
\(E_t^Q[V]>E_t^P[V]\) need not indicate an expectation error.

Several strands of evidence support this interpretation, but each is
conditional. [Bakshi and Kapadia
(2003)](https://doi.org/10.1093/rfs/hhg002) find negative average delta-hedged
option gains, consistent with compensation for volatility risk. [Carr and Wu
(2009)](https://doi.org/10.1093/rfs/hhn038) document large index variance
premia using model-free variance-swap logic. Their sign convention is realized
variance minus the swap rate; their negative premium maps to a positive
implied-minus-realized premium here. Neither design directly recovers
\(E_t^P[V]\), and option returns additionally depend on jumps, hedging error,
trading costs, and rare realizations.

Tail-risk evidence sharpens the insurance mechanism. [Bollerslev and Todorov
(2011)](https://doi.org/10.1111/j.1540-6261.2011.01695.x) combine
high-frequency returns, short-dated out-of-the-money options, and extreme-value
approximations and attribute a large fraction of average equity and variance
risk premia to compensation for rare events. [Drechsler and Yaron
(2011)](https://doi.org/10.1093/rfs/hhq085) show that a calibrated long-run-risk
model with stochastic volatility and non-Gaussian shocks can jointly generate
a time-varying variance premium and other asset-pricing moments. These findings
make disaster and uncertainty compensation plausible; they do not uniquely
identify it. Rare-tail probabilities are intrinsically difficult to estimate,
and successful calibration is a joint test of preferences, state dynamics, and
measurement. [Broadie, Chernov, and Johannes
(2009)](https://doi.org/10.1093/rfs/hhp032) demonstrate the corresponding
warning: extreme sampling uncertainty can make apparently exceptional
out-of-the-money put returns statistically compatible with several models.

Risk-bearing capacity adds a frictional equilibrium channel. In [Gârleanu,
Pedersen, and Poteshman
(2009)](https://doi.org/10.1093/rfs/hhp005), end-user demand affects option
prices when dealers cannot perfectly hedge the residual exposure; demand for
one contract can also affect other contracts through the covariance of their
unhedgeable payoffs. [Chen, Joslin, and Ni
(2019)](https://doi.org/10.1093/rfs/hhy004) use deep out-of-the-money SPX
put trading to construct a measure of intermediary constraints and find that
tighter constraints are associated with more expensive options, weaker funding
liquidity, and broker-dealer deleveraging. This evidence supports limited
supply of crash insurance, but it does not reveal why end users demand
insurance. Their demand may reflect objective bad-state exposure, subjective
fear, or both.

## Behavioral beliefs and probability weighting

Behavioral accounts alter how investors form or weight beliefs about future
volatility and tail outcomes. Extrapolation can make a recent volatility shock
too influential at long horizons; sluggish updating can produce short-horizon
underreaction; sentiment can shift perceived downside risk; and probability
weighting can give small-probability tail events decision weights that differ
from their objective probabilities. These mechanisms can raise option-implied
variance even when conventional risk compensation alone is insufficient.

Early option evidence is suggestive but particularly sensitive to the pricing
model. [Stein (1989)](https://doi.org/10.1111/j.1540-6261.1989.tb02635.x)
finds that long-maturity OEX implied volatility responds more to short-maturity
implied volatility than predicted by his mean-reverting rational-expectations
benchmark. [Poteshman
(2001)](https://doi.org/10.1111/0022-1082.00348) reports short-horizon
underreaction and overreaction following strings of same-signed variance
changes in SPX options, patterns consistent with cognitive biases. Yet both
inferences rely on model-extracted volatility and a maintained law of
volatility dynamics. Using model-free implied volatility, [Jiang and Tian
(2010)](https://doi.org/10.1016/j.jbankfin.2010.02.022) find that the earlier
misreaction patterns disappear and attribute them to option-model
misspecification. Thus these studies demonstrate a live behavioral hypothesis,
not settled evidence of irrational updating.

More direct evidence on beliefs comes from [Lochstoer and Muir
(2022)](https://doi.org/10.1111/jofi.13120). They document slow-moving
volatility expectations, with initial underreaction to volatility shocks
followed by delayed overreaction; related dynamics appear in VIX, variance
premia, surveys, and firm-level options. Triangulation across market and survey
evidence strengthens the belief-based account, but survey respondents need not
be marginal option traders, and slow updating can also reflect rational
information rigidity or learning rather than a unique cognitive bias.

Other work connects prices to sentiment or non-expected-utility preferences.
[Han (2008)](https://doi.org/10.1093/rfs/hhm071) finds that bearish sentiment
is associated with a steeper S&P 500 option smile and more negative
risk-neutral skewness, with stronger relations when arbitrage is more impeded.
[Baele et al.
(2019)](https://doi.org/10.1093/rfs/hhy127) show that an equilibrium model with
cumulative-prospect-theory probability weighting can jointly fit low
out-of-the-money put and call returns and a high variance premium. These
results establish that behavioral mechanisms can organize important option
facts. They do not show that sentiment or probability weighting causes the
aggregate 30-day variance gap: sentiment proxies can covary with objective
risk, and structural moment matching does not uniquely select one preference
model.

Belief disagreement sits across the usual labels. [Buraschi, Trojani, and
Vedolin (2014)](https://doi.org/10.1111/jofi.12095) link measured disagreement
to index-versus-single-stock volatility-premium wedges, smile differences, and
the correlation risk premium in a heterogeneous-belief equilibrium. Different
beliefs may reflect information heterogeneity or model uncertainty without
irrationality, although biased belief formation can generate similar
observables. It is therefore misleading to classify every belief-based model
as behavioral or every equilibrium model as fully rational.

## Why the channels are not mutually exclusive

The mechanisms can operate in the same market and reinforce one another:

\[
\begin{aligned}
&\text{objective tail exposure, risk aversion, sentiment, or distorted beliefs}\\
&\quad\longrightarrow \text{demand for protection}\\
&\quad\longrightarrow \text{dealer residual risk and balance-sheet use}\\
&\quad\longrightarrow \text{an option price containing both risk compensation
and demand pressure}.
\end{aligned}
\]

A behavioral increase in crash salience can raise put demand, while a rational
dealer charges more to warehouse the resulting jump and funding risk. Likewise,
an objectively riskier environment can increase both rational insurance demand
and pessimistic sentiment. Limits to arbitrage can allow either force to have a
larger price effect. Demand, disagreement, and intermediary constraints are
therefore transmission mechanisms as well as candidate sources of the premium.

This interaction also cautions against a residual argument. Failure of one
canonical rational model does not prove behavioral mispricing, because the
model may omit rare disasters, time-varying risk aversion, or intermediary
frictions. Conversely, fitting a rational model does not prove beliefs are
unbiased, because flexible state dynamics or preference parameters may absorb
behavioral variation. [Bondarenko
(2014)](https://doi.org/10.1142/S2010139214500153), for example, rejects a
studied class of explanations for expensive S&P 500 puts; that rejection
narrows the admissible models but does not identify a unique behavioral cause.

## Evidence limits for the present study

The locked design can estimate whether `VRP_X` is positive and robust, whether
VIX variance is calibrated to the specified realized-variance target, and how
VIX forecasts compare out of sample with GARCH and a naive benchmark. It
cannot adjudicate the rational-versus-behavioral decomposition because it does
not identify the physical conditional variance, investor utility, subjective
tail probabilities, option order flow, dealer constraints, or causal sentiment
shocks.

In particular:

1. A positive mean `VRP_X` is consistent with risk compensation, probability
   weighting, belief errors, constrained intermediation, and mixtures of them.
2. Calibration rejection is not proof of irrationality: an option price is a
   state-contingent price rather than an unbiased physical forecast.
3. Good VIX forecast performance does not eliminate a premium or behavioral
   component, and poor performance does not identify either component.
4. Regime dependence can show when the proxy changes, but NBER classifications
   and the pre-defined crisis cases do not provide exogenous variation that
   separates preferences, beliefs, and constraints.
5. Rare events, overlapping observations, horizon mismatch, and
   realized-variance measurement can exaggerate apparent support for either
   narrative if they are not handled as prescribed.

The defensible conclusion is therefore comparative rather than exclusive:
rational bad-state compensation has strong theoretical foundations and
supporting option and tail evidence; behavioral research shows that sentiment,
updating, and probability weighting can also affect option prices; and market
frictions provide a channel through which both can matter. The present
empirical analysis can assess the robustness and predictive content of the
ex-post proxy, but any allocation of that proxy across these mechanisms remains
outside its identification.

## References

- Baele, L., J. Driessen, S. Ebert, J. M. Londono, and O. G. Spalt. 2019.
  “Cumulative Prospect Theory, Option Returns, and the Variance Premium.”
  *Review of Financial Studies* 32 (9): 3667–3723.
  <https://doi.org/10.1093/rfs/hhy127>.
- Bakshi, G., and N. Kapadia. 2003. “Delta-Hedged Gains and the Negative Market
  Volatility Risk Premium.” *Review of Financial Studies* 16 (2): 527–566.
  <https://doi.org/10.1093/rfs/hhg002>.
- Bollerslev, T., and V. Todorov. 2011. “Tails, Fears, and Risk Premia.”
  *Journal of Finance* 66 (6): 2165–2211.
  <https://doi.org/10.1111/j.1540-6261.2011.01695.x>.
- Bondarenko, O. 2014. “Why Are Put Options So Expensive?” *Quarterly Journal
  of Finance* 4 (3): 1450015. <https://doi.org/10.1142/S2010139214500153>.
- Broadie, M., M. Chernov, and M. Johannes. 2009. “Understanding Index Option
  Returns.” *Review of Financial Studies* 22 (11): 4493–4529.
  <https://doi.org/10.1093/rfs/hhp032>.
- Buraschi, A., F. Trojani, and A. Vedolin. 2014. “When Uncertainty Blows in
  the Orchard: Comovement and Equilibrium Volatility Risk Premia.” *Journal of
  Finance* 69 (1): 101–137. <https://doi.org/10.1111/jofi.12095>.
- Carr, P., and L. Wu. 2009. “Variance Risk Premiums.” *Review of Financial
  Studies* 22 (3): 1311–1341. <https://doi.org/10.1093/rfs/hhn038>.
- Chen, H., S. Joslin, and S. X. Ni. 2019. “Demand for Crash Insurance,
  Intermediary Constraints, and Risk Premia in Financial Markets.” *Review of
  Financial Studies* 32 (1): 228–265.
  <https://doi.org/10.1093/rfs/hhy004>.
- Drechsler, I., and A. Yaron. 2011. “What's Vol Got to Do with It?” *Review of
  Financial Studies* 24 (1): 1–45. <https://doi.org/10.1093/rfs/hhq085>.
- Gârleanu, N., L. H. Pedersen, and A. M. Poteshman. 2009. “Demand-Based
  Option Pricing.” *Review of Financial Studies* 22 (10): 4259–4299.
  <https://doi.org/10.1093/rfs/hhp005>.
- Han, B. 2008. “Investor Sentiment and Option Prices.” *Review of Financial
  Studies* 21 (1): 387–414. <https://doi.org/10.1093/rfs/hhm071>.
- Jiang, G. J., and Y. S. Tian. 2010. “Misreaction or Misspecification? A
  Re-examination of Volatility Anomalies.” *Journal of Banking & Finance* 34
  (10): 2358–2369. <https://doi.org/10.1016/j.jbankfin.2010.02.022>.
- Lochstoer, L. A., and T. Muir. 2022. “Volatility Expectations and Returns.”
  *Journal of Finance* 77 (2): 1055–1096.
  <https://doi.org/10.1111/jofi.13120>.
- Poteshman, A. M. 2001. “Underreaction, Overreaction, and Increasing
  Misreaction to Information in the Options Market.” *Journal of Finance* 56
  (3): 851–876. <https://doi.org/10.1111/0022-1082.00348>.
- Stein, J. C. 1989. “Overreactions in the Options Market.” *Journal of
  Finance* 44 (4): 1011–1023.
  <https://doi.org/10.1111/j.1540-6261.1989.tb02635.x>.
