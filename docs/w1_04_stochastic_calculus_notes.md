# Brownian motion, geometric Brownian motion, and Itô's lemma

**Tracker task:** W1-04  
**Workstream:** Foundations  
**Role:** Econometrics  
**Status:** Worked notes; no change to the locked empirical protocol

## 1. Brownian motion

A standard Brownian motion (Wiener process) \(W_t\), \(t\geq0\), satisfies:

1. \(W_0=0\).
2. For \(0\leq s<t\), the increment \(W_t-W_s\sim N(0,t-s)\).
3. Increments over disjoint time intervals are independent.
4. Sample paths are continuous almost surely.

Thus \(E[W_t]=0\), \(\operatorname{Var}(W_t)=t\), and

\[
\operatorname{Cov}(W_s,W_t)=\min(s,t).
\]

The covariance follows by taking \(s\leq t\), writing
\(W_t=W_s+(W_t-W_s)\), and using independence of the increment:

\[
E[W_sW_t]
=E[W_s^2]+E[W_s(W_t-W_s)]
=s+0=s.
\]

For a short interval \(\Delta t\), \(\Delta W\sim N(0,\Delta t)\), so
\(\Delta W=O_p(\sqrt{\Delta t})\). Consequently, the stochastic term
dominates an ordinary \(O(\Delta t)\) drift locally. Brownian paths are
continuous but almost surely nowhere differentiable. Their quadratic
variation is nevertheless well behaved:

\[
\sum_i(W_{t_{i+1}}-W_{t_i})^2\ \xrightarrow{p}\ t
\quad\text{as the partition mesh tends to zero}.
\]

This motivates the Itô multiplication rules

\[
(dW_t)^2=dt,\qquad dW_t\,dt=0,\qquad (dt)^2=0.
\]

These are quadratic-variation bookkeeping rules, not ordinary algebraic
identities. More generally, an Itô process has dynamics

\[
dX_t=a(t,X_t)dt+b(t,X_t)dW_t,
\]

where \(a\) is its instantaneous drift and \(b^2\) is its instantaneous
variance rate. Conditional on current information \(\mathcal F_t\), a local
Euler approximation is

\[
\Delta X_t\approx a(t,X_t)\Delta t+b(t,X_t)\sqrt{\Delta t}\,Z,
\qquad Z\sim N(0,1).
\]

For econometric work, this continuous-time statement should not be confused
with an exact discrete-time likelihood unless the transition distribution is
known or the sampling approximation is justified.

## 2. Itô's lemma

Let \(X_t\) follow the Itô process above and let \(f(t,x)\) have one continuous
time derivative and two continuous state derivatives. A second-order Taylor
expansion gives

\[
df=f_tdt+f_xdX+\frac12f_{xx}(dX)^2.
\]

Substitute \(dX=a\,dt+b\,dW\). Terms of order above \(dt\) vanish, while
\((dW)^2=dt\), so

\[
(dX)^2=(a\,dt+b\,dW)^2=b^2dt.
\]

Therefore Itô's lemma is

\[
\boxed{
df(t,X_t)=
\left(f_t+a f_x+\frac12b^2f_{xx}\right)dt+b f_xdW_t.}
\]

The term \(\tfrac12b^2f_{xx}\) is the Itô correction. Ordinary chain-rule
reasoning misses it because ordinary differentiable paths have zero quadratic
variation, whereas Brownian motion does not.

For \(f(t,X_t,Y_t)\), where the shocks have instantaneous correlation \(\rho\),
the formula additionally contains \(f_{xy}\,dX_t dY_t\), with
\(dW_t^X dW_t^Y=\rho\,dt\). This cross-variation term matters in multivariate
asset-pricing and stochastic-volatility models.

## 3. Geometric Brownian motion

Geometric Brownian motion (GBM) is defined by

\[
dS_t=\mu S_tdt+\sigma S_tdW_t,
\qquad S_0>0,\quad \sigma>0.
\]

Apply Itô's lemma to \(f(S)=\log S\), for which \(f'=1/S\) and
\(f''=-1/S^2\):

\[
\begin{aligned}
d\log S_t
&=\frac1{S_t}dS_t-\frac12\frac1{S_t^2}(dS_t)^2\\
&=\left(\mu-\frac12\sigma^2\right)dt+\sigma dW_t.
\end{aligned}
\]

Integrating from \(0\) to \(t\) and exponentiating yields the exact solution

\[
\boxed{S_t=S_0\exp\!\left[
\left(\mu-\frac12\sigma^2\right)t+\sigma W_t\right].}
\]

Hence \(S_t>0\) almost surely and the continuously compounded return is
normal:

\[
\log(S_t/S_0)\sim
N\!\left((\mu-\tfrac12\sigma^2)t,\sigma^2t\right).
\]

Using the moment-generating function of a standard normal variable,
\(E[e^{\sigma W_t}]=e^{\sigma^2t/2}\), gives

\[
E[S_t]=S_0e^{\mu t},
\qquad
\operatorname{Var}(S_t)
=S_0^2e^{2\mu t}(e^{\sigma^2t}-1).
\]

The distinction between the arithmetic expected-return parameter \(\mu\) and
the log-growth rate \(\mu-\sigma^2/2\) is economically important. In derivative
pricing, a change from the physical measure \(P\) to a risk-neutral measure
\(Q\) replaces the appropriate asset drift by the risk-free carry (under the
model's assumptions), but does not make \(P\)- and \(Q\)-expectations of future
variance interchangeable.

GBM is the constant-volatility foundation for Black--Scholes, not a maintained
empirical description of equity-index volatility. It has no volatility
clustering, leverage effect, stochastic volatility, or jumps. The project's
VIX is a model-free SPX option-strip variance measure, never the
Black--Scholes implied volatility of a single option.

## 4. Solved examples

### Example 1 — Brownian transition and conditional probability

Suppose \(W_1=0.30\). Find the conditional distribution of \(W_{1.25}\) and
\(P(W_{1.25}>0.50\mid W_1=0.30)\).

Independent increments imply

\[
W_{1.25}\mid W_1=0.30
=0.30+(W_{1.25}-W_1)
\sim N(0.30,0.25).
\]

The conditional standard deviation is \(\sqrt{0.25}=0.50\). Therefore

\[
P(W_{1.25}>0.50\mid W_1=0.30)
=1-\Phi\!\left(\frac{0.50-0.30}{0.50}\right)
=1-\Phi(0.4)\approx0.3446.
\]

The variance is elapsed time, \(0.25\); confusing it with the standard
deviation \(0.50\) is a common scaling error.

### Example 2 — Exact GBM distribution and moments

Let \(S_0=100\), \(\mu=0.08\), \(\sigma=0.20\), and \(T=1\) year. Then

\[
\log(S_1/100)\sim N(0.08-0.20^2/2,\,0.20^2)=N(0.06,0.04).
\]

The median terminal price sets the normal shock to its median zero:

\[
\operatorname{Med}(S_1)=100e^{0.06}\approx106.18.
\]

The mean and variance are

\[
E[S_1]=100e^{0.08}\approx108.33,
\]

\[
\operatorname{Var}(S_1)
=100^2e^{0.16}(e^{0.04}-1)
\approx478.92,
\]

so \(\operatorname{SD}(S_1)\approx21.88\). The mean exceeds the median because
the lognormal distribution is right-skewed.

### Example 3 — Itô transform of a squared diffusion

Let \(dX_t=\kappa(\theta-X_t)dt+\eta dW_t\). Derive the dynamics of
\(Y_t=X_t^2\).

For \(f(x)=x^2\), \(f'(x)=2x\) and \(f''(x)=2\). Itô's lemma gives

\[
\begin{aligned}
dY_t
&=2X_t\,dX_t+\frac12(2)(dX_t)^2\\
&=\left[2\kappa X_t(\theta-X_t)+\eta^2\right]dt
+2\eta X_tdW_t.
\end{aligned}
\]

The \(+\eta^2dt\) term is the Itô correction. Taking expectations, provided
the needed moments exist, removes the stochastic integral:

\[
\frac{d}{dt}E[X_t^2]
=2\kappa\theta E[X_t]-2\kappa E[X_t^2]+\eta^2.
\]

This illustrates why second-moment dynamics cannot be obtained by applying an
ordinary chain rule.

### Example 4 — Expected integrated variance under GBM

Under GBM, the instantaneous variance rate of the log price is constant:

\[
d\log S_t=(\mu-\tfrac12\sigma^2)dt+\sigma dW_t.
\]

Over a horizon \(T\), integrated variance is therefore

\[
\int_t^{t+T}\sigma^2du=\sigma^2T.
\]

If \(\sigma=0.20\) per square-root year and \(T=30/365\), then

\[
\sigma^2T=0.20^2\frac{30}{365}\approx0.003288.
\]

Annualizing the horizon variance with the project's exact-calendar convention
recovers

\[
\frac{365}{30}(0.003288)=0.0400,
\]

an annualized variance of \(0.04\), corresponding to annualized volatility
\(\sqrt{0.04}=0.20\). In data, the primary ex-post target replaces the
unobserved integral by the sum of squared close-to-close log returns ending on
exchange dates \(d\) such that \(t<d\leq t+30\) calendar days, annualized by
\(365/30\). The strict inequality ensures that no return dated \(t\) enters a
forward target.

## 5. Econometric takeaways for this project

- Diffusion variance accumulates in time, so variance is additive across a
  horizon; volatility is its square root and is not additive. This supports
  conducting the primary VRP analysis in variance space.
- Under constant \(\sigma\), squared high-frequency increments estimate
  integrated variance. With discrete daily observations, realized variance is
  an ex-post noisy proxy and not itself \(E_t^P[\text{future variance}]\).
- The theoretical variance risk premium compares conditional expectations
  under \(Q\) and \(P\). The project's empirical \(VRP_t^X=IVAR_t-RVAR_t\)
  instead subtracts a realized outcome, so it also contains forecast error and
  measurement effects.
- Overlapping forward horizons reuse many of the same squared returns, inducing
  serial dependence even if primitive returns were independent. This is why
  the locked design requires overlap-aware HAC/Newey--West inference and a
  deterministic non-overlapping robustness sample.
- GBM provides transparent derivations and Black--Scholes foundations, but its
  constant conditional variance is precisely why richer conditional-variance
  models such as the protocol's GARCH(1,1) are needed for forecast comparison.

## 6. Formula checklist

\[
W_t-W_s\sim N(0,t-s),\qquad [W]_t=t,
\]

\[
df=(f_t+af_x+\tfrac12b^2f_{xx})dt+bf_xdW,
\]

\[
dS=\mu Sdt+\sigma SdW
\Longrightarrow
S_t=S_0e^{(\mu-\sigma^2/2)t+\sigma W_t},
\]

\[
E[S_t]=S_0e^{\mu t},\qquad
\operatorname{Var}(S_t)=S_0^2e^{2\mu t}(e^{\sigma^2t}-1).
\]
