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
| EMP-004 | Reproducible interim origin panel | TECHNICALLY COMPLETE / PROVISIONAL | Authorized path 55ce4a2, 9064/9067, two identical builds. Old strict gate still rejects. | Independent acceptance EMP-005. |
| EMP-005 | B: independent freeze review | PENDING EXTERNAL REVIEW | Coauthor reviews exact hashes, quality findings and freeze report. Code/tests cannot provide this approval. | Deliver reviewable freeze report after EMP-004. |
| EMP-006 | Returns and all six forward targets | COMPLETE / PROVISIONAL | RUN-008, 9087 returns; 9064 complete values per six series; full numpy audit; two identical executions. | Coauthor audit before inferential reporting. |
| EMP-007 | D: H1/H2 and diagnostic robustness | PENDING REVIEW GATE | EMP-005 accepted; protocol-defined HAC, calibration and mandatory sensitivities; complete experiment log. | Wait for independent freeze approval. |
| EMP-008 | E: recursive OOS and H3/H4 | PENDING REVIEW GATE | Prior milestones independently validated; locked units, windows and common masks. | Implement only after earlier scientific gates. |
| EMP-009 | H5 and paper reporting | PENDING | Prior validation gates, frozen NBER provenance/crisis dates; independent output audit. | Retain theory/Track A without modification. |
| EMP-010 | Separate CLOSE candidate validation | COMPLETE FOR INSPECTION / UNAPPROVED | Commit `2c820db`; contract `vix-close-candidate/1.0.0`; 9,063 origins; identical replay; 1,674 tests pass. No production targets. Strict path unchanged. | Obtain EMP-012 authorization before any approved promotion path. |
| EMP-011 | Source publication and close-correction investigation | DIAGNOSTICS COMPLETE / SIX DISCREPANCIES UNRESOLVED | Hashed Cboe notices, small FRED VIX publication checks and hypothetical correction footprints; 2019 correction explained. | Coauthors review source assumptions and unresolved-price sensitivity proposal; no replacements. |
| EMP-012 | Both-author CLOSE methodology agreement | AUTHORIZED AS REPORTED | Aleksandar communication 2026-10-13 reports both authors agree; f940a1d dated amendment. No signatures/direct Venelin confirmation. | Freeze acceptance remains separate. |

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

### 2026-10-13 — source investigation and CLOSE review package

- Implementation milestone commit: `2c820db`. Candidate and source-footprint
  modules plus **40** new test cases qualify inspection-only processing.
  Original strict source/panel implementations, theory, protocol and lock
  remain unchanged.
- Final candidate: **9,063/9,067** eligible origins; four missing predictor
  dates (0.044116%). Missing by year: 1991: 1, 1997: 2, 1999: 1. Non-session
  exclusions: 2004: 1, 2022: 5, 2023: 7, 2024: 7, 2025: 8. OOS 4,780/4,780;
  proposed post-2003 calendar year 5,535/5,535; alternate 2003-01-01 boundary
  5,787/5,787; post-2014-10-06 2,827/2,827. These are predictor-eligibility
  counts, not target or hypothesis sample-size claims.
- Acquired three small official Cboe notices under
  `data/raw/2026-10-13T150635Z/` and four small FRED VIXCLS windows under
  `data/raw/2026-10-13T150732Z/`, with verified TLS/hashes. Both archive and
  FRED republication corroborate three missing closes; 1999-12-31 is available
  separately but not stitched. Original full acquisitions were not refreshed.
- Cboe confirms 2004-06-11 full closure; the CSV repeats the previous provider
  close. GTH schedules explain why publication on some U.S. holidays is
  plausible, but exact historical CSV timestamp/source mechanisms remain
  unconfirmed. All 28 non-XNYS rows excluded as origins regardless.
- Replayed blocker diagnostics identically and reran candidate construction/
  verification with identical output hashes. Diagnostic correction footprints
  change no prices or target values. Six Yahoo/FRED disagreements remain
  unresolved; 2019 source explanation still requires a source-choice decision.
- Reviewable proposal: `docs/vix_close_acceptance_proposal.md`. Both author
  sign-offs are pending. It requests CLOSE-specific eligibility, four origin
  exclusions, 28 non-session exclusions, no stitching, preserved SPX and
  explicit post-2003/source-discrepancy decisions. No approval inferred.
- EMP-004 remains blocked for an approved production panel; EMP-006–009
  remain behind their scientific gates. EMP-010 completed only for inspection;
  EMP-012 pending. Next action is explicit both-author methodological review.

### 2026-10-13 — CLOSE proposal publication and passing CI

- Evidence/proposal commit: `58f726d`. PR #2 updated in place with the
  candidate contract, scientific limits, counts and validation; remains draft
  against `agent/autonomous-research`. Nothing merged or force-pushed.
- GitHub Actions succeeded at `58f726d` using the Python 3.11 dependency lock:
  https://github.com/Slavov88/volatility-risk-premium/actions/runs/38420832539.
  Local full suite: **1,674 passed**; compileall src/tests/scripts passed.
- Final review rechecked original source hashes, all candidate hashes,
  sanitized manifest equality, both approval/rejection boundaries and absence
  of an approved verified panel. Candidate and blocker diagnostics replayed
  identically. Original strict implementations, protocol and lock have no diff.
- Both-author methodology authorization remains pending; this concludes
  implementation/inspection, not an accepted empirical freeze. After approval,
  record the authorized amendment, build the approved freeze twice, then
  construct locked targets; H1/H2 still require independent freeze acceptance.

### 2026-10-13 — communicated methodology authorization

- EMP-012: AUTHORIZED FOR IMPLEMENTATION, both-author agreement as reported
  by Aleksandar on 2026-10-13; no independent signatures or freeze acceptance.
- Permanent amendment `2026-10-13-interim-vix-close/1.0.0` recorded before
  empirical computations. Authorizes one archive-verified CLOSE insertion,
  three exclusions, existing CLOSE eligibility, canonical Yahoo and all-seven
  discrepancy sensitivity; post-2003 starts 2004-01-01.
- EMP-004/006 may proceed through the separate interim path. EMP-005 remains
  pending external independent review; EMP-007 inference remains gated.
- Cboe inquiry SENT — AWAITING CBOE RESPONSE (author report only).

### 2026-10-13 archival cell verification

- Methodology milestone committed as f940a1d before target computations.
- Original XLS hash verified; OHLC A2528 serial 36525 (1999-12-31), E2528
  numeric CLOSE 24.64 percentage points. HIGH/LOW contains CLOSE. FRED
  Cboe-sourced republication corroborates 24.64.
- Narrow verifier added; 12 focused regressions passed. No targets run yet.
- Corrected encoding of appended authorization text; decisions unchanged.

### 2026-10-13 authorized interim builder implementation

- Archival verifier milestone: 80b78df. Added separate versioned builder,
  exact source-manifest binding, committed-code binding, authorization replay,
  source/derived hash verification and explicit independent-review rejection.
- Focused archive/interim/candidate/strict-builder suite: 64 passed in 8.04 s.
  The strict source gate and historical candidate remain unchanged.
- Production double-build follows the committed implementation; no panel
  count or target result claimed yet.

### 2026-10-13 interim freeze replay and target implementation

- Interim builder commit 55ce4a2: two actual builds independently replayed
  sources and produced the same immutable manifest/panel at
  data/processed/interim/40113d6646b0e7b8/. EMP-004 technically complete via
  the authorized interim path; old strict gate still rejects.
- Coverage computed from locked calendar: full 9064/9067, OOS 4780/4780,
  post-2003 (2004-01-01) 5535/5535, post-2014 2827/2827. Missing exactly
  1991-03-01, 1997-01-31, 1997-11-26. All 9088 SPX rows retained.
- Added six-target execution, all-origin independent numpy audit and isolated
  individual/joint alternate-close sensitivity. Unit regressions passed;
  production execution follows the target implementation commit.
- EMP-005 remains PENDING independent acceptance; EMP-006 implementation
  ready, actual execution not claimed yet; H1/H2 inference not executed.

### 2026-10-13 actual provisional targets and reproducibility

- Target commit c53bb9c: full source replay, 9087 SPX returns and 9064 complete
  values in each of six target series. Independent all-origin numpy audit
  passed; largest variance error 2.220446049250313e-16. Two full executions
  produced identical bytes/hashes, including all-seven CC sensitivities.
- EMP-004 and EMP-006 technically complete / PROVISIONAL. EMP-005 independent
  acceptance is pending. H1/H2, GARCH/OOS and H5 results not executed.
- Reviewer-ready freeze report and sanitized hashed manifests updated. Raw
  archives, strict gate and prior candidate preserved and actually rechecked.
- Provisional descriptions: primary mean VRP_X 0.011348914 annualized decimal
  variance; positive fraction 0.859995587. No significance/mechanism claim.
- Next: independent freeze review, then protocol H1/H2; recursive GARCH/OOS
  H3/H4 and frozen-regime H5 follow. Cboe response/source limitations remain
  explicitly pending and do not block authorized target processing.

- Final local suite: 1717 passed in 16.46 s; compileall src/tests/scripts and
  diff check passed. No restricted price CSV staged; only source, tests,
  sanitized provenance/aggregate JSON and research documentation.

- Evidence milestone 6669b8e preserves actual freeze/target manifests and
  aggregate outputs. Git attributes pin tracked manifest JSON to LF so
  authorization and metadata byte hashes survive Windows/Linux checkouts;
  scientific source fingerprints already normalize checkout line endings.

### 2026-10-13 publication and CI acceptance of implementation

- Pushed through 7842af4; draft PR #2 updated in place, still targets
  agent/autonomous-research. PR #1 remains open/draft and unchanged; main
  untouched, no merge/force push.
- GitHub Actions succeeded for 7842af4 in pinned Python 3.11 environment:
  https://github.com/Slavov88/volatility-risk-premium/actions/runs/38439995535
  Test and compile steps passed. Local full suite: 1717 passed in 16.46 s.
- Final Git tree clean before this journal entry; source/target files remain
  ignored. Independent scientific freeze acceptance and Cboe response are
  pending. Implementation CI success does not supply coauthor approval.

### 2026-10-13 provisional H1-H5 execution authorization

Aleksandar Slavov explicitly authorized H1-H5 statistical execution before
Venelin Mirchev's independent freeze review. That review remains PENDING;
results become visible before review and must be labelled PROVISIONAL -
PENDING INDEPENDENT COAUTHOR REVIEW. This removes the prior operational
inference restriction, not the strict acquisition gate or scientific review.
Specifications stay protocol 1.1.0 plus the authorized interim amendment.
No statistical method may change to improve observed results. A reviewer
rejection requires documented revision, new frozen dataset/version and full
re-execution, preserving original outputs. Use only the existing 9064-origin
freeze and canonical SPX, with its three missing VIX origins unchanged.

H1/H2: IMPLEMENTING. H3/H4: NOT STARTED. H5: NOT STARTED.

### H1-H2 computed / provisional; recursive GARCH implementation

- Authorization 7522a81 precedes results. Inference commit c896f12 executed
  all locked H1/H2 robustness grids; exact calendar overlap L0=21. Independent
  numpy OLS/score-sandwich, mean and joint Wald checks passed throughout.
- Outputs outputs/empirical_h1_h5/v1/h1_h2.json; result review remains pending.
- Recursive GARCH config fixed before fits: cold default starts at each origin,
  maxiter=1000, ftol=1e-9; no retries/specification changes on failure; percentage
  returns and decimal variance conversion. Three pre-specified variants:
  normal expanding, Student-t expanding, normal rolling five calendar years.
  Both 30c/21t forecasts derive from each same recursive fit. All 4780 origins
  scheduled per variant. Date-only residual diagnostic anchors: first/last
  eligible origin of each year. Return diagnostics precede fitting.

### Recursive forecasting launched and verified chronological checkpoints

- GARCH implementation 75de041; synthetic recurrence test initially failed
  because ARCH forecasts recompute final-residual backcasts while fitted
  conditional volatility retains the estimation backcast. Fixed the oracle
  in 9aeb3b5 before production fitting; all four GARCH tests then passed.
  Model specification/configuration did not change.
- Gaussian expanding and Gaussian rolling each completed 4780/4780 fits
  with zero failures. Student-t expanding RUNNING; partial coverage is not
  treated as a full-period H3 result. All variants use immutable verified
  checkpoint rows and independent daily forecast recurrence checks.
- H3/H4 IMPLEMENTING; three new forecast-analysis tests passed, including
  exact common-mask policy and refusal of incomplete coverage.
- NBER chronology source/432 monthly flags frozen in cade451 before any H5
  outcome. H5 IMPLEMENTING; two monthly parsing/mapping tests passed.
