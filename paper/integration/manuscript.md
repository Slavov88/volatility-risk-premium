---
title: 'The Volatility Risk Premium: An Empirical and Theoretical Investigation of the Gap Between Implied and Realized Volatility in Equity Index Markets'
---

# Abstract

Option-implied volatility can contain information about future fluctuations while exceeding their subsequent realization. These two properties answer different economic questions. We study them jointly for the S&P 500 and VIX, matching the implied horizon to a realized-variance proxy formed from returns ending within the following 30 calendar days and accounting for overlapping outcomes. Over the frozen 1990–2025 forecast-origin sample, the mean implied-minus-realized variance proxy is 0.01135 annualized decimal variance (95% HAC confidence interval 0.00723–0.01547; 9,064 origins). Joint unbiased calibration is rejected. In the 2007–2025 out-of-sample comparison, VIX has lower variance RMSE than expanding Gaussian GARCH(1,1), 0.06864 versus 0.07213, but their mean squared-loss difference is uncertain: −0.000491 (95% interval −0.001547–0.000564; p=0.3615). VIX contributes predictive information conditional on GARCH; the reverse contribution is imprecise in the primary specification and sensitive to the estimation window. The NBER recession shift is also imprecise. Later samples and alternative realized-variance estimators materially qualify the full-sample conclusion. The evidence supports a positive long-run ex-post variance gap, with useful option-market information, without separately identifying the conditional economic premium or its compensation mechanism. All empirical results remain provisional pending independent coauthor review.

# Introduction and research questions

The price of protection and the realized cost of the insured event need not coincide. Options are valued under risk-neutral probabilities, which embed the market price of risk; subsequent realized variance is one physical outcome. An implied measure can therefore systematically exceed realized variance without becoming an uninformative forecast. Conversely, an observed positive average gap does not establish that its entire magnitude rewards investors for bearing volatility risk. Forecast errors, differences between continuous and discrete measurements, horizon alignment, and data quality all enter the empirical comparison.

This study separates three questions that are frequently compressed into a single statement that implied volatility is “too high.” First, does implied variance exceed subsequent realized variance on average when both refer to a common horizon? Second, is VIX variance calibrated to physical realized variance, and how does its forecast accuracy compare with a recursively estimated time-series model? Third, does the observed gap change across externally dated business-cycle regimes or during pre-defined crisis years? The distinction matters for interpretation: an average premium, an unbiased forecast, and a forecast with low expected loss are different objects.

Our confirmatory analysis fixes five hypotheses. H1 tests the unconditional mean of the ex-post variance-premium proxy. H2 jointly tests the intercept and slope restrictions defining unbiased VIX variance calibration. H3 compares VIX and GARCH under squared-error loss out of sample, with two historical-variance benchmark contrasts treated as secondary. H4 asks whether each forecast contributes information conditional on the other. H5 tests a recession-minus-expansion difference using the NBER chronology. The expected positive sign of H1 motivates the inquiry but does not replace its two-sided test. Protocol 1.1.0, its dated amendments, and the interim data amendment determine the design; the descriptive crisis windows do not substitute for H5.

The contribution is a disciplined comparison of economic objects and statistical claims. The calendar window aligns the realized proxy with VIX's constant-maturity definition. A nontrading endpoint leaves the final partial interval unobserved, as discussed in Appendix A. The outcome panel retains all available S&P 500 returns even where VIX predictors are unavailable. Common forecast masks prevent model rankings from reflecting different evaluation dates. Overlap-aware inference distinguishes a large number of daily origins from an equally large number of independent monthly outcomes. Finally, the corrected forecasting results use an origin-specific scheduled exchange calendar: future unscheduled closures cannot silently improve a forecast by changing the number of sessions it was assumed to predict.

# Option prices, physical forecasts and insurance

Let \(\mathcal V\) be the same integrable annualized variance payoff in both expectations, \(M_{t,T}>0\) a terminal stochastic discount factor, and \(Q\) the measure induced by its normalized density. Assume deterministic discounting for the following comparison. Pricing implies
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

# Data, provenance, and measurement

The primary empirical market is the S&P 500 price index paired with the official Cboe daily VIX close. The price index excludes reinvested dividends and must not be confused with SPY or a total-return index. Yahoo Finance `^GSPC`, obtained through the pinned acquisition environment with automatic adjustment disabled, is the canonical OHLC source. FRED SP500 is a validation overlay where available; it never automatically replaces a Yahoo observation. The acquisition history includes a removal and subsequent restoration of this optional validation after transport failures. These decisions and their review states remain documented rather than erased from the record.

Forecast origins begin with common valid observations on or after 1990-01-02 and end on 2025-12-31. Outcome support extends through 2026-02-02 so that already-valid late-2025 origins retain complete future targets. These later returns create no 2026 confirmatory origins or predictor information. The interim pathway preserves 9,088 S&P 500 rows, including 21 outcome-support rows after 2025, and yields 9,064 complete core origins.

The official Cboe CSV did not pass the original strict OHLC/calendar gate. The authorized interim pathway instead validates finite positive unique CLOSE observations against available HIGH/LOW bounds, excludes 28 non-exchange dates, and retains 47 OPEN-only defects as warnings. Exactly one absent predictor, 1999-12-31, is inserted from a hash-verified official archival spreadsheet with VIX close 24.64 percentage points; three other unavailable VIX dates are excluded without interpolation. Missing predictors never delete S&P returns needed by another origin's target. The original rejected acquisition and prior candidate remain preserved. This pathway has author-reported authorization, and provisional H1–H5 execution was subsequently authorized before independent review; neither action supplies independent scientific acceptance.

Two comparability issues remain relevant. First, the daily historical VIX close is not established to be perfectly synchronized to the S&P cash close throughout the sample. Current VIX dissemination extends later into the afternoon, so its operational end-of-day information set may have a timing advantage. Second, the VIX series spans methodology changes. We retain the full sample and report sensitivities beginning in 2004 and on 2014-10-06, the weekly-option inclusion transition. These checks assess sensitivity rather than recover an invariant historical instrument.

Let $C_t$ denote the S&P close and $r_d=\log(C_d/C_{d-1})$. All internal returns and volatilities use decimals. Define

$$
I_t=(VIX_t/100)^2,\qquad
Y_t=\frac{365}{30}\sum_{d:t<d\leq t+30\mathrm{c}}r_d^2,
\qquad X_t=I_t-Y_t.
$$

The sum includes actual exchange return-ending dates strictly after the origin. It requires the entire calendar interval; targets are never shortened at the sample boundary. The number of sessions may vary because the economic horizon is fixed in calendar time. Our primary empirical object $X_t$ is the **ex-post variance-risk-premium proxy**, with the sign convention implied minus realized. The secondary volatility gap is $VIX_t/100-\sqrt{Y_t}$; the square root makes this a different estimand.

The theoretical conditional premium,

$$
\Pi_t=E_t^Q[V_{t,t+30\mathrm c}]-E_t^P[V_{t,t+30\mathrm c}],
$$

contains two expectations rather than one price-derived measure and one realization. Even if $I_t$ closely approximated the risk-neutral expectation of the same variance object, $X_t$ would equal a conditional premium plus a physical forecast error. Differences between VIX construction and discrete daily squared returns add further measurement terms. Accordingly, the present design estimates the mean proxy and its predictive properties; it does not observe $\Pi_t$ directly.

## Data diagnostics

Across 9,066 adjacent daily price-index returns through 2025, the mean log return is 0.000325 and its sample standard deviation is 0.011385. Skewness is −0.365 and excess kurtosis is 10.884. The 21-lag Ljung–Box statistic for squared returns is 11,363.1, and the 10-lag ARCH-LM statistic is 2,325.6. The correlation of the return with the next squared return is −0.100. The distribution has substantial tails and squared returns cluster, which makes conditional variance a relevant forecast target. These diagnostics use the price series before the VIX-origin mask.



\begin{center}\includegraphics[width=0.88\linewidth]{figures/return-diagnostics.pdf}\end{center}

*Figure 1. The figure compares empirical standardized return quantiles with Gaussian quantiles and plots autocorrelations through 21 sessions. Returns end by December 2025. The dashed diagonal in panel A is the Gaussian reference.*


# Statistical methods

We estimate H1 by regressing $X_t$ on a constant. Daily forward outcomes overlap, creating mechanically dependent observations. The primary Newey–West covariance uses a Bartlett kernel with lag $L_0$, derived mechanically as the greatest ordered origin lag whose target-return sets overlap. Here $L_0=21$. We also report lags 42 and 63. Covariances apply the finite-sample correction $N/(N-k)$; intervals and two-sided p-values use asymptotic normal critical values. These are HAC standard errors, not independent-observation standard errors. The deterministic non-overlap sensitivity starts with the earliest eligible origin and repeatedly selects the first origin strictly after the previous target ends. Eliminating mechanical overlap does not establish complete serial independence.

H2 is the Mincer–Zarnowitz regression

$$Y_t=a+bI_t+u_t,$$

with the joint Wald null $(a,b)=(0,1)$. Individual zero-coefficient tests address different restrictions; in particular, rejecting $b=0$ is not a calibration test. Point estimates use OLS and the same target-specific HAC rule.

The GARCH benchmark has a constant return mean and conditional daily variance

$$r_t=\mu+\epsilon_t,\qquad
\sigma_t^2=\omega+\alpha\epsilon_{t-1}^2+\beta\sigma_{t-1}^2.$$

The primary innovation distribution is Gaussian, with Student-$t$ robustness. Fits use percentage returns for numerical conditioning; resulting variances are divided by 10,000 before aggregation. Initial estimation uses returns through the final trading date of 2006. Models are recursively re-estimated using only information available at each 2007–2025 origin; an expanding window is primary, and a five-year rolling window is the required sensitivity. The naive forecast uses only historical variance on the prescribed backward-looking horizon.

For calendar forecasts, daily GARCH conditional variances are summed over the sessions scheduled under the origin's information restriction and annualized by $365/30$. Realized outcomes use actual exchange dates. The registered calendar repair replaces the original use of a retrospectively complete calendar with this scheduled-session convention. It conservatively excludes future ad-hoc closures even where some notices might already have existed; it is an operational restriction, not a claim to exhaust every historical public announcement. Cached fits and first-step states were retained, so the correction changes forecast aggregation rather than estimated model parameters. Appendix C distinguishes the historical cache replay from the independent computations on recovered observations.

H3 computes RMSE and MAE on one common mask and tests the paired loss differential

$$d_t=(Y_t-I_t)^2-(Y_t-\widehat G_t)^2.$$

Negative $E[d_t]$ favors VIX. The primary contrast is VIX versus Gaussian expanding GARCH. The VIX-versus-naive and GARCH-versus-naive tests receive Holm adjustment within their two-test secondary family at each specified setting. QLIKE is a robustness loss, not a substitute selected according to its ranking.

H4 estimates

$$Y_t=a+bI_t+g\widehat G_t+u_t.$$

Tests of $g=0$ and $b=0$ ask about incremental linear predictive information. They do not test causality, market efficiency, or jointly unbiased calibration. H5 estimates $X_t=a+\delta R_t+u_t$, where the origin inherits its month's NBER recession status. Peak months are excluded and trough months included. These ex-post labels never enter a forecast. The formal null is $\delta=0$ with the H1 HAC convention. Entire calendar years 2008, 2020, and 2022 are separately frozen descriptive windows.

# Confirmatory results

## H1. The average variance gap

The full-sample mean proxy is 0.011349 annualized decimal variance, with HAC standard error 0.002103 and 95% interval [0.007228, 0.015470]. The two-sided p-value is $6.7547\times10^{-8}$. Of 9,064 origins, 86.00% have a positive proxy, and the median is 0.012399. The positive fraction describes frequency, while the mean also depends on magnitudes. Nevertheless, the proxy is strongly asymmetric during abrupt volatility shocks. The minimum is −0.842627 on 2020-02-26, whereas the maximum is 0.324946 on 2008-12-01. These observations remain untrimmed.

The secondary mean volatility gap is 0.041169 in annualized decimal volatility, or 4.117 percentage points (95% interval 3.587–4.647 percentage points). This is an intuitive presentation of a separate nonlinear quantity. Taking the square root of the mean variance proxy would not recover it.

The post-2014 mean remains positive at 0.006668, but its 95% interval [−0.002536, 0.015873] includes zero (p=0.1556; 2,827 origins). The result therefore supports a positive full-sample average more clearly than a stable positive mean in every historical subsample. The difference in statistical precision and point estimates does not by itself establish a structural break.



\begin{center}\includegraphics[width=0.88\linewidth]{figures/mean-premium.pdf}\end{center}

*Figure 2. Mean close-to-close variance gaps and 95% intervals. All rows use the overlapping design except the explicitly labeled row, which uses the earliest eligible non-overlapping phase. Samples are nested, so this figure does not test a break.*

## H2. Calibration to realized variance

The calibration regression gives $\hat a=-0.005365$ (HAC SE 0.003549; 95% interval [−0.012321, 0.001592]) and $\hat b=0.863714$ (SE 0.108477; interval [0.651103, 1.076326]). The regression explains 37.22% of the sample variation in realized variance. The covariance-aware joint restriction $(a,b)=(0,1)$ is rejected, with Wald $\chi^2(2)=42.5063$ and p=$5.8868\times10^{-10}$.

Both marginal confidence intervals contain their respective calibration values, despite the joint rejection. This is possible because the joint statistic uses their covariance and tests the restriction in two dimensions. An individual test of the slope against zero would be especially misleading here: a forecast can contain substantial information and still be biased for physical realized variance. Calibration rejection is compatible with a priced risk component, but does not identify one. Post-2014 calibration is not rejected (joint p=0.3427), reinforcing the need to avoid a timeless claim of miscalibration.

## H3. Out-of-sample loss

On 4,780 common out-of-sample origins, VIX variance has the smallest RMSE among the primary three forecasts. Its MAE exceeds the GARCH MAE, however, so the preferred model depends on how errors are weighted.

| Forecast | RMSE | MAE | QLIKE | Mean forecast minus outcome |
|:--|--:|--:|--:|--:|
| VIX variance | 0.068636 | 0.028326 | 0.370235 | 0.007472 |
| Gaussian expanding GARCH | 0.072126 | 0.024795 | 0.380240 | −0.001091 |
| Historical variance | 0.084223 | 0.028729 | 0.576764 | 0.000874 |


The primary mean VIX-minus-GARCH squared-loss difference is −0.00049134, with HAC SE 0.00053841, 95% interval [−0.00154660, 0.00056392], and p=0.3615. The interval spans both an advantage and a disadvantage on the squared-loss scale. Failure to reject equal expected squared loss is neither proof of equality nor evidence that the lower sample RMSE is illusory. It means the sample ranking is uncertain after accounting for dependence and volatile losses. The two secondary naive comparisons also remain uncertain after Holm adjustment: both adjusted p-values are 0.2023.

QLIKE gives VIX a slightly lower sample loss, but its paired differential also spans zero (mean −0.010005, interval [−0.062309, 0.042299], p=0.7077). This complements the squared-loss result rather than furnishing an independent declaration of superiority.



\begin{center}\includegraphics[width=0.88\linewidth]{figures/forecast-loss.pdf}\end{center}

*Figure 3. Corrected mean VIX-minus-GARCH squared loss, with lag-21 Bartlett HAC 95% intervals. Negative values favor VIX. The horizontal scale multiplies annualized decimal variance squared by 1,000. All results use the 30-calendar-day close-to-close target.*

## H4. Incremental forecast information

In the corrected primary encompassing regression, the VIX coefficient is 0.679464 (95% interval [0.333339, 1.025589], p=0.0001193), while the GARCH coefficient is 0.205690 (interval [−0.201953, 0.613333], p=0.3227). The intercept is −0.000311 and $R^2=0.369442$. These estimates reject a zero VIX contribution conditional on GARCH, while the primary GARCH increment is not statistically distinguished from zero. The forecasts are highly correlated, at 0.916090, which limits precision in allocating their shared information.

The conclusion is specification dependent. With the five-year rolling Gaussian model, the GARCH coefficient is 0.290634 with interval [0.001964, 0.579305] and p=0.04846 at the primary calendar lag. A blanket claim that GARCH never adds information would therefore discard a required sensitivity. Conversely, the relatively weak rolling-window evidence does not overturn the primary result or establish universal forecast complementarity.

## H5. Recessions and crises

There are 8,312 expansion origins and 752 recession origins. Their mean proxies are 0.011699 and 0.007477, respectively. The formal recession-minus-expansion estimate is −0.004222 (HAC SE 0.017152; 95% interval [−0.037840, 0.029395]; p=0.8055). This interval permits substantial changes in either direction. Recession medians are higher than expansion medians even though recession means are lower, illustrating the influence of rare large negative realizations.

The frozen crisis-year descriptions make this distinction concrete. Mean proxies are −0.038268 in 2008, −0.018406 in 2020, and 0.008786 in 2022; their medians are 0.005222, 0.036458, and 0.010722. These windows contain 253, 253, and 251 origins, respectively. A negative crisis-year mean alongside a positive median is consistent with unusually large forecast errors around sudden shocks. It is not a direct estimate of the compensation investors required before those shocks. The descriptive years also differ from the formal recession classification: 2022 is an independently frozen market-stress case, not an NBER recession assigned by this analysis.

# Robustness and its limits

The positive full-sample close-to-close mean survives both longer HAC bandwidths and the fixed-session horizon. Its p-values at lags 42 and 63 are $1.6043\times10^{-6}$ and $2.5703\times10^{-6}$; the 21-session mean is 0.011242, with 95% interval [0.007186, 0.015297] at HAC(20). The deterministic non-overlap mean is 0.012732 (418 origins; interval [0.007845, 0.017619]). These designs support the existence of the full-sample average without making daily origins independent or proving a constant conditional premium.

Sample dependence is more consequential. Starting in 2004 gives a mean of 0.007601 (interval [0.001162, 0.014041], p=0.02069). Starting with the weekly-option methodology sample produces the uncertain daily result reported above, while the fixed deterministic non-overlap phase rejects a zero mean. Both results must remain visible; selecting phases according to significance would change the research design. Full-sample calibration survives bandwidth changes, whereas post-2003 calibration crosses the conventional significance threshold as the HAC lag increases.

Range estimators produce substantially larger average gaps: 0.022319 for Parkinson and 0.024718 for Garman–Klass in the full primary sample. These estimators exploit intraday ranges but omit explicit overnight return increments and rely on assumptions about the price process that differ from close-to-close squared returns. Their larger gaps should therefore be read as measurement sensitivity, not as more favorable confirmations of one identical estimand. This distinction also changes the regime narrative. The full-sample recession shift is positive for Parkinson, 0.029646 (p=0.02036 at lag 21), and Garman–Klass, 0.036743 (p=0.002710), while it is negative and imprecise for close-to-close. The sign and precision of regime dependence cannot be described as invariant to variance measurement.

Forecasting robustness retains VIX's lower RMSE without establishing the primary squared-loss advantage: corrected full-sample VIX-minus-GARCH p-values are 0.2087 for Student-$t$ expanding and 0.4106 for Gaussian rolling estimation. Post-2014 Gaussian expanding inference gives p=0.2271. The fixed-21 forecast quantities are unchanged by the calendar repair. This pattern supports caution about a universal ranking while retaining evidence of option-market information in encompassing regressions.

The historical fitted models themselves warrant care. All primary Gaussian expanding fits converged, but persistence is high: median $\alpha+\beta=0.989374$, with 2,206 of 4,780 origins at or above 0.99. The Student-$t$ expanding median is 0.996593, and three historical rolling Gaussian fits reach approximately unity. The fresh refits have two boundary fits, as documented in the supplement. Convergence does not establish model adequacy or eliminate parameter uncertainty. The comparison is with the frozen GARCH benchmark, not with every possible physical variance forecast.

# Exploratory evidence beyond the core

Three post-core exercises separate a warning signal, a variance forecast and a portfolio decision. Across 3,520 historical evaluation origins in 2012–2025, subsequent variance exceeded 1.5 times implied variance at 244 origins. The historical event-frequency benchmark achieved a Brier score of 0.06528, compared with 0.06778 for the multivariate logistic model and 0.07028 for boosting. Under QLIKE the variance combination (0.38798) improved on trailing variance (0.60732), yet did not improve on VIX (0.38580). Better historical prediction against a weak comparator did not establish prospective warning value.

These policies carry different average equity exposures, so the buy-and-hold comparison is not a comparison at equal risk. The portfolio audit uses SPY shares and cash, fractional next-open rebalancing, dividends on the shares held at the ex-date and costs on traded notional. In the zero-cash, 5-basis-point scenario, trailing volatility targeting earned a 9.76% compound annual return and the combined signal 7.94%, against 14.80% for buy-and-hold. Crediting idle cash with the registered full Treasury proxy raised these strategy returns to 10.16% and 8.49%, respectively. These are returns on equity exposure and cash under fixed execution assumptions. They do not measure the payoff from selling variance.

The Nasdaq-100/VXN comparison uses the same dates on both markets. Across 4,780 common 2007–2025 origins, the Nasdaq-minus-S&P mean proxy difference was −0.000768 (historical HAC 95% interval −0.002396 to 0.000860). The original comparison implemented paired HAC for H1 and H2 but omitted the registered joint block bootstrap and the full H1–H5 Holm family. The external evidence therefore cannot establish either a cross-market difference or equivalence. The exploratory supplement gives the individual comparisons, failure diagnostics, cash-accounting bridge and coverage limits.

# Interpretation, limitations, and conclusion

Taken together, the core findings distinguish a positive historical average from a complete economic explanation. In the full sample, implied variance exceeds subsequent realized close-to-close variance, and the joint physical calibration restrictions fail. VIX nevertheless contributes information conditional on a persistent return-based model. These facts are compatible: a risk-neutral measure can be useful for prediction while carrying a component that causes biased physical forecasts. The uncertain squared-loss advantage and rolling-window encompassing sensitivity prevent a stronger claim that one source dominates across losses, periods, and model choices.

The insurance interpretation is economically plausible but is not identified by these regressions. A volatility shock can generate a large negative ex-post proxy even when ex-ante protection was priced at a positive premium. Evidence that compensation is specifically attributable to volatility or tail risk would require additional restrictions or instruments connecting prices to conditional physical expectations. Descriptive recession and crisis comparisons cannot supply that identification, particularly when estimator choice changes the regime result.

Several limitations determine the scope of the conclusion. Daily squared returns are a noisy proxy for integrated variance and do not isolate jumps. Range measures omit overnight movements. Historical VIX construction and close timing vary; the later-sample checks reduce comparability concerns without eliminating them. The interim CLOSE pathway, single archival insertion, uncorrected Yahoo baseline, and alternate-close sensitivity registrations require independent review. Recession observations are concentrated in a few episodes, and post-2014 contains only 43 recession origins, with far less independent information because outcomes overlap. The confirmatory forecasting model set is intentionally narrow, and parameter estimation uncertainty is not transformed into a proof of forecast equivalence. Finally, the empirical results concern the S&P 500/VIX pair and should not automatically be generalized to other equity indices or asset classes.

The methodological correction is also part of the scientific result. Ex-post knowledge of exchange closures can enter an apparently innocuous horizon aggregation even when no future return enters a GARCH fit. The corrected analysis preserves original outputs and uses scheduled horizons under an explicit information restriction. Its numerical effects are small and the checked conventional decisions are unchanged, but neither fact would justify retaining an information-set error.

The long-run ex-post variance gap is positive and statistically well determined under the primary full-sample design, while calibration, relative forecast performance, and regime comparisons answer distinct questions and show meaningful sensitivity. A defensible account of the volatility risk premium must retain these distinctions. The record of exact matches, fresh numerical reproductions and outstanding review decisions accompanies these estimates in Appendix C.



# Appendix A. Replication and option validation

Assume a frictionless market with a money-market account and a dividend-paying index with continuous yield $q$. Under the physical measure, $dS=(\mu-q)S\,dt+\sigma S\,dW^P$ for constant $\sigma>0$. Itô's formula gives $dV=(V_t+(\mu-q)SV_S+\tfrac12\sigma^2S^2V_{SS})dt+\sigma SV_S\,dW^P$. Write $\tau=T-t$ and let $N$ denote the standard normal cumulative distribution. Black and Scholes (1973) and Merton (1973) provide the option-pricing benchmark.

## Delta replication
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
no-dividend Black–Scholes partial differential equation used for the core
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
the put. The Black–Scholes--Merton prices are

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

## Variance swaps and the log contract

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

## Numerical option checks

The deterministic validation report reproduced in the supplementary Track A validation report compares six calls/puts with QuantLib 1.43. Maximum absolute price and IV errors are respectively \(1.862\times10^{-14}\) index-price units and \(3.065\times10^{-13}\) annualized decimal volatility. An additional independent Gaussian-payoff quadrature gives maximum price error \(5.151\times10^{-14}\) across those six cases. Log-strike integration of the continuous strip at volatilities 0.12, 0.30 and 0.60 and maturities 30/365 and one year recovers \(\sigma^2\) with maximum annualized-variance error \(1.110\times10^{-16}\) across six cases. These are numerical checks within a diffusion model, not empirical evidence that jumps or replication basis are immaterial.

The fixed market exercise uses six European AM-settled SPX contracts observed on 2022-09-15, expiring 2022-10-21, at strikes 3850, 3900 and 3950. The source-convention maturity is 35/365, rate 0.027946575342, forward 3916.093068610 and spot 3901.35. Equivalent continuous carry is −0.011388364485. It reproduces the source's parity-based Black-76 pricing through the algebraically equivalent Black–Scholes–Merton form; it is not an independent estimate of a literal negative dividend yield. Maximum absolute midpoint-IV discrepancy is \(8.604\times10^{-7}\); repricing source IV differs from midpoints by at most \(4.137\times10^{-4}\) index points, with all six values inside bid–ask spreads. Published IV rounding, par-yield approximation, AM settlement and asynchronous quotes limit interpretation. No option timestamps exist in the 2022 sample. This small exercise verifies implementation consistency only; it neither tests an entire option surface nor supplies Track B's VIX series.

# Appendix B. Statistical inference and source sensitivity

For a regression with $N$ eligible origins and $k$ coefficients, define $s_t=x_t\hat u_t$, $G_j=\sum_{t=j+1}^N s_ts_{t-j}'$ and $B=(X'X)^{-1}$. We estimate the covariance by

$$
\widehat V=\frac{N}{N-k}B\left[G_0+\sum_{j=1}^{L}\left(1-\frac{j}{L+1}\right)(G_j+G_j')\right]B.
$$

The mean test uses $x_t=1$. Pointwise intervals use a standard normal critical value. For $R\theta=r$, the quadratic form $(R\hat\theta-r)'(R\widehat VR')^{-1}(R\hat\theta-r)$ uses a chi-square reference with rank$(R)$ degrees of freedom. H2 imposes two restrictions at once. H4 reports tests of individual zero coefficients. The paired loss analysis uses the same score formula on the loss difference. Each secondary Holm family contains two comparisons at the same design setting. Conditional variance measurement error can change forecast rankings, particularly under a loss that responds strongly to a few large misses (Newey and West, 1987; Diebold and Mariano, 1995; Patton, 2011).

For daily Parkinson and Garman–Klass contributions we use $[\log(H/L)]^2/(4\log 2)$ and $\tfrac12[\log(H/L)]^2-(2\log2-1)[\log(C/O)]^2$, respectively, aggregated on the same dates as close-to-close variance. The estimators exclude overnight price changes and depend on the quality of the range (Parkinson, 1980; Garman and Klass, 1980). Omitting the overnight move changes the economic exposure being measured.

The archived alternate-close exercise preserved Yahoo as canonical and perturbed each of seven disputed closes separately and jointly. We reproduced its close-to-close results using the original signed adjustments. Each current FRED test cell reproduces that adjustment against the original Yahoo snapshot. All seven alternate prices lie within the original daily ranges, so we also computed the allowed Garman–Klass sensitivity, after the core results were known. In the joint 30-day scenario, the mean close-to-close proxy changes by $+5.84\times10^{-7}$ and the Garman–Klass proxy by $-3.59\times10^{-8}$. The largest absolute change to a single 30-day close-to-close target is 0.000240. Parkinson uses only the high and low, so the close substitutions do not enter its formula. These are measurements of sensitivity, with no changes to the baseline or its inferential sample. The supplement supplies all eight scenarios at both horizons.


# Appendix C. Reproducibility and outstanding decisions

This paper is based on the source history through commit `27735e5`. The corrected forecasting record is pinned separately at `b03686e`, and H1, H2 and formal H5 are pinned at `4f5d885`. Protocol 1.0.1 at the foundation branch limits forecast origins to 2025 and extends outcome support into 2026. The research branch subsequently restored FRED as an optional validation source and refined H3, H5 and the post-2014 sensitivity before outcomes under version 1.1.0. The original interim-freeze record still says confirmatory execution awaited review. A later dated authorization in the deviation log permitted provisional computation ahead of that review. Both texts remain part of the scientific record.

The public replication package identifies full commit IDs and SHA-256 digests, the source exceptions, per-test sample sizes and the commands that regenerate the exhibits. We recovered the historical Cboe CSV prefix, normalized Yahoo OHLC and official Cboe XLS by hash. The canonical OHLC, eligible CLOSE series and aligned origin panel matched their original digests. Two new builds yielded identical outputs in the current runtime. Their canonical daily-return and six-target files did not match the archived file digests. The all-origin audit of target construction matched its historical digest. One of the seven disputed dates, 2019-08-12, is explained by a Cboe notice of an S&P recalculation that supports the FRED close. Yahoo remains canonical, and all seven dates enter the registered sensitivity. Six dates remain unexplained. The original SPX acquisition manifest and the complete historical FRED SP500 validation response are missing. Accordingly, full replay of the original chain remains open.

An independent implementation rebuilt all six targets and the H1, H2 and H5 score covariances. The largest absolute difference across the six sets of reconstructed target values was below $8\times10^{-15}$ against the new daily records. Coefficients and standard errors agreed with the archived primary analysis to within $2\times10^{-15}$. All 72 corrected H3/H4 analysis cells were checked against the published summaries, including loss-difference identities, interval arithmetic and the 36 fixed-session controls. The 1,134 checked threshold classifications were unchanged by the historical correction. The historical fit database is absent from a public checkout. Fresh cold-start fitting completed all 14,340 origin-model combinations with zero failures. All 72 evaluation-mask hashes and counts matched the corrected record, with no 5% classification changes. The primary GARCH RMSE differed by $1.88\times10^{-10}$. These refits used the producer fitting implementation; independent NumPy calculations checked the primary loss and regression covariances. They are fresh numerical reproductions in the recorded runtime. Historical cache replay remains unavailable.

Independent coauthor review remains necessary for the provisional CLOSE pathway and archive insertion, the three exclusions, the treatment of six unexplained price discrepancies and the documented 2019 recalculation, the documented comparison of conflicting historical protocol states, and final acceptance of the conclusions. The strict VIX acquisition remains rejected. Any revised data or source policy must receive its own version and a complete replay. The Nasdaq protocol's full multiplicity family and other markets with missing approved inputs remain open. The review package separates these decisions from the software and arithmetic checks.


# Supplementary reporting

The accompanying supplement reports the complete diagnostic and robustness inventory. It includes return moments, quantiles, Jarque–Bera, Ljung–Box and ARCH-LM statistics; time-series and histogram figures; proxy quantiles and dependence; full H1/H2/H5 robustness tables; corrected H3/H4 tables for 72 analysis cells; and parameter, likelihood and residual-diagnostic summaries for fresh GARCH fits. Across 38 fixed annual anchors per model, ARCH-LM(10) rejected at an unadjusted 5% level at 2 Gaussian-expanding, 10 Student-t-expanding and 8 Gaussian-rolling anchors. Squared-residual Ljung–Box(21) rejected at 0, 0 and 2 anchors, respectively. These dependent diagnostic tests are descriptive and cover the fixed anchors. Remaining conditional heteroskedasticity qualifies model adequacy despite convergence.

# References

- Bakshi, G., and N. Kapadia. 2003. “Delta-Hedged Gains and the Negative Market Volatility Risk Premium.” *Review of Financial Studies* 16 (2): 527–566. <https://doi.org/10.1093/rfs/16.2.527>. [Author-hosted article](https://people.umass.edu/~nkapadia/docs/Bakshi_and_Kapadia_2003_RFS.pdf).

- Black, F., and M. Scholes. 1973. “The Pricing of Options and Corporate
  Liabilities.” *Journal of Political Economy* 81 (3): 637--654.
 <https://doi.org/10.1086/260062>.

- Bollerslev, T. 1986. “Generalized Autoregressive Conditional Heteroskedasticity.” *Journal of Econometrics* 31, 307–327. <https://doi.org/10.1016/0304-4076(86)90063-1>.

- Bollerslev, T., G. Tauchen, and H. Zhou. 2009. “Expected Stock Returns and Variance Risk Premia.” *Review of Financial Studies* 22 (11): 4463–4492. <https://doi.org/10.1093/rfs/hhp008>. [Author institutional record](https://scholars.duke.edu/publication/732839).

- Carr, P., and L. Wu. 2009. “Variance Risk Premiums.” *Review of Financial
  Studies* 22 (3): 1311--1341.
 <https://doi.org/10.1093/rfs/hhn038>.

- Cboe Global Indices. 2026. *Cboe Volatility Index Methodology*, version 6.0, February 26. <https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf>.

- Cboe. 2014. “Indicative (Spot) VIX Index Value to Include SPX Weeklys Beginning October 6, 2014.” Information Circular IC14-075, September 22. <https://res-certification.cboe.com/resources/regulation/circulars/general/IC-CBOE-2014-075.pdf>.

- Cboe. “Historical Data for Cboe VIX Index and Other Volatility Indices.” <https://www.cboe.com/tradable_products/vix/vix_historical_data>.

- Demeterfi, K., E. Derman, M. Kamal, and J. Zou. 1999. “More Than You Ever Wanted to Know About Volatility Swaps.” Goldman Sachs Quantitative Strategies Research Notes, March. [Author-hosted research note and download](https://emanuelderman.com/more-than-you-ever-wanted-to-know-about-volatility-swaps-the-journal-of-der/).

- Diebold, F. X., and R. S. Mariano. 1995. “Comparing Predictive Accuracy.” *Journal of Business & Economic Statistics* 13, 253–263. <https://doi.org/10.1080/07350015.1995.10524599>.

- Garman, M. B., and M. J. Klass. 1980. “On the Estimation of Security Price Volatilities from Historical Data.” *Journal of Business* 53, 67–78. <https://doi.org/10.1086/296072>.

- Gârleanu, N., L. H. Pedersen, and A. M. Poteshman. 2009. “Demand-Based Option Pricing.” *Review of Financial Studies* 22 (10): 4259–4299. <https://doi.org/10.1093/rfs/hhp005>.

- Harrison, J. M., and S. R. Pliska. 1981. “Martingales and Stochastic
  Integrals in the Theory of Continuous Trading.” *Stochastic Processes and
  Their Applications* 11 (3): 215--260.
 <https://doi.org/10.1016/0304-4149(81)90026-0>.

- HistoricalData.net. “Historical US Options Data — End-of-Day Chains.” <https://historicaldata.net/options.html>. Provider documentation and fixed sample provenance, rather than a source of the theoretical derivations.

- Merton, R. C. 1973. “Theory of Rational Option Pricing.” *Bell Journal of
  Economics and Management Science* 4 (1): 141--183.
 <https://doi.org/10.2307/3003143>.

- National Bureau of Economic Research. “U.S. Business Cycle Expansions and Contractions.” <https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions>.

- Newey, W. K., and K. D. West. 1987. “A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix.” *Econometrica* 55, 703–708. <https://doi.org/10.2307/1913610>.

- Parkinson, M. 1980. “The Extreme Value Method for Estimating the Variance of the Rate of Return.” *Journal of Business* 53, 61–65. <https://doi.org/10.1086/296071>.

- Patton, A. J. 2011. “Volatility Forecast Comparison Using Imperfect Volatility Proxies.” *Journal of Econometrics* 160, 246–256. <https://doi.org/10.1016/j.jeconom.2010.03.034>.

- Cboe. 2019. “Corrected Closing Settlement Prices for Certain S&P Indices II.” Notice C2019081302, August 13. <https://cdn.cboe.com/resources/release_notes/2019/Corrected-Closing-Settlement-Prices-for-Certain-SP-Indices-II.pdf>.
