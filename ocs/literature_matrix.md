# Literature matrix

**Tracker task:** W1-07  
**Status:** matrix complete for W1-07; coauthor review pending. Literature results below are not findings of this project.

**Coverage rule:** purposive foundational reading across four pre-specified strands—Black–Scholes, ARCH/GARCH, implied versus realized volatility, and the variance risk premium—plus the authoritative VIX methodology. This is not a systematic review or a claim that the selected sources are exhaustive.

**Coverage check:** 13 sources: 2 Black–Scholes foundations, 2 ARCH/GARCH foundations, 5 IV/RV or realized-variance measurement sources, 3 variance-risk-premium papers, and 1 authoritative VIX methodology. Links and source metadata were checked on 2026-09-11.

| Source | Question / contribution | Method | Data | Main result | Limitation for this project | Relevance to this project |
|---|---|---|---|---|---|---|
| [Black & Scholes (1973)](https://doi.org/10.1086/260062) | Derive an option valuation relation from no-arbitrage and replication. | Continuous-time stock model and delta-hedged replicating portfolio. | Theoretical. | Foundational European option-pricing relation. | Constant volatility, continuous paths/trading, idealized markets; not a VIX construction. | Track A derivation and disciplined contrast with Track B. |
| [Merton (1973)](https://doi.org/10.2307/3003143) | Develop a general theory of rational option pricing and extend the Black–Scholes framework. | Continuous-time arbitrage arguments and dynamic replication for contingent claims. | Theoretical. | Establishes broader option-pricing restrictions and extensions, including treatment of payouts. | Relies on idealized continuous trading and diffusion-based assumptions; still does not make a single-option implied volatility equivalent to VIX. | Supports Track A boundary conditions and the explicit treatment of dividends and rates in real-option validation. |
| [Engle (1982)](https://doi.org/10.2307/1912773) | Model time-varying conditional variance. | ARCH, likelihood estimation, diagnostics. | U.K. inflation. | Establishes conditional heteroskedasticity as an estimable dynamic process. | Original application is not equity returns; ARCH can be restrictive/high-order. | Foundation for volatility clustering and conditional-variance modelling. |
| [Bollerslev (1986)](https://doi.org/10.1016/0304-4076(86)90063-1) | Generalize ARCH parsimoniously by including lagged conditional variance. | GARCH class, stationarity/moment results, maximum likelihood. | Inflation example. | GARCH captures persistence with fewer parameters. | Basic GARCH(1,1) is symmetric and deliberately not state of the art. | Defines the benchmark statistical volatility model. |
| [Canina & Figlewski (1993)](https://doi.org/10.1093/rfs/6.3.659) | Test whether option-implied volatility forecasts subsequent realized volatility and subsumes recent observed volatility. | Forecast regressions and subsample comparisons by option maturity and strike. | S&P 100 index options and subsequent index volatility. | Reports little correlation with future volatility and little incremental information in its design. | Uses the old OEX market, single-option Black–Scholes IV, overlapping observations, and a short sample; it is not evidence about modern model-free VIX by itself. | Provides the skeptical benchmark that later sampling and measurement studies reassess; motivates alignment and overlap-aware inference. |
| [Christensen & Prabhala (1998)](https://doi.org/10.1016/S0304-405X(98)00034-8) | Reassess whether implied volatility contains incremental information for future realized volatility. | Monthly non-overlapping sampling; calibration/encompassing regressions; IV and OOS robustness. | S&P 100 options and realized volatility, 1983–1995. | Finds implied volatility contains substantial information; overlap and sample design help explain differences from earlier studies. | Different underlying, era, and single-option Black–Scholes IV rather than VIX. | Motivates strict forward alignment, deterministic non-overlap robustness, calibration/encompassing tests, and genuine OOS comparison. |
| [Poon & Granger (2003)](https://doi.org/10.1257/002205103765762743) | Review volatility measurement and forecasting evidence. | Survey of historical, conditional, and implied-volatility methods and forecast evaluation. | 93 studies across assets/markets. | Forecast rankings depend on measurement, horizon, loss function, and design. | Heterogeneous review cannot determine one universally optimal estimator. | Motivates common targets/masks, explicit loss functions, OOS evaluation, and robustness rather than result-driven model choice. |
| [Andersen, Bollerslev, Diebold & Labys (2003)](https://doi.org/10.1111/1468-0262.00418) | Link high-frequency returns to realized-volatility measurement, modelling, and forecasting. | Quadratic-variation theory plus long-memory vector autoregressions for log realized volatility and density forecasts. | Intraday Deutschemark/U.S. dollar and yen/U.S. dollar spot exchange rates. | Finds that high-frequency realized-volatility measures support accurate volatility and return-density forecasts in the studied FX data. | Intraday FX evidence is not directly transferable to daily-close S&P 500 targets; this project lacks an intraday core measure. | Clarifies that realized variance is a measured proxy and that measurement frequency can matter; supports cautious interpretation of close-to-close targets. |
| [Jiang & Tian (2005)](https://doi.org/10.1093/rfs/hhi027) | Extend and implement model-free implied volatility with jumps, then compare its information content with Black–Scholes IV and past realized volatility. | Option-strip integration with truncation/discretization analysis and forecast-encompassing tests. | S&P 500 index options and underlying returns. | Their model-free measure subsumes the information in Black–Scholes IV and past realized volatility in the studied sample. | A research implementation using option panels is not identical to the official historical VIX series, and the sample and market microstructure differ from this project. | Reinforces the locked separation of model-free VIX from single-option Black–Scholes IV and motivates forecast encompassing. |
| [Bakshi & Kapadia (2003)](https://doi.org/10.1093/rfs/hhg002) | Test for a market volatility risk premium using delta-hedged option returns. | Derives the link between volatility-risk pricing and delta-hedged gains under stochastic volatility; tests option portfolios. | S&P 500 index options and index returns. | Delta-hedged option portfolios underperform zero on average, consistent with a negative market price/premium for volatility risk under the paper's convention. | Option-return identification differs from an implied-minus-realized ex-post variance gap and is sensitive to jumps, hedging error, and transaction costs. | Provides risk-compensation evidence while requiring an explicit sign translation: its negative volatility-risk-premium convention is compatible with a positive `IVAR - RVAR` premium paid by variance buyers. |
| [Carr & Wu (2009)](https://doi.org/10.1093/rfs/hhn038) | Quantify variance risk premiums using option-implied and realized variance. | Model-free variance-swap replication compared with realized variance. | Five stock indices and 35 individual stocks. | Under their realized-minus-swap-rate convention, average variance premia are strongly negative for the S&P 500, S&P 100, and Dow indexes and generally smaller for individual stocks. | Their sign convention is the reverse of this project's empirical proxy, and neither ex-post measure directly observes the theoretical conditional premium. | Supports variance-space primary terminology and variance-replication intuition; requires translating their negative premium into this project's positive `IVAR - RVAR` convention. |
| [Bollerslev, Tauchen & Zhou (2009)](https://doi.org/10.1093/rfs/hhp008) | Ask whether variance risk premia predict aggregate stock returns. | Equilibrium motivation plus predictive regressions using implied/realized variation. | U.S. aggregate market data. | Reports return predictability at intermediate horizons. | Return prediction is outside the confirmatory core and inference is specification-sensitive. | Economic interpretation only; possible extension after the core scope gate. |
| [Cboe VIX Methodology](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf) | Define the operational VIX index. | Weighted SPX option strip, near/next-term variance calculations, constant 30-day interpolation. | Live SPX option quotes and rate inputs. | VIX is a constant 30-calendar-day model-free volatility index, not one Black–Scholes IV. | Methodology/contract rules can evolve; VIX is not a physical-measure unbiased forecast by definition. | Authoritative Track B definition and the reason the primary realized target is exact 30 calendar days. |

## Synthesis for the present design

The literature motivates testing for a positive average implied-minus-realized variance gap and suggests that option-implied measures can contain useful forward-looking information. The conflicting findings of Canina and Figlewski (1993) and Christensen and Prabhala (1998) also show why horizon alignment, overlap, estimator choice, and sample design must be explicit. None of these sources determines this project's result.

Terminology is not uniform across the literature. Carr and Wu (2009) define their empirical variance premium as realized variance minus the synthetic variance-swap rate, while this project is locked to implied variance minus realized variance. Bakshi and Kapadia's (2003) negative price of volatility risk is likewise viewed from the payoff/risk-price side. All quantities imported into this project must therefore be translated to the locked `VRP_X = IVAR - RVAR` sign convention before comparison.

The final pre-analysis hierarchy is:

1. **Primary horizon:** exact forward 30 calendar days, because the economic maturity of VIX is constant calendar time.
2. **Mandatory horizon robustness:** exactly the next 21 trading days, the conventional one-trading-month approximation.
3. **Primary object:** variance-space `VRP_X = IVAR - RVAR`.
4. **Secondary communication object:** volatility-space `VOLGAP = IVOL - RVOL`.
5. **Inference:** overlap-aware HAC plus deterministic non-overlapping robustness.
6. **Forecasting:** VIX, GARCH, and naive forecasts compared genuinely out of sample on the same target and common mask.

Forecast superiority, if observed, supports relative information content against the stated benchmark. It does not by itself prove the Efficient Markets Hypothesis.

## Targeted reading record used for protocol lock

### Christensen & Prabhala (1998)

Targeted sections covered their research-design contrast, non-overlap logic, calibration and encompassing regressions, OOS robustness, and inferential consequences of overlap.

**Protocol implication:** retain a full rolling panel for information efficiency but use robust covariance and a deterministic non-overlapping sample; jointly test calibration restrictions; never reuse future observations in model estimation.

**Boundary:** their single-option OEX implied volatility and option-life realized measure are not copied mechanically into the VIX design.

### Poon & Granger (2003)

Targeted sections covered volatility/variance definitions, realized-volatility measurement, forecast-loss measures, calibration/encompassing regressions, noisy realized targets, and OOS evaluation.

**Protocol implication:** pre-specify the target and loss functions, compare forecasts on one common mask, distinguish in-sample from recursive OOS estimation, and account for serial correlation in overlapping forecast losses.

**Boundary:** the review documents heterogeneous practices rather than one universally optimal horizon or estimator. It motivates transparent pre-specification and robustness.

## Horizon decision note

An August 23 draft briefly made 21 trading days primary for simplicity and alignment with the original project tracker. The August 26 methodological review restored the exact 30-calendar-day horizon as primary after re-examining the Cboe definition of VIX. This occurred before empirical VRP or forecast-ranking results were generated. The 21-trading-day design remains mandatory robustness, so both economically natural constructions are reported.
