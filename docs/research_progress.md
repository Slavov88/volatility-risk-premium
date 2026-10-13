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
| EMP-010 | Separate CLOSE candidate validation | CANDIDATE GENERATED / TESTING | Version `vix-close-candidate/1.0.0`; original immutable inputs replayed; 9,063 inspection origins, no production targets. Strict production path unchanged. | Complete source footprint diagnostics and full tests; deliver sign-off proposal. |
| EMP-011 | Source publication and close-correction investigation | IN PROGRESS | Official holiday notices found; original XLS evidence retained; 2019 correction independently explained, other six discrepancies unresolved. | Record hashed notices and diagnostic footprints without changing prices. |
| EMP-012 | Both-author CLOSE methodology sign-off | PENDING EXTERNAL APPROVAL | Candidate manifest cannot authorize itself; confirmatory loader explicitly rejects this contract under protocol 1.1.0. | Review `docs/vix_close_acceptance_proposal.md` once completed; both authors must sign. |

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

### 2026-10-13 — audit package delivery

- Implementation commit: `b191daf`. New regression tests plus the complete
  original suite passed: **1,634 tests**. No synthetic fixture replaced a
  production input.
- Produced four sanitized dated manifests, `docs/experiment_log.md`, and
  `docs/production_data_freeze_report.md`. These contain actual coverage,
  hash/replay evidence, defect dates, source-investigation limitations and
  exact reproduction commands. Provider price rows are excluded from Git.
- The only completed milestone is EMP-001. EMP-002's acquisition subtask is
  complete, but its production acceptance remains blocked; EMP-003's audit
  is reproducible but source resolutions are incomplete. EMP-004/006 are
  blocked and EMP-005/007/008 require independent review.
- Baseline remote CI verified green at `456a77c`:
  https://github.com/Slavov88/volatility-risk-premium/actions/runs/38405901655.
  New branch CI is not yet claimed; draft PR publication will run the existing
  pull-request workflow. PR #1 remains open/draft and unchanged.

### 2026-10-13 — publication and independent CI verification

- Evidence commit: `a30d37b`; branch pushed as `agent/empirical-production`.
  Draft PR #2 targets `agent/autonomous-research`:
  https://github.com/Slavov88/volatility-risk-premium/pull/2.
- GitHub Actions passed at `a30d37b`: **1,634 tests in 7.65 s** plus
  successful compilation, using Python 3.11 and the unchanged dependency lock:
  https://github.com/Slavov88/volatility-risk-premium/actions/runs/38415138496.
- Final local checks reverified all source hashes, sanitized-price redaction,
  audit implementation hash, identical source-audit and archive-inspection
  outputs. Direct subprocess exits were 2 for the rejection audit and 1 for
  the blocked panel builder. No processed origin panel exists.
- PR #1 verified still open/draft on `agent/autonomous-research`. Nothing
  merged into main; no theory/protocol/lock edits. Operational statuses remain
  as above. Next required step is coauthor/source resolution, not inference.

### 2026-10-13 — VIX CLOSE candidate implementation

- Continued clean `agent/empirical-production` at `a124b9a`; fetched remote
  branches and attached existing draft PR #2. No new acquisition of the full
  Yahoo or VIX history. Original acquisition hash/rejection audit reproduced;
  baseline **1,634 passed in 14.28 s**.
- Added distinct proposed CLOSE validation and immutable candidate panel
  construction. It rejects invalid CLOSE/range consistency, duplicates,
  ambiguous dates and provenance errors. Missing predictors and non-XNYS
  provider dates are explicitly excluded, never filled. OPEN failures remain
  visible diagnostics. Original SPX observations remain intact.
- Initial inspection run produced 9,063 candidate origins at
  `data/processed/candidates/a6d85fa6da2bc8c7/`. A date-set construction was
  then optimized without changing retention decisions; replay under the
  final implementation produced the same count at
  `data/processed/candidates/ad54efed0d346f17/`. Both are explicitly unapproved;
  only the final implementation's provenance will be used in the proposal.
- Candidate verification checks original and derived hashes and replays the
  complete manifest/content. Confirmatory loading raises an approval error;
  the existing strict builder rejects both the original failed source and
  a candidate manifest passed as an acquisition.
- Focused candidate/footprint checks: **38 passed in 7.70 s** before two
  additional integration regressions. Full suite **1,674 passed in 17.56 s**;
  compilation and whitespace checks passed before the implementation milestone
  commit. No RVAR/VRP or H1–H5 run.
- Added EMP-010–012 without changing existing task IDs. Next action is
  source-diagnostic evidence and a concrete both-author review proposal.
