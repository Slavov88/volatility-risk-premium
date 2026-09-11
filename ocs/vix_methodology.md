# Why VIX Is Model-Free Rather Than a Single-Option Black--Scholes IV

Cboe's VIX measures 30-calendar-day forward-looking S&P 500 volatility from SPX/SPXW option prices. It uses two expirations that bracket 30 days. For each expiration, Cboe identifies the strike \(K^*\) where call and put mid-quotes are closest, infers the forward by put--call parity, \(F=K^*+e^{RT}[C(K^*)-P(K^*)]\), and sets \(K_0\) to the first listed strike at or below \(F\). The strip contains out-of-the-money puts below \(K_0\), out-of-the-money calls above \(K_0\), and the average put/call quote at \(K_0\).

For one expiration, the annualized variance quantity is

\[
\sigma^2(T)=\frac{2}{T}\sum_i
\frac{\Delta K_i}{K_i^2}e^{RT}Q(K_i)
-\frac{1}{T}\left(\frac{F}{K_0}-1\right)^2.
\]

Here \(T\) is time to expiration in years, \(R\) is the maturity-matched risk-free rate, \(Q(K_i)\) is the selected option mid-quote, and \(\Delta K_i\) is the strike interval represented by \(K_i\). The sum is a discrete approximation to an integral across strikes: an option contributes in proportion to its price and strike interval and inversely to \(K_i^2\). The last term corrects for \(K_0\) generally differing from the forward. Quote-validity and consecutive-zero rules truncate illiquid tails.

VIX then interpolates **total variance**, not volatility. If \(M_1\le M_{30}\le M_2\) are minutes to the near-term, 30-day, and next-term endpoints, let \(w_1=(M_2-M_{30})/(M_2-M_1)\), \(w_2=(M_{30}-M_1)/(M_2-M_1)\), and \(T_j=M_j/M_{365}\). Then

\[
VIX=100\sqrt{\left(T_1\sigma_1^2w_1+T_2\sigma_2^2w_2\right)
\frac{M_{365}}{M_{30}}}.
\]

The weighted terms \(T_j\sigma_j^2\) are variance accumulated to each expiration; \(M_{365}/M_{30}\) annualizes the interpolated 30-day amount. Thus VIX is the square root of a constant-maturity variance estimate, expressed in annualized percentage volatility units.

## Why “model-free”

A single-option Black--Scholes implied volatility instead solves

\[
C^{BS}(S,K,T,R,q,\sigma_{BS})=C^{mkt}
\]

for one option's \(\sigma_{BS}\). It is conditional on the Black--Scholes pricing function, and different strikes or maturities generally produce different implied volatilities. VIX neither performs this inversion nor chooses one at-the-money option. Its cross-strike weights come from no-arbitrage static replication of a log-contract/variance payoff using a broad strip of European puts and calls. Consequently, the option strip reveals a risk-neutral variance quantity without assuming geometric Brownian motion, lognormal returns, or constant volatility. “Model-free” therefore means free of a particular parametric option-pricing model, not assumption-free.

The interpretation assumes frictionless no-arbitrage valuation, valid European payoffs and put--call parity, an appropriate discount curve, contemporaneous reliable quotes, and the integrability needed for strike replication. Exact theory uses a continuum of strikes and, for the standard quadratic-variation link, continuous prices; listed strikes, finite tails, filters, bid--ask spreads, and jumps create approximation or convention differences. Finally, VIX is risk-neutral: it embeds volatility and tail-risk compensation, so it is not automatically an unbiased physical-measure forecast of realized volatility.

## Primary sources

- [Cboe VIX Index Methodology](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf), version 6.0, revised February 26, 2026.
- [Cboe Volatility Index Mathematics Methodology](https://cdn.cboe.com/api/global/us_indices/governance/Cboe_Volatility_Index_Mathematics_Methodology.pdf), sections 3(a)--3(b).
