# Black--Scholes PDE from a delta-hedged replicating portfolio

**Tracker task:** W2-01

**Workstream:** Black--Scholes theory

**Role:** Econometrics

**Dependency:** W1-04

**Status:** Complete hand derivation; no change to the locked empirical protocol

## 1. Claim

Let \(V(t,S)\) be the time-\(t\) value of a European derivative written on a
non-dividend-paying stock. Under the assumptions below, absence of arbitrage
implies that, for \(0\leq t<T\) and \(S>0\),

\[
\boxed{
V_t(t,S)
+\frac{1}{2}\sigma^2S^2V_{SS}(t,S)
+rS V_S(t,S)
-rV(t,S)=0.}
\]

The terminal condition is

\[
\boxed{V(T,S)=\Phi(S),}
\]

where \(\Phi\) is the derivative payoff. For a European call and put,
respectively,

\[
\Phi_C(S)=(S-K)^+,
\qquad
\Phi_P(S)=(K-S)^+,
\qquad
x^+=\max(x,0).
\]

The derivation uses a dynamically rebalanced stock--bond portfolio to
replicate the derivative. Equivalently, the difference between the
replicating portfolio and the derivative is delta hedged.

## 2. Assumptions

1. **Stock dynamics.** Under the physical probability measure \(P\), the stock
   follows geometric Brownian motion

   \[
   dS_t=\mu S_t\,dt+\sigma S_t\,dW_t,
   \qquad S_t>0,\quad \sigma>0,
   \]

   where \(\mu\), \(\sigma\), and the continuously compounded risk-free rate
   \(r\) are constant.
2. **Risk-free asset.** A money-market account \(B_t\) is traded:

   \[
   dB_t=rB_t\,dt,
   \qquad B_t=B_0e^{rt}.
   \]
3. **No dividends.** The stock pays no dividends before \(T\).
4. **European payoff.** The derivative pays \(\Phi(S_T)\) only at the fixed
   maturity \(T\).
5. **Regularity.** For \(t<T\), \(V(t,S)\) is once continuously differentiable
   in \(t\) and twice continuously differentiable in \(S\), so Itô's lemma
   applies. The call and put payoff kink at \(T\) does not require the terminal
   payoff itself to be differentiable.
6. **Idealized trading.** Trading is continuous; stock and bond positions can
   be adjusted without transaction costs, taxes, bid--ask spreads, or
   indivisibilities; short selling and borrowing are allowed at the same rate
   \(r\).
7. **Continuous paths and known model inputs.** There are no jumps, and
   \(\sigma\) is known and constant.
8. **No arbitrage and self-financing replication.** Rebalancing is financed
   entirely within the stock--bond portfolio. No cash is injected or removed
   after inception. A locally riskless self-financing position must earn the
   risk-free rate.

These assumptions make the one-Brownian-risk market complete: the stock and
bond span the derivative's local risk. The PDE is a conditional no-arbitrage
result under these assumptions, not an empirical claim that actual index
returns have constant volatility or continuous paths.

## 3. Itô expansion of the derivative

Write \(V_t=\partial V/\partial t\), \(V_S=\partial V/\partial S\), and
\(V_{SS}=\partial^2V/\partial S^2\). A second-order stochastic Taylor
expansion gives

\[
dV
=V_t\,dt+V_S\,dS+\frac{1}{2}V_{SS}(dS)^2.
\]

The omitted second- and higher-order terms vanish under the Itô rules
\((dt)^2=0\), \(dt\,dW=0\), and \((dW)^2=dt\). In particular,

\[
\begin{aligned}
(dS)^2
&=(\mu S\,dt+\sigma S\,dW)^2\\
&=\mu^2S^2(dt)^2
  +2\mu\sigma S^2\,dt\,dW
  +\sigma^2S^2(dW)^2\\
&=0+0+\sigma^2S^2\,dt\\
&=\sigma^2S^2\,dt.
\end{aligned}
\]

Substitute \(dS=\mu S\,dt+\sigma S\,dW\) and
\((dS)^2=\sigma^2S^2dt\) into the expansion:

\[
\begin{aligned}
dV
&=V_t\,dt
  +V_S(\mu S\,dt+\sigma S\,dW)
  +\frac{1}{2}V_{SS}\sigma^2S^2\,dt\\
&=V_t\,dt
  +\mu S V_S\,dt
  +\sigma S V_S\,dW
  +\frac{1}{2}\sigma^2S^2V_{SS}\,dt\\
&=\left(
V_t+\mu S V_S+\frac{1}{2}\sigma^2S^2V_{SS}
\right)dt
+\sigma S V_S\,dW.
\end{aligned}
\]

Thus the derivative has local diffusion exposure
\(\sigma S V_S\,dW\).

## 4. Construct the self-financing replicating portfolio

At time \(t\), let

- \(\Delta_t\) be the number of stock shares held; and
- \(\beta_t\) be the number of money-market-account units held.

The replicating portfolio value is

\[
X_t=\Delta_tS_t+\beta_tB_t.
\]

Replication requires equality of values:

\[
X_t=V(t,S_t).
\]

Solving the value equation for the bond holding gives

\[
\begin{aligned}
\beta_tB_t
&=X_t-\Delta_tS_t\\
&=V(t,S_t)-\Delta_tS_t,
\end{aligned}
\]

and hence

\[
\beta_t=\frac{V(t,S_t)-\Delta_tS_t}{B_t}.
\]

Because the strategy is self financing, changes in portfolio value come only
from gains and losses on the assets already held:

\[
dX_t=\Delta_t\,dS_t+\beta_t\,dB_t.
\]

There are no \(S_t\,d\Delta_t\), \(B_t\,d\beta_t\), or cross-variation terms
in this gains equation. Changes in holdings satisfy the self-financing
financing constraint: the cost of buying one asset is funded by selling the
other. Substituting the stock and bond dynamics gives

\[
\begin{aligned}
dX_t
&=\Delta_t(\mu S_t\,dt+\sigma S_t\,dW_t)
  +\beta_t(rB_t\,dt)\\
&=\Delta_t\mu S_t\,dt
  +\Delta_t\sigma S_t\,dW_t
  +r\beta_tB_t\,dt.
\end{aligned}
\]

Use \(\beta_tB_t=V-\Delta_tS_t\):

\[
\begin{aligned}
dX_t
&=\Delta_t\mu S_t\,dt
  +\Delta_t\sigma S_t\,dW_t
  +r(V-\Delta_tS_t)\,dt\\
&=\left[
\Delta_t\mu S_t+rV-r\Delta_tS_t
\right]dt
+\Delta_t\sigma S_t\,dW_t.
\end{aligned}
\]

## 5. Match the stochastic exposures: the delta hedge

Exact local replication requires \(dX_t=dV_t\). First match the coefficients
of the common Brownian shock \(dW_t\):

\[
\Delta_t\sigma S_t=\sigma S_tV_S.
\]

Because \(\sigma>0\) and \(S_t>0\), divide both sides by \(\sigma S_t\):

\[
\boxed{\Delta_t=V_S(t,S_t).}
\]

This is the Black--Scholes delta. Substituting \(\Delta_t=V_S\) into the
replicating-portfolio dynamics gives

\[
dX_t
=\left[
\mu S V_S+rV-rS V_S
\right]dt
+\sigma S V_S\,dW.
\]

The derivative dynamics from Itô's lemma are

\[
dV
=\left[
V_t+\mu S V_S+\frac{1}{2}\sigma^2S^2V_{SS}
\right]dt
+\sigma S V_S\,dW.
\]

The diffusion terms are now identical. Matching the drift terms step by step,

\[
V_t+\mu S V_S+\frac{1}{2}\sigma^2S^2V_{SS}
=\mu S V_S+rV-rS V_S.
\]

Subtract \(\mu S V_S\) from both sides:

\[
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
=rV-rS V_S.
\]

Subtract \(rV-rS V_S\) from both sides:

\[
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
-rV+rS V_S=0.
\]

Reorder the terms:

\[
\boxed{
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
+rS V_S-rV=0.}
\]

This is the Black--Scholes PDE for a non-dividend-paying underlying.

## 6. The same result as an explicit delta-hedged position

The preceding replication argument can be written as a hedge of one derivative
liability. Form a portfolio that is long \(\Delta_t\) shares, short one
derivative, and long \(\eta_t\) units of the money-market account:

\[
H_t=\Delta_tS_t-V(t,S_t)+\eta_tB_t.
\]

The money-market position finances changes in \(\Delta_t\); it cannot in
general be omitted from a dynamically rebalanced self-financing strategy.
Applying the stochastic product rule to the portfolio value gives its total
differential:

\[
\begin{aligned}
dH_t
={}&d(\Delta_tS_t)-dV_t+d(\eta_tB_t)\\
={}&\Delta_t\,dS_t+S_t\,d\Delta_t+d[\Delta,S]_t-dV_t\\
&+\eta_t\,dB_t+B_t\,d\eta_t+d[\eta,B]_t.
\end{aligned}
\]

Because \(B_t\) has finite variation, \(d[\eta,B]_t=0\). Self financing
means that rebalancing purchases are paid for entirely by rebalancing sales,
so the changes in holdings obey

\[
S_t\,d\Delta_t+B_t\,d\eta_t+d[\Delta,S]_t+d[\eta,B]_t=0.
\]

Consequently, the total differential of the self-financing portfolio equals
its gains process:

\[
dH_t=\Delta_t\,dS_t-dV_t+\eta_t\,dB_t.
\]

Thus this equation is not obtained by differentiating
\(\Delta_tS_t-V(t,S_t)\) and discarding rebalancing terms; those terms are
offset by the explicitly imposed financing condition. Equivalently, over
each infinitesimal holding interval, the predictable holdings
\(\Delta_t\) and \(\eta_t\) are fixed at the interval's left endpoint while
asset gains accrue, and the endpoint rebalance is financed within the
portfolio.

Substitute the stock, derivative, and money-market dynamics without skipping
terms:

\[
\begin{aligned}
dH
={}&\Delta(\mu S\,dt+\sigma S\,dW)\\
&-\left[
\left(
V_t+\mu S V_S+\frac{1}{2}\sigma^2S^2V_{SS}
\right)dt
+\sigma S V_S\,dW
\right]
+\eta rB\,dt\\
={}&\left[
\Delta\mu S
-V_t-\mu S V_S-\frac{1}{2}\sigma^2S^2V_{SS}
+\eta rB
\right]dt\\
&+\left[
\Delta\sigma S-\sigma S V_S
\right]dW.
\end{aligned}
\]

Choose \(\Delta=V_S\). The Brownian coefficient becomes

\[
\begin{aligned}
\Delta\sigma S-\sigma S V_S
&=V_S\sigma S-\sigma S V_S\\
&=0,
\end{aligned}
\]

and the physical-drift terms become

\[
\begin{aligned}
\Delta\mu S-\mu S V_S
&=V_S\mu S-\mu S V_S\\
&=0.
\end{aligned}
\]

Therefore

\[
dH
=-\left(
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
\right)dt
+\eta rB\,dt.
\]

The hedge is locally riskless, so no arbitrage requires its gain to equal the
risk-free return on its current value:

\[
dH=rH\,dt.
\]

Since \(H=SV_S-V+\eta B\),

\[
dH=r(SV_S-V+\eta B)\,dt.
\]

Equate the two expressions for \(dH\):

\[
-\left(
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
\right)dt+\eta rB\,dt
=r(SV_S-V+\eta B)\,dt.
\]

Expand the right-hand side:

\[
-\left(
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
\right)dt+\eta rB\,dt
=rSV_S\,dt-rV\,dt+\eta rB\,dt.
\]

Subtract \(\eta rB\,dt\) from both sides:

\[
-\left(
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
\right)dt
=r(SV_S-V)\,dt.
\]

Divide by \(dt>0\):

\[
-V_t-\frac{1}{2}\sigma^2S^2V_{SS}
=rS V_S-rV.
\]

Move every term to the left:

\[
-V_t-\frac{1}{2}\sigma^2S^2V_{SS}
-rS V_S+rV=0.
\]

Multiply by \(-1\):

\[
\boxed{
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
+rS V_S-rV=0.}
\]

The explicit hedge and the stock--bond replication produce the same PDE.

## 7. Why no arbitrage forces the risk-free return

After setting \(\Delta=V_S\), the \(dW\) term vanishes over the local interval.
Suppose the resulting self-financing hedge earned a deterministic rate greater
than \(r\). An arbitrageur could borrow its initial value at rate \(r\), buy
the hedge, and retain a positive riskless difference. If it earned less than
\(r\), the arbitrageur could short the hedge and invest the proceeds in the
money-market account. Hence a locally riskless self-financing position must
satisfy \(dH=rHdt\).

This argument also explains why the physical expected-return parameter
\(\mu\) disappears. Delta hedging cancels the shared Brownian shock and the
associated \(\mu S V_S\) exposure. The PDE depends on the risk-free rate,
volatility, time, and payoff, but not on investors' physical expected stock
return.

## 8. Terminal and boundary conditions for calls and puts

The PDE alone does not identify a unique derivative price; it is paired with
the terminal payoff. For a call \(C(t,S)\),

\[
C(T,S)=(S-K)^+.
\]

The standard limiting conditions are

\[
C(t,0)=0
\]

and, as \(S\to\infty\),

\[
C(t,S)\sim S-Ke^{-r(T-t)}.
\]

For a put \(P(t,S)\),

\[
P(T,S)=(K-S)^+.
\]

The standard limiting conditions are

\[
P(t,0)=Ke^{-r(T-t)}
\]

and, as \(S\to\infty\),

\[
P(t,S)\to0.
\]

These conditions complete the call and put boundary-value problems. Solving
them yields the Black--Scholes closed-form prices; that solution is separate
from the present PDE derivation.

## 9. Algebra and interpretation checks

### 9.1 Portfolio identity

With \(\Delta=V_S\), the bond position is

\[
\beta B=V-SV_S.
\]

Therefore

\[
\Delta S+\beta B
=SV_S+(V-SV_S)
=V,
\]

so the stock--bond holdings reproduce the derivative's value.

### 9.2 Drift identity implied by the PDE

Starting from the PDE,

\[
V_t+\frac{1}{2}\sigma^2S^2V_{SS}+rSV_S-rV=0,
\]

isolate the terms that do not contain \(rSV_S-rV\):

\[
V_t+\frac{1}{2}\sigma^2S^2V_{SS}
=rV-rSV_S.
\]

Add \(\mu SV_S\) to both sides:

\[
V_t+\mu SV_S+\frac{1}{2}\sigma^2S^2V_{SS}
=\mu SV_S+rV-rSV_S.
\]

The left side is the derivative's Itô drift. The right side is the
replicating portfolio's drift when \(\Delta=V_S\). Their diffusion
coefficients are both \(\sigma SV_S\), confirming \(dV=dX\).

### 9.3 Dimensional check

If \(V\) and \(S\) are measured in currency and \(t\) in years, then
\(V_t\), \(\sigma^2S^2V_{SS}\), \(rSV_S\), and \(rV\) are all measured in
currency per year. Every PDE term therefore has the same units.

## 10. Scope and project interpretation

This derivation is the no-dividend core model authorized for Track A. A real
SPX option validation must separately address dividends, rates, bid--ask
spreads, quote timing, exercise and settlement conventions, and contract
details, as required by the locked protocol.

Nothing here redefines Track B. In particular:

- a Black--Scholes implied volatility is obtained by inverting one option's
  parametric pricing equation;
- VIX is quoted as 100 times annualized 30-day expected volatility derived
  from a model-free SPX option strip; and
- the empirical variance-space quantity remains
  \(IVAR_t=(VIX_t/100)^2\), not a single-option Black--Scholes variance.

The exact forward 30-calendar-day target, fixed-21-trading-day robustness,
premium sign, overlap-aware inference, out-of-sample design, sample endpoints,
and all other locked scientific choices remain unchanged.

## References

- Black, F., and M. Scholes. 1973. “The Pricing of Options and Corporate
  Liabilities.” *Journal of Political Economy* 81 (3): 637--654.
  <https://doi.org/10.1086/260062>.
- Merton, R. C. 1973. “Theory of Rational Option Pricing.” *Bell Journal of
  Economics and Management Science* 4 (1): 141--183.
  <https://doi.org/10.2307/3003143>.
- Project dependency: [`w1_04_stochastic_calculus_notes.md`](w1_04_stochastic_calculus_notes.md).
- Authoritative project protocol:
  [`../paper/method_protocol.md`](../paper/method_protocol.md), Section 16.
