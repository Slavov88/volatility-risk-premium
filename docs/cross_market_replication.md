# Cross-market replication: Nasdaq-100/VXN

**Status: EXPLORATORY EXTERNAL REPLICATION — PROVISIONAL, PENDING INDEPENDENT REVIEW.**

This extension adds the Nasdaq-100/VXN market to the frozen S&P 500/VIX research. It does not replace or revise the original S&P results. The primary cross-market conclusion is limited to these two U.S. equity markets; Russell 2000 and EURO STOXX 50 remain blocked pending data that can be independently verified in this environment.

## Scientific result

The 2007–2025 paired panel contains 4,780 identical origin dates. Both markets have positive point estimates of 30-calendar-day variance risk premium (Nasdaq 0.006704; S&P 0.007472), but the HAC mean tests are borderline (p=0.0780 and p=0.0494). The paired Nasdaq-minus-S&P difference is -0.000768 (95% CI [-0.002396, 0.000860], p=0.355). For 21 trading sessions, the paired difference is -0.000800 (95% CI [-0.002411, 0.000811], p=0.331). Post-2014, neither market's mean differs from zero at conventional levels and paired differences remain uncertain. The evidence is consistent with similar positive long-run means, but does not establish stable positive VRP across markets or across recent periods.

Nasdaq H3 forecast evaluation uses the same 4,780 origins for all three GARCH specifications. At 30 calendar days, VXN has RMSE 0.06862 versus 0.07328 (normal expanding), 0.07232 (normal five-year rolling), and 0.07712 (Student-t expanding); the trailing benchmark RMSE is 0.08523. The VXN advantage over trailing and the normal-expanding GARCH advantage over trailing do not survive the registered two-comparison Holm adjustment (adjusted p=0.0909 for each at lag 21). VXN-versus-GARCH squared-loss p=0.249 and QLIKE p=0.184. The 21-session results are directionally similar and also do not yield a Holm-significant incremental forecast winner. In the 30-calendar-day H4 encompassing regressions, the VXN coefficients are positive, but the GARCH coefficient is not significant in any variant (full-sample p=0.189–0.460); post-2014 GARCH coefficients are also not significant. The extension therefore does not establish incremental GARCH information beyond VXN.

The frozen NBER H5 chronology gives a full-sample 30-calendar-day recession VRP difference of 0.01189 (95% CI [-0.03214, 0.05593], p=0.597; 586 recession origins). The post-2014 21-session estimate is -0.05127 (95% CI [-0.26382, 0.16127], p=0.636). Selected crisis-year means are negative in 2008, 2020, and 2022. These descriptive windows and the H5 regression do not establish a stable regime effect.

H6 event forecasts cover 3,520 2012–2025 origins and 310 events. The four event-model ROC AUCs range from 0.318 to 0.463; the best is still below 0.5, and average precision (0.080 for model C) is below event prevalence (0.088). Model D has a 3.47% higher Brier score than baseline A (63-session block-bootstrap relative reduction -0.0347; 95% CI [-0.0644, -0.0124]). A fixed retrospective alert-budget comparison does not rescue broad event-prediction utility. These are exploratory historical diagnostics, not prospective warning-system evidence.

H7 gives VXN the best primary QLIKE among the evaluated standalone/combined Nasdaq forecasts (0.2690); combined is 0.2899, GARCH 0.2967, HAR 0.3108, EWMA 0.3846, and trailing 0.4339. Combined-minus-VXN QLIKE is 0.02091 (HAC lag-21 p=0.182); the 63-session paired bootstrap relative QLIKE reduction is -7.78% (95% CI [-17.32%, 3.17%]). Combining forecasts does not reliably beat the strongest individual benchmark.

H8 replays the exact fixed Nasdaq H7 signals through QQQ from 2012-01-04 to 2026-01-02 (3,520 marked rows, 3,519 executed signals), with 10% target volatility, long-only 0–100% exposure, unchanged next-open execution, dividend treatment, and 0/1/5/10/25 bp fees. At 5 bp, full DGS1MO accrual raises CAGR by 0.72–0.87 percentage points for the four risk-targeting strategies. Their CAGR rank remains trailing, GARCH, combined, VXN; VXN moves just above combined in common-rate Sharpe, but the paired 63-session Sharpe interval for VXN minus combined spans zero ([-0.0367, 0.0537]). Buy-and-hold still has the highest CAGR but realizes 20.50% volatility and is not a like-risk comparator. The cash adjustment improves absolute returns for cash-holding rules; it does not establish an economically superior sophisticated rule.

## Design and information controls

The protocol was registered before outcome analysis in commit `88de0f5`; data-source permission/coverage amendments were committed before outcomes in `ced7cce` and `fb20a28`. Forecast evaluation cuts off origins at 2025-12-31. Historical realized targets use actual XNYS sessions. Forecasts use the regular scheduled-session policy in `src/vrp/asof_garch_calendar.py`; future unscheduled closures are excluded. The XNYS utility bounds were extended to 1985 only because the verified Nasdaq return history begins in 1986; the target and S&P outcome periods are unchanged.

The primary target is implied annualized variance less subsequent annualized realized close-to-close variance. Forecast losses, masks, annualization, three recursive GARCH configurations, post-2014 sensitivity, nonoverlapping 30-calendar-day origins, paired HAC tests, and Holm adjustments follow the existing S&P implementation. H5's NBER labels are historical ex-post outcomes, not inputs to forecasts. H6–H8 are explicitly post-H1–H5 exploratory extensions, with no refitting or tuning of H7 models for H8.

## Market and source coverage

| Market | Implied-volatility data | Underlying/investable data | Executed scope | Status |
| --- | --- | --- | --- | --- |
| NASDAQ-100 | Cboe VXN via FRED current-vintage history (2001-02-02 onward), overlapping official Cboe daily series checked exactly | Nasdaq-100 via FRED (1986-01-02 onward); QQQ vendor OHLC/dividend/split snapshot | H1–H8; paired H1/H2 with S&P | Computed, provisional |
| S&P 500 reference | Existing frozen VIX/S&P package | Existing SPY package | Preserved; synchronized H1/H2 and 5 bp H8 results used for comparison | Existing provisional baseline |
| Russell 2000 | Official RVX history is acquired; FRED current-vintage RVX begins 2004 | Candidate RUT history in the environment is a vendor snapshot, not an independently verified authoritative index history | No inferential H1–H8 execution | Blocked: authorized licensed RUT/index observations were not present for validation; IWM alone cannot substitute for the index target |
| EURO STOXX 50 | VSTOXX has a full-history licensing boundary | Licensed EURO STOXX 50 series and aligned investment proxy data not present locally | No inferential H1–H8 execution | Blocked pending licensed entitled files and documented calendar/time-zone alignment |
| DJIA/VXD | Not independently verified for the full required scope | DIA proxy not fully source-audited here | Not run | Excluded optional market |

The author attested on 2026-10-15 that written permissions cover research use and public sharing of derived results from all proposed providers. License documents are not stored in this checkout. Raw source observations remain local and ignored; manifests retain source identity and SHA-256 values. Permission does not itself supply missing source files or establish source accuracy.

## Answers to the registered scientific questions

1. **Positive VRP across markets:** positive long-run point estimates appear in Nasdaq and S&P; same-origin differences are not significant. The 2007–2025 test and post-2014 period do not provide strong evidence of consistent positivity. Two U.S. indices are not broad global external validity.
2. **Calibration failures:** market-specific H2 fits and paired interaction contrasts show no stable difference in the common sample. Failure to reject exact calibration is not evidence of equivalence; recent-sample uncertainty is substantial.
3. **Implied-volatility forecasting beyond S&P:** VXN is the strongest tested Nasdaq H3/H7 benchmark by RMSE/QLIKE, but paired cross-market series-level H3 loss contrasts were not available in the frozen S&P summary, so relative effect magnitudes are not formally pooled.
4. **Incremental GARCH:** not supported in Nasdaq H4/H7; the encompassing GARCH coefficient and paired forecast improvements are uncertain.
5. **Regime dependence:** the NDX H5 recession coefficient is imprecise and post-2014 is inconclusive; negative selected crisis-year means counsel against a stable regime claim.
6. **Extreme-volatility event prediction:** H6 historical event scores are weak and do not establish useful prospective warnings.
7. **Forecast combinations:** H7 combined forecasts do not reliably beat VXN or GARCH; H8 does not show robust economic superiority for the combined rule.
8. **Investable risk control:** QQQ cash accrual lifts absolute performance but leaves the fixed strategy CAGR order unchanged and the risk-targeting rules below buy-and-hold CAGR. The cash proxy is not an actual broker return.
9. **Robustness:** the broad directional ordering survives 21-session and post-2014 checks, while statistical significance and relative magnitudes weaken in the recent sample.
10. **Supported versus open:** support is strongest for positive full-history sample means and the fact that volatility rules mechanically reduce realized risk. Forecast, event, regime, global generalization, and alpha claims remain exploratory, inconclusive, or unsupported.

## Reproduction and artifact identity

Run from the repository root with the locked environment and local authorized input files:

```powershell
$env:PYTHONPATH = "src"
python scripts/run_cross_market_us_h1_h2.py
python scripts/run_cross_market_ndx_garch.py --variant normal_expanding --variant t_expanding --variant normal_rolling5y
python scripts/evaluate_cross_market_ndx_h3_h4.py
python scripts/run_cross_market_ndx_h5.py
python scripts/run_cross_market_ndx_h6_h7.py
python scripts/run_cross_market_ndx_h8.py
python scripts/audit_cross_market_ndx_h8_components.py
python scripts/compare_cross_market_ndx_spx.py
```

The full local JSON results are stored under `outputs/cross_market/v1/` (ignored by Git along with market observations). Their SHA-256 digests and input manifest digests are in `data/manifests/cross_market_execution_v1.json`. The compact interpretation and exact principal estimates are recorded in [cross_market_results.md](cross_market_results.md). Run `pytest -q`, `python -m compileall src tests scripts`, and `git diff --check` for implementation qualification. All results remain provisional pending independent scientific review and rerun from entitled source data.
