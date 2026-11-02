# Exploratory prediction, portfolio and external-market extensions

All extensions are historical and exploratory, selected after inspection of the S&P 500 H1–H5 results. They remain provisional pending independent coauthor review. Registering their subsequent implementation does not make the 2012–2025 evaluation prospective. No prospective extension results or executable variance-option strategy results are available.

## Design and version control

H6–H8 share 3,520 evaluation origins in 2012–2025 after a 2007–2011 warm-up. Fitted models update at 168 monthly refits using only training labels whose complete 30-calendar-day outcomes have matured. Features use information through the origin, scaling is training-only, and cached Gaussian expanding GARCH forecasts are reused. No crisis observations are deleted. The outcome and implied variance remain annualized decimal variances,

$$
y_t=\frac{365}{30}\sum_{t<d\leq t+30\mathrm{c}}r_d^2,
\qquad i_t=(VIX_t/100)^2.
$$

The evidence below uses version 2 of the extension. Version 1 used finalized calendars containing future unscheduled closures and is explicitly invalidated for strict as-of calendar claims. The correction separates forecast-time scheduled sessions from actual target sessions, changes 61 forecast origins and analytically extends ten cached GARCH variance vectors; it does not alter the historical outcomes or select new model settings. The historical artifacts are preserved. This calendar repair does not constitute independent scientific acceptance.

H6 and H7 compare paired loss differences with Bartlett HAC(63), HAC(21) sensitivity, and circular 63-session block bootstrap intervals (1,000 draws, seed 1729). Holm correction covers the four advanced-versus-simple H6 tests and three combination-versus-constituent H7 tests separately. H8 has one primary contrast, combination versus trailing at 5 bp. Historical bootstrap intervals do not remove the exploratory selection of the research questions or establish future performance.

## H6: underestimation events

The fixed event is $Y_t=1[y_t>1.5i_t]$, corresponding to a realized-to-implied volatility ratio above $\sqrt{1.5}$. There are 244 events (6.932%). Model A is an expanding matured event-frequency forecast; B is a logistic regression on log implied variance; C is a six-feature logistic model; D is a fixed shallow gradient-boosting model. Neither advanced model improves primary Brier loss.

| Model | Mean probability | Brier | Event contribution | Nonevent contribution | ROC AUC | Recall at retrospective 10% alert budget |
|---|---:|---:|---:|---:|---:|---:|
| A | 0.082965 | 0.065280 | 0.058785 | 0.006496 | 0.3223 | 0.0000 |
| B | 0.086696 | 0.066011 | 0.058743 | 0.007268 | 0.3216 | 0.0041 |
| C | 0.094268 | 0.067777 | 0.056996 | 0.010782 | 0.5084 | 0.0574 |
| D | 0.085558 | 0.070276 | 0.060028 | 0.010248 | 0.3917 | 0.0328 |

For C versus A, excess Brier is 0.002497 (HAC 95% CI [−0.000333, 0.005327], Holm $p=0.1674$). D is worse than A by 0.004996 ([0.001584, 0.008408], Holm $p=0.01641$). C's event contribution improves by 0.001789, but its nonevent contribution worsens by 0.004286; over-warning on numerous nonevents offsets its event-day improvement. Its ROC-AUC block interval [0.3878, 0.6226] includes chance. Neither advanced model passes the registered joint requirement of at least 5% relative Brier improvement and five percentage points of recall improvement against the strongest simple benchmark.

The 10% alert budget ranks the entire evaluation sample and is a retrospective allocation diagnostic. It is not a deployable threshold. The separately saved training-quantile rule has varying alert fractions; A alerts on every date because of ties. The event is relative to implied variance: a high VIX raises the realized-variance threshold. Thus these events cannot be interpreted as an exhaustive definition of economically severe volatility shocks.

## H7: combining variance forecasts

The six fixed forecasts are raw implied variance, Gaussian GARCH, trailing calendar-month variance, EWMA, HAR-style ridge on daily squared-return proxies, and a nonnegative-coefficient ridge combination of implied, GARCH and trailing variance. The HAR model does not use intraday realized variance. The combination is not a convex weighted average: its intercept and coefficient scaling matter. Primary QLIKE is $y/f-\log(y/f)-1$; negative candidate-minus-baseline differences favor the candidate.

| Forecast | QLIKE | RMSE | MAE | Mean forecast minus outcome |
|---|---:|---:|---:|---:|
| Implied variance | 0.385802 | 0.060933 | 0.022692 | 0.007424 |
| GARCH | 0.389746 | 0.067156 | 0.020418 | 0.000367 |
| Trailing | 0.607323 | 0.080749 | 0.023392 | 0.000577 |
| EWMA | 0.525568 | 0.071736 | 0.021981 | 0.000176 |
| HAR-style ridge | 0.413478 | 0.062619 | 0.021308 | 0.003017 |
| Combination | 0.387982 | 0.063252 | 0.020923 | 0.003722 |

| Combination minus baseline QLIKE | Difference | HAC(63) 95% CI | Holm $p$ |
|---|---:|---|---:|
| Implied variance | 0.002180 | [−0.044002, 0.048362] | 1.0000 |
| GARCH | −0.001763 | [−0.029652, 0.026126] | 1.0000 |
| Trailing | −0.219341 | [−0.342043, −0.096639] | 0.001377 |

The combination improves a weak trailing benchmark but does not pass the registered requirement of a 5% QLIKE reduction against the strongest constituent with at most 5% RMSE deterioration. Its lower MAE than implied variance coexists with worse RMSE and QLIKE. Constituent forecast correlations are high (implied/GARCH 0.8962; GARCH/trailing 0.9258), but overlapping information is an association, not an identified cause of failure. Raw implied-variance coefficients rise from 0.2078 to 0.6799 across refits while GARCH coefficients fall from 0.5289 to 0.2048; no coefficient intervention was tested. Descriptive calibration projections use evaluation outcomes and must never be presented as submitted forecasts.

The table uses the registered primary HAC(63) intervals and the Holm adjustment based on those tests. HAC(21) is a sensitivity: combination minus implied, GARCH, and trailing has raw two-sided $p$ values 0.917728, 0.894317, and 0.00021056, respectively; the corresponding HAC(63) raw values are 0.926278, 0.901381, and 0.00045900. The HAC(21) result is not the primary test.

## H8: next-open SPY execution and cash sensitivity

Each strategy uses $w_t=\min\{1,\max[0,0.10/\sqrt{f_t}]\}$, trades at the next exchange open, and remains long-only without leverage. The self-financing accounting credits old-share overnight returns and dividends before rebalancing, new-share intraday returns afterward, and costs on traded notional. There are 3,520 open marks from 2012-01-04 to 2026-01-02 and 3,519 earned signals; the final forecast earns no return. The primary case charges 5 bp per traded notional and initially assumes zero cash yield.

| SPY policy | Zero-cash CAGR, % | Annual volatility, % | Rolling 21-session target RMSE, % | Full-DGS cash CAGR, % | Cash CAGR increment, pp |
|---|---:|---:|---:|---:|---:|
| Buy-and-hold | 14.7953 | 16.6676 | 9.9570 | 14.7953 | 0.0000 |
| Trailing | 9.7603 | 10.1395 | 2.9597 | 10.1644 | 0.4041 |
| Implied variance | 7.3026 | 7.7745 | 3.2980 | 7.9457 | 0.6431 |
| GARCH | 9.0291 | 9.4509 | 2.6846 | 9.5172 | 0.4881 |
| Combination | 7.9389 | 8.4384 | 3.0281 | 8.4919 | 0.5530 |

The combination reduces overall volatility but worsens rolling target RMSE relative to trailing by 0.06849 percentage points (block-63 95% CI [−0.20909, 0.37154] pp). Its CAGR difference is −1.82134 pp ([−3.03400, −0.68716] pp). It fails the joint requirement of at least 0.5 pp RMSE reduction without more than 0.5 pp CAGR deterioration. The disadvantage exists gross of costs: combination CAGR 8.2297% versus trailing 9.9988%. Transaction costs alone do not explain it.

The additive annual-variance bridge for combination is −0.00287939 relative to the 10% target variance. Its cap term is only −0.00002224; the largest term, −0.00202096, is the horizon/aggregation/changing-exposure bridge. Consequently cap binding is not an adequate explanation of the aggregate undershoot. The bridge is an accounting decomposition, and its largest term remains economically unresolved.

The separately registered cash experiment retains the signals and weights and models initial-release ALFRED DGS1MO quotes available before each prior open. It accrues simple ACT/365F interest on actual prior post-trade cash over elapsed calendar days. It also preserves zero, half-DGS and converted DTB4WK scenarios. Full Treasury pass-through is a hypothetical liquid cash account, not observed broker compensation or an executable Treasury total return. At 5 bp, the block-63 intervals for incremental CAGR are [0.2538, 0.5774] pp (trailing), [0.4293, 0.8786] pp (implied), [0.3204, 0.6856] pp (GARCH), and [0.3685, 0.7558] pp (combination). Point CAGR order is unchanged. Zero-reference Sharpe rankings can change, while a common DGS opportunity-cost benchmark gives a different order; these small ranking differences do not establish alpha. Every cash scenario retains the failed H8 joint gate.

Fractional shares, opening fills, flat transaction costs and ex-date rather than payment-date dividend credits are simplifying assumptions. Taxes, market impact, bid–ask histories and actual broker sweep terms are absent. The VIX itself is not traded. Executable option surfaces, funding and margin data needed for H9 remain unavailable.

## External-market evidence and incomplete registered inference

The tracked cross-market report describes Nasdaq-100/VXN/QQQ results; Russell 2000 and EURO STOXX 50/VSTOXX remain blocked by unavailable verified underlying or entitled full-history files. VXN and Nasdaq observations are current-vintage histories, not point-in-time vintage reconstructions. The execution manifest identifies seven output JSONs, none present in this checkout. A fresh H1/H2 calculation below uses recovered, hash-exact Nasdaq and VXN source snapshots and freshly reconstructed S&P targets; it is not a recovery of the historical output bytes. The remaining H6–H8 and QQQ values are report transcriptions, not fresh market refits.

| Nasdaq versus S&P comparison | Origins | Nasdaq 30c proxy mean | S&P 30c proxy mean | Paired difference; reported HAC(21) 95% CI; raw $p$ |
|---|---:|---:|---:|---|
| Common 2007–2025 | 4,780 | 0.006704 | 0.007472 | −0.000768; [−0.002396, 0.000860]; 0.355 |
| Post-2014-10-06 | 2,827 | 0.004668 | 0.006668 | −0.002001; [−0.004163, 0.000161]; 0.0697 |

The paired H1 figures above agree with the fresh reconstruction to displayed precision. For the longer Nasdaq sample (6,241 origins), the reported mean is 0.008587 (HAC(21) raw $p=0.00830$), compared with $p=0.0780$ on the common 2007–2025 sample and $p=0.3316$ post-2014. These different rejection outcomes do not themselves demonstrate a market difference. The report gives Nasdaq 2012–2025 H6 prevalence 8.81%, model-D relative Brier reduction versus A of −3.47% (63-session interval [−6.44%, −1.24%]), and combination-minus-VXN QLIKE 0.02091 (HAC(21) sensitivity $p=0.182$). QQQ zero-to-full-DGS CAGR rises from 11.288% to 12.008% for trailing and 9.411% to 10.228% for combination. These are provisional descriptive extensions to the SPY findings.

The newly calculated paired H1 circular bootstrap uses synchronized dates and 1,000 valid draws per interval, seed 1729. For 30c, the primary block-63 percentile intervals are [−0.002712, 0.001056] for 2007–2025 and [−0.005049, 0.000293] post-2014; block-21 intervals are [−0.002395, 0.000764] and [−0.004178, 0.000165], while block-126 intervals are [−0.002768, 0.001147] and [−0.005050, 0.000616]. The 21-session-target results and full precision are in `paired_h1_h2_rebuilt.json`. These intervals are fresh partial evidence, not a completed registered H1–H5 bootstrap family or adjusted tests.

For H2 on the common 30c sample, the Nasdaq-minus-S&P intercept interaction is 0.002586 (SE 0.001484, raw normal $p=0.08137$) and slope interaction is −0.013137 (SE 0.035828, raw $p=0.71386$). The producer stacks both markets in an OLS regression with market intercept and slope interactions, sums the two score vectors within each date, and applies Bartlett HAC at 21 ordered-origin lags to those grouped scores, with factor $2n/(2n-4)$. It is not a regression of one market's outcome on the other market's outcome. This reconstruction calls the historical producer for that covariance; its label of independent verification should not be read as an independent reimplementation.

There is a material registration–implementation gap. The cross-market protocol specifies paired circular block bootstrap contrasts with blocks 63 (primary), 21 and 126, 1,000 draws, seed 1729, and Holm correction across new-market primary H1–H5 contrasts. The historical paired-market producer implements only H1 and H2, using HAC(21), with no market-contrast bootstrap or Holm adjustment. The new calculation supplies H1 bootstrap intervals only. Within-Nasdaq H6/H7 bootstrap/Holm routines and H8 scenario bootstraps do not complete that registered cross-market family. H3 per-origin S&P forecasts were not preserved in the reported historical summary, preventing an honest paired cross-market H3 loss test from those summaries alone. No completed H1–H5 cross-market family or adjusted market-superiority conclusion can be claimed. Non-rejection is not calibration equivalence or evidence of no economically meaningful difference.

## Provenance and reproduction boundary

The authoritative rules are `paper/method_protocol.md` 1.1.0 and its deviation log, followed by the separate extension, failure-diagnostic, cash and cross-market registrations. The inspected integration tree is `27735e5653b5b778fb0e23ccc3e9079d4bdd6aa3`. Exact Git sources for numerical recovery are:

| Evidence | Git tree | Artifact and SHA-256 |
|---|---|---|
| H6 v2 | `2ac49b69d56db939d051849c6dbaf1c9eaa4ec12` | `quant_extension_h6_v2.json`: `2a8107e9ace5dcfd565bbdba59bf7f298906584d3050565806f129072b4715c9` |
| H7 v2 | same | `quant_extension_h7_v2.json`: `cec3e911eaef7f4d27d8395ba8316f807a910b82601a79bcfe29a8f636001d68` |
| H8 v2 | same | `quant_extension_h8_v2.json`: `b09b8f3ffdd8af230854709e39771efb0e73f8c9b5afb9c5b33607e04183f001` |
| Failure diagnostics | `956a9d8aa9ebc05c55e71241aeffbc11d80e2a7e` | `quant_failure_results_v1.json`: `165ee888a84dd8df8a406490ac81b67667eee7906e0cb98c4c579cd6672ac80d` |
| Cash sensitivity v2 | `0910d8e26355832bdbd63abbc10a65a70bbc4d77` | `h8_cash_results_v2.json`: `849296a15472fb8f4902d275807c66f8b58af49de4cf5d182baec8da4ab884fd` |
| Cross-market report | `27735e5653b5b778fb0e23ccc3e9079d4bdd6aa3` | `docs/cross_market_results.md`; output hashes are recorded in `cross_market_execution_v1.json`, but output bytes are absent |

Manifest filenames in the table are under `data/manifests/`. The portable `verify_extensions.py` reads exact Git blobs, checks declared producer-source hashes and result hashes, reconstructs H6 Brier contributions and H7 QLIKE differences from committed tables, and reconstructs primary zero-cash H8 terminal wealth, CAGR, volatility and rolling-risk RMSE from daily return components. The fresh replay passes and its full receipt is `extension_receipt_reverified.json`. It checks cash-summary identities and unchanged CAGR ordering, but does not refit models, rebuild original forecast paths or replay all cash ledgers. The fresh full implementation suite passes 1,839 tests in 23.58 seconds using Python 3.12.14; the original execution manifest records Python 3.11.5. This is a compatibility check, not a bitwise environment reproduction.

The original raw-data replay entry points fail because ignored empirical, failure and cash output files are absent; the concrete errors are retained in `replay_extension.log`, `replay_failure.log` and `replay_cash.log`. Passing unit tests and the available component replay support implementation and arithmetic consistency, but do not establish independent freeze acceptance, raw-to-result reproducibility or recovery of absent cross-market output bytes.

### Reproduction of the partial paired calculation

Both scripts accept explicit paths and can be launched from any working directory. Set `AUDIT_DIR` to this supplement's directory, `CHECKOUT` to the cross-market source checkout, `SOURCE_DIR` to a private directory holding the two exact CSVs, `SPX_TARGETS` to the reconstructed target CSV, and `OUTPUT_DIR` to an existing writable destination. With the recorded dependencies installed, run:

```sh
python "$AUDIT_DIR/rebuild_paired_h1_h2.py" \
  --checkout "$CHECKOUT" --source-dir "$SOURCE_DIR" \
  --spx-targets "$SPX_TARGETS" --output "$OUTPUT_DIR/paired_h1_h2_rebuilt.json" \
  > "$OUTPUT_DIR/paired_h1_h2_rebuilt.log"
```

To attempt source recovery instead, `python "$AUDIT_DIR/fetch_pinned_sources.py" --checkout "$CHECKOUT" --output "$SOURCE_DIR"` writes the recovered CSVs and a recovery receipt only under that chosen directory, subject to the original hash gate. It requires `requests` and network access. Source files are private and must not be committed. To repeat the separate Git-blob component audit, run `(cd "$CHECKOUT" && python "$AUDIT_DIR/verify_extensions.py")` with the listed historical commits available; that audit reads Git objects from its working directory.

The paired run used Python 3.12.14, numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, statsmodels 0.15.0 and exchange-calendars 4.13.2. It checks Nasdaq and VXN input hashes `2326ea9359dc6d521ada1c0600b90be23e054b4ba93955a615a5dba97159ff9f` and `53aa81e815b3f9f5b7b18bcfa64f0c5d02b2341aad5b128307f069d1d7bd3f2f`. The rebuilt S&P target hash is `3c7fc89fc510659fca0a976ad0d61f780aa93505cc2764f53d38a3a14d671fbc`, different from the original derived-byte hash; its provenance and rebuild limits are in `prov-delivery/provenance.md`. The Nasdaq panel spans 2001-02-02 to 2025-12-31; the session audit finds missing 2002-01-29 in the underlying and excludes three non-session dates from each series, as recorded in the JSON. The FRED snapshots were recovered by retaining only the prefix whose exact original hash matched; the TLS recovery receipt records the appended bytes. The input paths in the JSON are logical identifiers from the original workspace, not required current locations; the flags select their current locations. Those private inputs and Git objects are prerequisites, not embedded in this supplement. The fresh result depends on the historical cross-market implementation; it is a numerical reconstruction, not independent model validation.
