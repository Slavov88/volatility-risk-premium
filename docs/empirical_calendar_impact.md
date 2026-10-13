# Empirical calendar impact and version status

**CORRECTED / PROVISIONAL — PENDING INDEPENDENT COAUTHOR REVIEW**

**Current H3/H4 evidence:** [corrected results](h3_h4_corrected_results.md). Original30c GARCH-based H3/H4 comparisons are **SUPERSEDED / INVALID_FOR_STRICT_EX_ANTE_FORECASTING**; their result JSON/manifests, original reports and hashes remain immutable. Original21t numerical evidence is verified unaffected, but date metadata is superseded. This repair changes the forecasting information set, not any fit, target, criterion or selected model.

| variant | changed30c origins | extended vectors | changed21t values | max |forecast change| | max-change origin | first-step reconstruction error |
|---|---|---|---|---|---|---|
| normal_expanding | 61 | 10 | 0 | 0.0024819540117229 | 2018-12-04 | 0 |
| normal_rolling5y | 61 | 10 | 0 | 0.0029875576003412 | 2012-10-23 | 0 |
| t_expanding | 61 | 10 | 0 | 0.0028281455355906 | 2018-12-04 | 0 |

H1/H2 **all cells exactly reproduced**; formal H5 **all regressions exactly reproduced**. The original target data, VIX, source freeze, NBER labels and inference specifications are unchanged. H5 has a real ancillary dependency: it embeds primary H3 crisis forecast-loss tables. Two GARCH case RMSE display values differ only by floating-point summation: [{"corrected": 0.17314680450686998, "metric": "rmse", "model": "garch", "original": 0.17314680450686995, "signed_change": 2.7755575615628914e-17, "year": "2008"}, {"corrected": 0.02899562278888399, "metric": "rmse", "model": "garch", "original": 0.028995622788883988, "signed_change": 3.469446951953614e-18, "year": "2022"}]. These are rounding-scale companion-table changes, not revised H5 regime evidence. Preserve original H5 and use the corrected case-loss companion in the audit/cases manifest; never claim the entire H5 artifact is independent of GARCH.

H6–H8 v2 control: full H6/H7/H8 recomputation passes exact predictor-source hashes, every numerical field and all27 forecast/trade CSV bytes, with original result hashes unchanged. No reranking, refitting of historical GARCH, strategy change or data acquisition. Its Gaussian reaggregation helper already uses this corrected policy.

Calendar-rule verification:185 rule-generated dates2007–2026 match an independent standard-holiday implementation. Juneteenth's2022 observation was known before relevant horizons: [SEC Release34-93183,2021-09-30](https://www.sec.gov/rules/sro/nyse/2021/34-93183.pdf) states filing2021-09-28 and immediate operability. MLK effective1998 predates all OOS; obsolete election/Lincoln/Washington rules end earlier. This verification is limited to the registered2007–2025 origins and30c/at-most22-step horizons, not an assurance of arbitrary historical/horizon safety.

Numerical verification: 42 archived full/post2014 CC lag cells independently replayed; first-step reconstruction error0 for every cached fit; stored recurrence error<=1.74e-18 decimal variance; independent QLIKE identity error5.5511151231258e-17. Full producer replay repeats all14340 cache checks and all72 analysis cells exactly, including forecast JSON and comparison CSV bytes. H6–H8 v2 also fully replayed unchanged.

Original baseline summary/report files are intentionally not edited because their raw-byte hashes form the preserved evidence and extension's validation boundary. Current [versioned empirical summary](empirical_results_summary_calendar_v1.md), README, research-progress and experiment-log links point here. No independent coauthor acceptance or publication readiness is implied. Local validation1816 tests passed; compileall/diff-check and remote CI recorded in the current progress log.

Artifacts: `outputs/empirical_calendar_repair/v1/{corrected_results.json,forecasts/,metric_comparison.csv,forecast_comparison.csv,case_metrics.csv,independent_audit.json,decision_audit.json,deterministic_replay.json,extension_control_replay.json,preservation_snapshot.json}`. Sanitized manifests under `data/manifests/empirical_calendar_repair_*` preserve exact scalar results/settings/hashes without original provider prices. Failed synthetic assertions (selector return type; weekday rather than XNYS fixture dates) were corrected before final testing; no empirical run or cached fit failed.
