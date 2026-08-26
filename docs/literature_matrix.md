# Literature matrix

**Tracker task:** W1-07  
**Status:** targeted protocol reading complete; coauthor review pending. Literature results below are not findings of this project.

| Source | Question / contribution | Method | Data | Main result | Limitation for this project | How we use it |
|---|---|---|---|---|---|---|
| [Black & Scholes (1973)](https://doi.org/10.1086/260062) | Derive an option valuation relation from no-arbitrage and replication. | Continuous-time stock model and delta-hedged replicating portfolio. | Theoretical. | Foundational European option-pricing relation. | Constant volatility, continuous paths/trading, idealized markets; not a VIX construction. | Track A derivation and disciplined contrast with Track B. |
| [Engle (1982)](https://doi.org/10.2307/1912773) | Model time-varying conditional variance. | ARCH, likelihood estimation, diagnostics. | U.K. inflation. | Establishes conditional heteroskedasticity as an estimable dynamic process. | Original application is not equity returns; ARCH can be restrictive/high-order. | Foundation for volatility clustering and conditional-variance modelling. |
| [Bollerslev (1986)](https://doi.org/10.1016/0304-4076(86)90063-1) | Generalize ARCH parsimoniously by including lagged conditional variance. | GARCH class, stationarity/moment results, maximum likelihood. | Inflation example. | GARCH captures persistence with fewer parameters. | Basic GARCH(1,1) is symmetric and deliberately not state of the art. | Defines the benchmark statistical volatility model. |
| [Christensen & Prabhala (1998)](https://doi.org/10.1016/S0304-405X(98)00034-8) | Reassess whether implied volatility contains incremental information for future realized volatility. | Monthly non-overlapping sampling; calibration/encompassing regressions; IV and OOS robustness. | S&P 100 options and realized volatility, 1983–1995. | Finds implied volatility contains substantial information; overlap and sample design help explain differences from earlier studies. | Different underlying, era, and single-option Black–Scholes IV rather than VIX. | Motivates strict forward alignment, deterministic non-overlap robustness, calibration/encompassing tests, and genuine OOS comparison. |
| [Poon & Granger (2003)](https://doi.org/10.1257/002205103765762743) | Review volatility measurement and forecasting evidence. | Survey of historical, conditional, and implied-volatility methods and forecast evaluation. | 93 studies across assets/markets. | Forecast rankings depend on measurement, horizon, loss function, and design. | Heterogeneous review cannot determine one universally optimal estimator. | Motivates common targets/masks, explicit loss functions, OOS evaluation, and robustness rather than result-driven model choice. |
| [Carr & Wu (2009)](https://doi.org/10.1093/rfs/hhn038) | Quantify variance risk premiums using option-implied and realized variance. | Model-free variance-swap replication compared with realized variance. | Five stock indices and 35 individual stocks. | Documents economically important variance-risk-premium behaviour. | The theoretical conditional premium is not identical to this project's ex-post proxy. | Supports variance-space primary terminology, variance-replication intuition, and careful sign/unit mapping. |
| [Bollerslev, Tauchen & Zhou (2009)](https://doi.org/10.1093/rfs/hhp008) | Ask whether variance risk premia predict aggregate stock returns. | Equilibrium motivation plus predictive regressions using implied/realized variation. | U.S. aggregate market data. | Reports return predictability at intermediate horizons. | Return prediction is outside the confirmatory core and inference is specification-sensitive. | Economic interpretation only; possible extension after the core scope gate. |
| [Cboe VIX Methodology](https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf) | Define the operational VIX index. | Weighted SPX option strip, near/next-term variance calculations, constant 30-day interpolation. | Live SPX option quotes and rate inputs. | VIX is a constant 30-calendar-day model-free volatility index, not one Black–Scholes IV. | Methodology/contract rules can evolve; VIX is not a physical-measure unbiased forecast by definition. | Authoritative Track B definition and the reason the primary realized target is exact 30 calendar days. |

## Synthesis for the present design

The literature motivates a positive average implied-minus-realized variance gap and suggests that option-implied measures can contain useful forward-looking information. It does not determine this project's result.

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
