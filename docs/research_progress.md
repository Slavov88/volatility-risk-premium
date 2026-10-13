# Operational research progress

Protocol: `paper/method_protocol.md` **1.1.0**. Track B execution owner:
Aleksandar Slavov / Codex. Independent scientific approval remains with the
other coauthor. This is the operational source of truth; historical W-task
references in individual notes are retained. No central tracker was present
in the fetched checkout.

## Milestones and acceptance criteria

| ID | Milestone | Status | Acceptance / evidence | Next action |
|---|---|---|---|---|
| EMP-001 | Inspect scientific branch and locked environment | IN PROGRESS | Start `456a77c`; branch `agent/empirical-production`; fetched all remote branches; read locked methodology and provenance docs. Python 3.11.5 virtual environment created; exact dependency installation running. | Execute baseline tests and inspect remaining scientific modules/tests. |
| EMP-002 | A: immutable production acquisition | IN PROGRESS | Require verified TLS, locked Yahoo/Cboe windows, hashes and production-quality reports. No acquisition success claimed yet. | Run existing acquisition CLIs immediately after environment installation. |
| EMP-003 | A: source discrepancy audit | PENDING | Count missing sessions/OHLC defects; investigate historical Yahoo/FRED differences; never replace canonical values. | Inspect actual acquisition manifests and source rows locally. |
| EMP-004 | B: reproducible verified origin panel | PENDING | Both source quality gates pass; verified hashes/windows/calendar; no 2026 origins; repeat identical bytes and row counts. | Run `vrp-build-verified-panel` after EMP-002 passes. |
| EMP-005 | B: independent freeze review | PENDING EXTERNAL REVIEW | Coauthor reviews exact hashes, quality findings and freeze report. Code/tests cannot provide this approval. | Deliver reviewable freeze report after EMP-004. |
| EMP-006 | C: returns and all six forward targets | PENDING | Gate-accepted source artifacts; exact 30c/21t CC, Parkinson/GK; origin-aligned IVOL/IVAR/VRP_X/VOLGAP; diagnostics, hashes and repeatability. Pre-review outputs provisional. | Reuse existing scientific functions after quality gates pass. |
| EMP-007 | D: H1/H2 and diagnostic robustness | PENDING REVIEW GATE | EMP-005 accepted; protocol-defined HAC, calibration and mandatory sensitivities; complete experiment log. | Wait for independent freeze approval. |
| EMP-008 | E: recursive OOS and H3/H4 | PENDING REVIEW GATE | Prior milestones independently validated; locked units, windows and common masks. | Implement only after earlier scientific gates. |
| EMP-009 | H5 and paper reporting | PENDING | Prior validation gates, frozen NBER provenance/crisis dates; independent output audit. | Retain theory/Track A without modification. |

## Initial implementation inventory

- Existing: SPX/Cboe production acquisition, source-quality reports, immutable
  hash persistence, manifest-enforced origin panel, XNYS calendar, safe returns,
  exact forward targets/range estimators, premium units, HAC/regression helpers,
  summary, regime and OOS window/common-mask utilities, GARCH unit conversion.
- Corresponding synthetic tests exist. Their current execution status will be
  recorded below; existence is not a passing-test claim.
- Missing empirical artifacts in this checkout: production freeze, executed
  return/target dataset, reviewed inferential results, recursive fitted forecasts.
- Track A theory, pricer and validation notes are existing coauthor work and
  are outside the modifications planned for this execution.

## Reproduction

Use Python 3.11 and `requirements-dev.lock` without changing the lock.
Baseline/commit checks: `.venv/Scripts/python -m pytest` and
`.venv/Scripts/python -m compileall src tests`.
Acquisition commands follow README locked windows. Provider data stay ignored
under `data/raw/` / `data/processed/`; only sanitized provenance is committed.

## Append-only dated history

### 2026-10-13 — initialization

- Empty local Git checkout had no remote or files. Added the user-specified
  remote, fetched all branches, inspected history and created execution branch
  from `origin/agent/autonomous-research` at `456a77c`.
- Working tree was clean; no contributor changes were overwritten. Draft PR #1
  and all remote branches remain untouched.
- Reviewed authoritative methodology and data provenance in requested order.
  Protocol 1.1.0 and its scientific gates remain unchanged.
- Initialized tracker before production acquisition. Dependency installation
  and source/test inventory are in progress. No empirical result generated.
