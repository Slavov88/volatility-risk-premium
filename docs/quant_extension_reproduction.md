# Quant extension reproduction

**EXPLORATORY — POST H1–H5 RESULT SELECTION — PENDING INDEPENDENT REVIEW**

Use Python3.11 and the unchanged `requirements-dev.lock` plus additive `requirements-quant-extension.lock`. Install editable repository without resolving dependencies. Exact environment versions are in `data/manifests/quant_extension_execution.json`. Baseline raw provider data/checkpoints and new SPY CSV are intentionally local ignored artifacts; a fresh Git clone cannot execute the empirical study without these licensed/provider source artifacts. CI qualifies synthetic/integration logic without distributing market data. Sanitized complete result JSON and PNG publication figures are tracked.

From repository root, with original verified source/target/GARCH trees in place:

```powershell
.venv/Scripts/python.exe scripts/run_quant_extension.py h6
.venv/Scripts/python.exe scripts/run_quant_extension.py h7
.venv/Scripts/python.exe scripts/run_quant_portfolio.py acquire
.venv/Scripts/python.exe scripts/run_quant_portfolio.py h8
.venv/Scripts/python.exe scripts/audit_quant_extension.py
.venv/Scripts/python.exe scripts/report_quant_extension.py
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m compileall -q src tests scripts
git diff --check
```

Each execution requires committed exact source code. Original result commits are stored inside the result JSON. On an exact original code checkout, wrappers reproduce original immutable JSON/CSV; later commits with identical model source hashes have different Git identity metadata. Therefore **to replay in the delivered checkout**, use `scripts/replay_quant_extension.py`, which recomputes all H6/H7/H8 numerics and refuses changed CSV bytes, source hashes or numerical fields while recording the original/replay Git identity separately. Never overwrite an immutable result to update metadata. Report-generator output is deterministic within the pinned environment; cross-platform figure/font binary identity is not promised. Scientific numeric equality and source hashes matter separately from renderer binary hashes.

Forecast CSVs preserve origin, target and each model prediction plus fit-as-of dates. H6 JSON contains all168 refit hyperparameters, scaling, logistic coefficients and tree importances; trees are reconstructed deterministically from frozen training inputs/settings. H7 JSON contains all168 coefficients, scaling/smearing and positivity-floor counts. H8's25 logs preserve signal origin, execution date, shares/cash, dividend credit, trades, costs, NAV, returns and exposure. `independent_audit.json` checks every portfolio row and fixed ordinal model anchors. `baseline_preservation.json` pins56 prior processed/results/checkpoint/report files; raw-source hashes also revalidated by existing freeze loader.

Registration timestamp and prospective rule are in `quant_extension_registration.json`; use a separate future artifact namespace, unchanged settings, actual as-of new GARCH and252 matured origins before assessment. No future observations are included here. Independent review is required before promoting scientific claims. H9 remains blocked on actual option quotes/funding/margin/license acquisition.
