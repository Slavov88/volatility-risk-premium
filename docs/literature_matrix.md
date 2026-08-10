# Literature matrix

**Tracker task:** W1-07
**Status:** Targeted protocol reading complete; in review by Person A. Results
below summarize prior work and are not findings of this project.

| Source | Question / contribution | Method | Data | Main result | Limitation for this project | How we use it |
|---|---|---|---|---|---|---|
| [Black & Scholes (1973)](https://doi.org/10.1086/260062) | Derive an option valuation relation from no-arbitrage and replication. | Continuous-time stock model and delta-hedged replicating portfolio. | Theoretical analysis rather than a large empirical forecasting sample. | Produces the foundational pricing formula. | Constant volatility, continuous paths/trading, and idealized market assumptions; not a VIX construction. | Track A derivation and a disciplined contrast with Track B. |
| [Engle (1982)](https://doi.org/10.2307/1912773) | Model time-varying conditional variance. | ARCH specification, likelihood-based estimation, and diagnostic testing. | U.K. inflation. | Establishes conditional heteroskedasticity as an estimable dynamic process. | Original application is not equity returns; symmetric ARCH can be too restrictive and high-order. | Foundation for volatility clustering and later GARCH diagnostics. |
| [Bollerslev (1986)](https://doi.org/10.1016/0304-4076(86)90063-1) | Generalize ARCH parsimoniously by including lagged conditional variance. | GARCH class, stationarity/moment results, maximum likelihood. | Inflation example. | GARCH captures persistence with fewer parameters than high-order ARCH. | Basic GARCH(1,1) is symmetric, distribution-sensitive, and deliberately not state of the art. | Defines the benchmark statistical volatility model. |
| [Christensen & Prabhala (1998)](https://doi.org/10.1016/S0304-405X(98)00034-8) | Reassess whether implied volatility contains incremental information for future realized volatility. | Monthly non-overlapping sampling; calibration and encompassing regressions; instrumental-variables and OOS robustness. | 139 S&P 100 option/realized-volatility observations, Nov. 1983-May 1995. | The paper attributes materially different conclusions from earlier work partly to longer history and avoidance of severe overlap. | Different underlying, era, and single-option Black-Scholes IV; its conclusions are not predictions for VIX. | Motivates common-period construction, a predetermined non-overlap check, joint calibration restrictions, and OOS MSE. |
| [Poon & Granger (2003)](https://doi.org/10.1257/002205103765762743) | Synthesize volatility definitions and forecast evaluation across 93 studies. | Review of historical and option-implied approaches, loss metrics, regression tests, and realized-target measurement. | Multiple assets, regions, frequencies, and forecast definitions. | Measurement noise, horizon, data frequency, loss choice, overlap, and in-sample estimation can alter apparent rankings. | A heterogeneous survey cannot substitute for a controlled common-target comparison. | Supports a variance target, MSE as primary loss, RMSE reporting, explicit OOS estimation, overlap-aware uncertainty, and transparent target measurement. |
| [Carr & Wu (2009)](https://doi.org/10.1093/rfs/hhn038) | Quantify variance risk premiums directly from option portfolios and realized variance. | Model-free synthetic variance-swap rate from option prices, compared with realized variance. | Options on five stock indices and 35 individual stocks. | Documents economically large variance-risk-premium behavior across assets. | Published variance and sign conventions require explicit mapping to this project's (IVAR-RVAR) definition. | Terminology, variance-replication intuition, and a required sign/units cross-check. |
| [Bollerslev, Tauchen & Zhou (2009)](https://doi.org/10.1093/rfs/hhp008) | Ask whether model-free variance risk premia predict aggregate stock returns. | Equilibrium motivation plus predictive regressions using implied and high-frequency realized variation. | Post-1990 U.S. aggregate market data. | Reports strongest predictability at an intermediate quarterly horizon. | Return prediction is an optional extension; inference and specification sensitivity prevent treating this as a core expected result. | Economic interpretation and, only after the scope gate, a possible extension. |
| [Cboe VIX Methodology](https://cdn.cboe.com/resources/indices/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf) | Define the operational VIX index. | Weighted OTM SPX/SPXW option strip, near/next-term variance calculations, 30-day interpolation. | Live option quotes and U.S. Treasury yield-curve inputs. | VIX is a 30-day model-free volatility index, not one Black-Scholes IV. | Methodology and contract rules can change; VIX is not a physical-measure unbiased forecast by definition. | Authoritative Track B definition and ingestion/units specification. |

## Synthesis for the present design

The literature motivates a positive average gap and potentially useful implied-
volatility forecasts, but it does not determine this project's result. The core
replication must keep future alignment, overlapping-window inference, common
targets, and volatility-versus-variance units explicit. Forecast superiority, if
observed, would support information aggregation relative to stated benchmarks;
it would not by itself prove the Efficient Market Hypothesis.

## Targeted reading record for protocol lock

This is a targeted review, not a claim that either paper was read cover to
cover.

### Christensen & Prabhala (1998)

- **Pages read:** journal pp. 126-129 (research-design contrast, monthly
  non-overlap, option/realized-volatility construction); pp. 133-135
  (calibration and encompassing regressions); pp. 139-140 (estimator and OOS
  robustness); pp. 143-147 (mechanics and inferential consequences of overlap,
  conclusion).
- **Protocol implication:** retain the full overlapping daily panel for power
  with robust covariance, but add one deterministic non-overlapping sample.
  Test \(\alpha=0,\beta=1\) jointly as calibration, not as a theorem. Keep OOS
  comparison on forecast errors and never reuse future observations in model
  estimation.
- **Boundary:** their implied volatility comes from one near-ATM OEX option and
  their realized measure is volatility over the option life; neither definition
  is copied mechanically into the present VIX/variance design.

### Poon & Granger (2003)

- **Pages read:** journal pp. 479-482 (volatility/variance definitions,
  measurement, realized volatility, frequency and microstructure); pp. 490-492
  (loss measures, equal-accuracy inference, calibration/encompassing
  regressions, noisy actual-volatility proxies, and OOS evaluation).
- **Protocol implication:** compare forecasts against one well-defined variance
  target; keep MSE primary and RMSE interpretable; treat MAE as descriptive;
  distinguish in-sample from genuine recursive OOS forecasts; account for
  serial correlation in overlapping forecast errors. QLIKE is retained only as
  a clean positive-variance robustness loss.
- **Boundary:** the survey documents heterogeneous practices rather than one
  universally optimal estimator or loss, so it motivates pre-specification and
  robustness rather than a result-dependent choice.
