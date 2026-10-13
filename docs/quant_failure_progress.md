# Failure investigation execution and verification

**EXPLORATORY DIAGNOSTICS — PENDING INDEPENDENT COAUTHOR REVIEW**

Branch `agent/quant-failure-mechanisms` starts from verified Task1 head `b03686ece031038b9daba03a9a4b1990d4e95674`. The plan was committed as `7ad9187` before decompositions. Primary producer `89cd4a7`, independent diagnostic producer `315f9d3`; fixed severity uncertainty / publication checks `a4bf94f`. No model refit, coefficient change, threshold search, new strategy, data acquisition, options purchase or proposed future experiment executed.

The investigation is complete on3520 common origins,168 original monthly fit records and all25 original SPY ledgers. It includes all35 fixed partitions, original periods, each year and leave-year-out comparisons, future-outcome severity groups explicitly labeled as hindsight, and fixed block21/63/126 uncertainty. No sparse or unfavorable cell was omitted. Overlapping event origins are not independent shocks.

- [H6 report](h6_failure_analysis.md): non-event excess Brier outweighs event-loss improvement; ranking and calibration differ; original full budget versus executable saved thresholds; chronological drift and2020 forward-label chronology.
- [H7 report](h7_failure_analysis.md): all six forecasts, loss dimensions, exact calibration/MSE decomposition, raw coefficients, correlated inputs, fixed regimes and episode concentration.
- [H8 report](h8_failure_analysis.md): unchanged cap, exposures/cash, accounting identities and full covariance terms, instrument/horizon/timing bridges, costs/gross/net and regime contributions.
- [Synthesis](quant_failure_mechanisms.md): each explanation has supporting and contrary observations. One future horizon/instrument-matching hypothesis, with fixed practical criteria and504 matured prospective origins, is proposed only.

Additional [false-negative / true-positive severity intervals](tables/quant_failure/false_negative_severity_uncertainty.csv) quantify forward variance ratio, realized volatility and origin IVOL on every fixed group/model/alert-policy cell. These intervals condition on the original saved allocation; the retrospective budget is not reselected for this severity calculation. Circular block63 bootstrap1000 draws,seed1729 resamples full chronology then selects the subgroup. Empty/no-event cells retain null intervals and valid-draw counts. The main alert recall bootstrap separately reselects hindsight allocations as specified.

C's230 false negatives under the original whole-sample budget have mean realized/implied variance ratio3.79224 (95% interval2.32260–5.91110) and mean realized volatility28.5777% (22.3568%–35.4763%). The saved executable policy still misses207 events, mean ratio3.84133 (2.32589–6.20605). These are substantial missed risks, not merely marginal threshold crossings; the uncertainty and target overlap preclude treating them as independent shocks.

Numerical evidence: [primary results](../data/manifests/quant_failure_results_v1.json), [independent audit](../data/manifests/quant_failure_independent_audit_v1.json), [severity and publication checks](../data/manifests/quant_failure_final_checks_v1.json). Local namespaces `outputs/quant_failure_diagnostics/v1/` retain exact JSON/CSV evidence. Sanitized numerical tables and five PNG/PDF figures are committed; provider-price datasets remain local and unchanged.

Publication inventory **v3 is current**. V1 was the initial publication inventory; v2 froze the scientific table whitelist so subsequent QA tables cannot silently change it; v3 moves the annual prevalence legend clear of the2018 peak. These change publication/replay bookkeeping and figure layout only. Earlier inventory JSONs remain preserved, and all v1/v2 report/table/figure bytes are archived locally under `outputs/quant_failure_diagnostics/v1/publication_drafts/v2/` (the two inventories reference identical publication bytes). Numeric producer identities and primary/audit result hashes are unchanged. See [current publication hashes](../data/manifests/quant_failure_publication_v3.json).

Reproduce from the pinned local datasets and committed source:

```powershell
.venv/Scripts/python.exe scripts/run_quant_failure.py
.venv/Scripts/python.exe scripts/run_quant_failure_audit.py
.venv/Scripts/python.exe scripts/publish_quant_failure.py
.venv/Scripts/python.exe scripts/quant_failure_final_checks.py
.venv/Scripts/python.exe scripts/replay_quant_failure.py
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m compileall -q src tests scripts
git diff --check
```

Initial producers pin their execution commits; running them at a later head deliberately fails immutable persistence if only the commit identity differs. Use the replay script at the delivery head: it verifies original source hashes, executes all scientific calculations again, compares every numerical/table/publication field while preserving producer identities, and records a new replay audit. Final-check addenda have the same immutable commit rule. Missing original datasets fail closed; no replacement data are acquired.

Full local pytest passed **1824 tests in36.66s**; compileall src/tests/scripts and git diff checks passed. Added adversarial checks cover future-outcome perturbations to origin-observable partitions, fixed boundaries, weighted rank ties/zero weights, Brier within-bin residual, imbalance, calibration cross terms, cap behavior under future shocks, maturity-preserving bootstrap groups, dividends, fees, share/cash ledger tampering and the unused final signal. Independent original portfolio metrics are reconstructed with compensated sums and a separate NAV/drawdown loop; exact scoring and25-ledger cash/share/covariance identities pass. Five PNG previews are visually inspected; standalone PDFs are also rendered for inspection. The final execution manifest records actual replay, visual, environment, branch and CI evidence. Automated verification is not independent coauthor acceptance.

All original H1–H8 outputs, fitted model source and report bytes remain hash-preserved. Task1's status remains **CORRECTED / PROVISIONAL — PENDING INDEPENDENT COAUTHOR REVIEW**; its draft PR and prior branches are untouched. This task receives a separate draft PR targeting `agent/asof-calendar-repair`, with no merge.
