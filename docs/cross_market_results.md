# Cross-market results and economic attribution

**EXPLORATORY — PROVISIONAL / PENDING INDEPENDENT REVIEW.** All variance numbers are annualized decimal variance. The synchronized market comparisons are paired by origin; the H8 section uses the fixed 5 bp cost scenario unless stated otherwise.

## H1–H2: risk premium and calibration

| Period / horizon | N | Nasdaq VRP mean (HAC p) | S&P VRP mean (HAC p) | Nasdaq − S&P (95% CI; p) |
| --- | ---: | ---: | ---: | --- |
| 2007–2025, 30c | 4,780 | 0.006704 (0.0780) | 0.007472 (0.0494) | -0.000768 [-0.002396, 0.000860]; 0.355 |
| 2007–2025, 21t | 4,780 | 0.006580 (0.0835) | 0.007380 (0.0512) | -0.000800 [-0.002411, 0.000811]; 0.331 |
| Post-2014, 30c | 2,827 | 0.004668 (0.3316) | 0.006668 (0.1556) | -0.002001 [-0.004163, 0.000161]; 0.0697 |
| Post-2014, 21t | 2,827 | 0.004530 (0.3514) | 0.006550 (0.1688) | -0.002020 [-0.004152, 0.000111]; 0.0632 |

For the longer Nasdaq-only available sample (2001–2025; 6,241 origins), 30c VRP mean is 0.008587 (HAC lag-21 p=0.00830; 75.95% positive). That full-history result does not persist as a conventionally significant common-period or post-2014 result. In the paired H2 interaction model, full common-period slope differences are small (30c Nasdaq-minus-S&P beta -0.0131, p=0.714; 21t -0.0146, p=0.687). Post-2014 differences are +0.0610 (p=0.218) and +0.0618 (p=0.204). Market-specific joint alpha=0, beta=1 tests are not rejected in the paired 2007–2025 or post-2014 samples; these null results do not establish calibration equivalence.

## H3–H4: recursive forecasting

Every variant produced 4,780/4,780 converged recursive fits. Each saved daily variance path passed the analytic GARCH recurrence, positive-variance, training chronology, horizon, annualization, and common-mask checks. Normal-expanding was already fully cached; only Student-t expanding and normal five-year rolling were executed in the D: research checkout. No GARCH models were refit for H6–H8.

| Period / horizon | Implied RMSE | Normal expanding RMSE | Student-t expanding RMSE | Normal 5y rolling RMSE | Trailing RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full, 30c | 0.06862 | 0.07328 | 0.07712 | 0.07232 | 0.08523 |
| Post-2014, 30c | 0.06812 | 0.07776 | 0.08234 | 0.07340 | 0.09076 |
| Full, 21t | 0.06831 | 0.07370 | 0.07765 | 0.07268 | 0.08364 |
| Full nonoverlap, 30c (N=221) | 0.07264 | 0.07596 | 0.08108 | 0.07444 | 0.08368 |

On primary 30c squared loss, VXN minus trailing is -0.002555 (HAC lag-21 p=0.0745; two-comparison Holm p=0.0909). Normal-expanding GARCH minus trailing is -0.001894 (p=0.0454; Holm p=0.0909); the Student-t and rolling adjusted tests also exceed 0.05. Implied minus normal-expanding GARCH squared loss is -0.000661 (p=0.249); QLIKE difference is -0.01515 (p=0.184). At 21t, the implied-minus-trailing mean squared-loss differential is -0.002330 (p=0.0780); no robustness test creates a multiplicity-adjusted winner.

Full 30c normal-expanding H4 coefficients are alpha 0.00132, beta(VXN) 0.6688, gamma(GARCH) 0.2051; gamma p=0.189. For Student-t, gamma=0.0859 (p=0.460); for normal rolling, gamma=0.1664 (p=0.149). Post-2014 gamma estimates are -0.0670, -0.1038, and 0.0348 (p=0.586, 0.392, and 0.744). H4 therefore provides no evidence of robust incremental GARCH information beyond VXN.

## H5–H7: regime, event, and model combination

| Test | Estimate | Dependence-aware uncertainty | Interpretation |
| --- | --- | --- | --- |
| H5 full-sample NDX recession minus expansion VRP, 30c | +0.01189 | 95% CI [-0.03214, +0.05593], p=0.597; N=6,241, including 586 recession origins | No detected average regime shift; imprecise |
| H5 post-2014 recession coefficient, 21t | -0.05127 | 95% CI [-0.26382, +0.16127], p=0.636 | No stable recent regime effect |
| H6 event-model D vs baseline A Brier relative reduction | -3.47% | 63-session block bootstrap 95% CI [-6.44%, -1.24%] | D is worse on Brier; historical event prediction weak |
| H7 combined minus VXN QLIKE | +0.02091 | HAC lag-21 p=0.182; 63-session bootstrap relative reduction -7.78%, 95% CI [-17.32%, +3.17%] | No reliable combination gain |

H6 has 3,520 origins, 310 events, and event prevalence 8.81%. ROC AUCs are 0.381 (A), 0.318 (B), 0.463 (C), and 0.399 (D); average precision ranges 0.059–0.080. This is not prospective warning evidence. In H7, standalone VXN has RMSE/MAE/QLIKE 0.06139/0.02631/0.26899; combined has 0.06416/0.02569/0.28990. The combined model slightly lowers MAE but has worse RMSE and QLIKE than VXN.

## H8: QQQ fixed-rule replay, zero cash versus DGS1MO

Cash income is booked on the prior actual cash balance using an initial-release-known rate locked before each interval, the actual elapsed calendar days, and ACT/365. The 5 bp cost case is shown; all five fixed strategies and all five cost settings were run. “Annual income / initial NAV” is cumulative interest dollars divided by initial NAV and study years; “annual normalized cash income” instead scales each credit by prior NAV. CAGR increment is the difference between the self-financing interest-bearing and zero-interest paths. All are different quantities.

| Rule | Calendar-weighted cash | Zero CAGR | DGS1MO CAGR | CAGR increment | Cash income / initial NAV | Annual income / initial NAV | Annual normalized cash income | Zero → DGS1MO common-rate Sharpe | DGS1MO max drawdown | Realized vol | |vol−10%| | Turnover / year | Fees / initial NAV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Buy-and-hold | 0.00% | 19.654% | 19.654% | 0.000 pp | 0.000 | 0.000 | 0.000 | 0.903 → 0.903 | -35.12% | 20.50% | 10.50 pp | 0.080 | 0.0007 |
| Trailing volatility | 36.06% | 11.288% | 12.008% | +0.720 pp | 0.3091 | 2.209% | 0.645% | 0.915 → 0.976 | -14.63% | 10.61% | 0.61 pp | 5.261 | 0.0868 |
| VXN | 47.88% | 8.932% | 9.800% | +0.867 pp | 0.3038 | 2.170% | 0.793% | 0.865 → 0.958 | -14.49% | 8.52% | 1.48 pp | 5.571 | 0.0750 |
| GARCH | 46.05% | 9.544% | 10.380% | +0.837 pp | 0.3069 | 2.193% | 0.761% | 0.882 → 0.967 | -14.26% | 9.04% | 0.96 pp | 5.872 | 0.0859 |
| Combined | 45.69% | 9.411% | 10.228% | +0.817 pp | 0.2977 | 2.127% | 0.744% | 0.870 → 0.952 | -15.26% | 9.03% | 0.97 pp | 4.628 | 0.0659 |

Cash-income amounts and fee amounts are multiples of initial NAV. The paired 63-session bootstrap 95% CIs for DGS1MO-minus-zero CAGR are [0.47, 1.01] pp (trailing), [0.58, 1.19] pp (VXN), [0.56, 1.14] pp (GARCH), and [0.55, 1.12] pp (combined). The DGS1MO half-rate scenario roughly halves the cash contribution; the DTB4WK full-rate scenario is close to DGS1MO full-rate, with the same CAGR rank. At 5 bp, DGS1MO full-rate does not change the CAGR ordering among the four volatility rules. The common-DGS1MO Sharpe ordering changes only in the close VXN/combined comparison; their paired 63-session interval overlaps zero. The same broad cash-yield sensitivity in the frozen SPY study also preserves CAGR ordering and does not separate Sharpe rankings statistically. This sensitivity changes absolute wealth estimates for cash-heavy allocations, especially the VXN rule, but does not demonstrate strategy superiority or a broker cash yield.

The original scenario ledgers separately record dividends on old shares, cash interest, share counts, cash balances, trade notional, fees, and NAV. [`audit_cross_market_ndx_h8_components.py`](../scripts/audit_cross_market_ndx_h8_components.py) joins the frozen QQQ opens/closes and exports 20 daily component ledgers for the four rate scenarios × five strategies at the primary 5 bp cost. Each row separates prior-share overnight equity P&L, dividend cash, post-trade intraday equity P&L, cash interest, trade notional, and fee; it checks their self-financing return identity. The maximum daily residual is 6.06e-16. The aggregate incremental log-growth attribution separately groups direct interest, changed equity/dividend P&L, and changed fees, with maximum residual below 2e-14. All 100 scenario/cost ledgers pass the independent Decimal/accrual and share/cash/fee audit (maximum absolute error 3.55e-15); all 25 zero-interest ledgers exactly reproduce the original QQQ zero-rate reference values. Per-file hashes are in `data/manifests/h8_ledger_component_attribution_v1.json`.

## Data, implementation, and output hashes

The frozen data manifest is `data/manifests/cross_market_sources_v1.json` (SHA-256 `7a78261c22d5d9af773a6a3f3b8be3c0cdda15fe08e8e6c81fa5a684f0cae379`). The VXN/RVX extension is `data/manifests/cross_market_volatility_v2.json` (SHA-256 `5baf82276ce3dd2583b08731f08702af26beceb00144e32f85d1fd4bba7ce47c`); the Task 3 initial-release cash-rate manifest is `data/manifests/h8_cash_rate_source_v1.json` (SHA-256 recorded in `cross_market_execution_v1.json`). FRED current-vintage VXN matches official Cboe history exactly over 4,299 overlapping dates; RVX matches over 4,290 dates. The FRED Nasdaq close source has one missing XNYS session (2002-01-29) and three non-session values; those values were quarantined, no returns were bridged, and no H3 OOS target depends on the gap.

The full machine results remain in local ignored output storage; exact hashes are recorded in `data/manifests/cross_market_execution_v1.json`. Key result files are `ndx_vxn_h1_h2_v2.json`, `ndx_vxn_h3_h4_v2.json`, `ndx_vxn_h5_v1.json`, `ndx_vxn_h6_v1.json`, `ndx_vxn_h7_v1.json`, `ndx_spx_paired_inference_v3.json`, and `h8_cash_yield_v1/ndx_qqq_h8_v1.json` under `outputs/cross_market/v1/`.
