# Operational research progress

Protocol: `paper/method_protocol.md` **1.1.0**. Track B execution owner:
Aleksandar Slavov / Codex. Independent scientific approval remains with the
other coauthor. This is the operational source of truth; historical W-task
references in individual notes are retained. No central tracker was present
in the fetched checkout.

## Milestones and acceptance criteria

| ID | Milestone | Status | Acceptance / evidence | Next action |
|---|---|---|---|---|
| EMP-001 | Inspect scientific branch and locked environment | COMPLETE | Start `456a77c`; clean execution branch; Python 3.11.5; all 51 lock entries match installed versions; baseline 1,620 tests passed; compileall passed. | Keep lock/protocol unchanged. |
| EMP-002 | A: immutable production acquisition | ACQUIRED / VIX QUALITY BLOCKED | Yahoo 9,088 rows accepted; Cboe 9,091 rows rejected; FRED 2,338 usable overlap. Verified default TLS, immutable artifacts/hashes under `data/raw/2026-10-13T142430Z/`. | Obtain reviewed resolution for VIX defects; do not promote rejected data. |
| EMP-003 | A: source discrepancy audit | PARTIAL / REVIEW REQUIRED | Reproducible date-only audit; four missing VIX sessions, 28 non-sessions, 47 OPEN-only defects; seven Yahoo/FRED discrepancies. Official Cboe 2019 correction supports one discrepancy; other six unresolved. | Review findings in `docs/production_data_freeze_report.md`; seek authoritative source clarification. |
| EMP-004 | B: reproducible verified origin panel | BLOCKED | Actual builder rejected with `PanelProvenanceError: VIX: acquisition not accepted`. No output panel. | Require both existing source gates to pass before construction/repeatability claim. |
| EMP-005 | B: independent freeze review | PENDING EXTERNAL REVIEW | Coauthor reviews exact hashes, quality findings and freeze report. Code/tests cannot provide this approval. | Deliver reviewable freeze report after EMP-004. |
| EMP-006 | C: returns and all six forward targets | BLOCKED BY EMP-004 | Existing functions tested; production target execution not run. No return/VRP/target artifact claimed. | Reuse existing scientific functions after quality gates pass. |
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

### 2026-10-13 — production acquisition and rejection diagnosis

- Tracker initialization commit: `8256a34`. Baseline: **1,620 passed in
  24.16 s**; compileall successful. All 51 pinned package versions verified;
  Windows-only transitive `colorama==0.4.6` additionally installed by pytest.
- Both locked acquisitions executed using existing tools/default certificate
  verification. Yahoo passed, VIX failed. Hashes and findings are preserved
  in sanitized manifests and the experiment log. No gate or protocol changed.
- Verified-panel command executed and rejected the VIX manifest. Local
  `outputs/panel_gate.log` records the traceback. No panel or scientific
  H1–H5 result generated.
- Added a narrowly scoped rejection-audit command and auxiliary official XLS
  inspection script. The latter uses isolated `xlrd==2.0.2` in
  `outputs/archive_inspection`; it does not modify the locked empirical
  environment or feed the production pipeline.
- Archive inspection initially misclassified textual `n/a` as present numeric
  data. Invalid preliminary metadata retained locally as
  `outputs/archive_inspection_invalid_v1.json`; corrected inspection distinguishes
  row presence from finite closes. Four synthetic missing-value regressions
  pass. Only 1999-12-31 has a usable archived close among the four missing dates;
  no source stitching performed.
- Focused new checks: **14 passed in 5.70 s** (hash tampering, redaction,
  missing-session diagnosis, replay, immutable repeat output, n/a/NaN/infinity).
  Full suite: **1,634 passed in 14.02 s**. `compileall src tests scripts`
  and `git diff --check` passed before the implementation commit.
- Next action: deliver exact sanitized source audit for independent review.
  VIX quality and six unexplained Yahoo/FRED differences remain external
  source/review blockers; gate-compliant targets cannot proceed yet.
