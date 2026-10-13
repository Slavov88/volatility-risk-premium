# Scientific execution log

Protocol version **1.1.0** throughout. Acquisition quality diagnostics are
scientific data-validation computations, not empirical hypothesis results.
No H1–H5 test or premium/forecast target was executed in RUN-001–005. RUN-008 later records authorized provisional targets. Initial entries below record the
first session's commands retrospectively from actual logs/artifacts; no
specification was selected from a favorable result.

## RUN-001 — 2026-10-13: canonical production acquisition

Purpose: acquire full frozen index outcomes and VIX predictors, test source
quality, and independently validate index closes. Base code `456a77c`;
operational tracker commit `8256a34`. Retrieval time was approximately
14:24:30 UTC (17:24:30 Europe/Sofia). Python 3.11.5, all 51
`requirements-dev.lock` entries verified exactly; library versions are also
in `data/manifests/2026-10-13_production_quality_audit.json` and local
`outputs/environment.json`. Existing production CLIs run unchanged:

```powershell
.venv/Scripts/vrp-download-spx.exe --start-date 1990-01-02 --end-exclusive 2026-02-03 --validate-fred
.venv/Scripts/vrp-download-vix.exe --start-date 1990-01-02 --end-exclusive 2026-01-01
```

- Immutable local inputs/output snapshots:
  `data/raw/2026-10-13T142430Z/yahoo/gspc_ohlc_unadjusted.csv`,
  `cboe/VIX_History.csv`, `cboe/vix_frozen_normalized.csv`,
  `fred/sp500_close.csv`, and source manifests in that acquisition directory.
- SPX SHA-256:
  `dd7838e8470a5056e99b82dba808bf9df226ced891e0826e4425d55a8d0f544e`.
- Raw VIX SHA-256:
  `965f14ae8d58079536b5491219b647e6385592be2c466e6ac849f6ace0bbe1f7`.
- Normalized VIX SHA-256:
  `10b2faa178208d7553f96597b40e63807668af77b3f8242f73afb8b8a40b0f94`.
- FRED SHA-256:
  `4590145f9ed88e20b41bc1325fa7c538e7532e8b1289dac4b801b216c9bd77e6`.
- Validation state: Yahoo accepted; VIX rejected; FRED available, seven
  above-tolerance discrepancies. Logs: `outputs/spx_acquisition.log` and
  `outputs/vix_acquisition.log`. Exact original-manifest hashes appear in
  RUN-002's report. Default verified TLS used; no override requested.
- Interpretation limits: passing Yahoo schema/coverage is not scientific
  approval; FRED is a validation overlay, never a replacement series.

## RUN-002 — 2026-10-13: fail-closed panel gate and source audit

Purpose: independently replay hashes, source normalization, quality reports
and FRED comparison; diagnose rejection without bypassing it.

```powershell
.venv/Scripts/vrp-build-verified-panel.exe --raw-root data/raw --spx-manifest 2026-10-13T142430Z/gspc_manifest.json --vix-manifest 2026-10-13T142430Z/vix_manifest.json --processed-root data/processed
.venv/Scripts/python.exe -m vrp.acquisition_audit --raw-root data/raw --spx-manifest 2026-10-13T142430Z/gspc_manifest.json --vix-manifest 2026-10-13T142430Z/vix_manifest.json --report outputs/production_quality_audit.json
```

Inputs are RUN-001's exact artifacts. Original SPX manifest SHA-256:
`29bb559550a8470b1b8c034cf752b8bd3919b2585069ed27d252ddc2bb6873a5`;
VIX manifest SHA-256:
`68c11d8fe5a9f454761a898b1bd6bdee499c7a55b30ce370ec28549fc8805d92`.

Panel builder rejected with `PanelProvenanceError: VIX: acquisition not accepted`;
no panel output. Audit status `BLOCKED_VIX_QUALITY`, its direct Python exit
code is 2. Audit repeated with identical output SHA-256:
`a3cab6ddf0399d436fab797616cb145ffcc9e27cc001edf2c5958028ba78943f`.
Sanitized identical report at
`data/manifests/2026-10-13_production_quality_audit.json`.

Parameters: locked XNYS 4.13.2, exact acquisition windows, FRED one-cent
tolerance, original data retained without corrections. Diagnostic intersection
9,063 dates is **not** an accepted origin panel. No 2026 origin admitted.
Limit: no approved freeze, realized target or inference follows from this audit.

## RUN-003 — 2026-10-13: auxiliary official Cboe source investigation

Purpose: determine whether another currently linked official source repairs
the missing-date diagnosis, and investigate a material index discrepancy.
All auxiliary downloads used `vrp.data.fetch_bytes` (default verified TLS)
and `write_immutable`; files remain in RUN-001's local `cboe/` directory.
The three source URLs are recorded in
`data/manifests/2026-10-13_cboe_archive_inspection.json`.

Reacquire the auxiliary artifacts with the following equivalent command:

```powershell
@'
from pathlib import Path
from vrp.data import fetch_bytes, write_immutable
root = Path('data/raw/2026-10-13T142430Z/cboe')
sources = {
 'linked_VIX_History.csv': 'https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv',
 'vixarchive.xls': 'https://cdn.cboe.com/resources/us/indices/vixarchive.xls',
 'spx_2019_correction.pdf': 'https://cdn.cboe.com/resources/release_notes/2019/Corrected-Closing-Settlement-Prices-for-Certain-SP-Indices-II.pdf',
}
for name, url in sources.items():
    print(name, write_immutable(root / name, fetch_bytes(url)))
'@ | .venv/Scripts/python.exe -
uv pip install --system-certs --target outputs/archive_inspection xlrd==2.0.2
.venv/Scripts/python.exe scripts/inspect_cboe_archive.py --acquisition-directory data/raw/2026-10-13T142430Z --parser-path outputs/archive_inspection --report data/manifests/2026-10-13_cboe_archive_inspection.json
```

Live provider bytes can change; never overwrite a differing immutable file.
For later acquisitions, use a fresh timestamp directory and compare hashes.
The isolated XLS parser is an inspection tool, not a new locked empirical
dependency or production input path.

- XLS SHA-256:
  `9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566`.
- Correction PDF SHA-256:
  `176f66347df23150f7460c42d5a7fbe87fc6c5bcf27f0a6bd9d1af63f2069744`.
- Linked current CSV is byte-identical to RUN-001's raw VIX.
- Archive: 3,532 rows; 3,528 overlapping closes agree; only one missing
  current-CSV date has a usable archived close. No stitching performed.
- Validation correction: preliminary `pd.notna('n/a')` logic wrongly counted
  a textual placeholder as a finite close. Invalid preliminary report retained
  only at `outputs/archive_inspection_invalid_v1.json`; corrected committed
  report requires successful finite numeric conversion. Four synthetic
  placeholder/nonfinite tests passed. The corrected script reproduced its
  report successfully.
- Interpretation: the [Cboe 2019 correction notice](https://cdn.cboe.com/resources/release_notes/2019/Corrected-Closing-Settlement-Prices-for-Certain-SP-Indices-II.pdf)
  documents a recalculated 2019-08-12 closing settlement value supporting
  FRED's side of that discrepancy. This does not authorize overwriting Yahoo
  OHLC; six other differences remain unexplained. Independent review required.

## Engineering validation accompanying RUN-002/003

Implementation commit `b191daf`. Baseline: 1,620 passed in 24.16 s;
new focused checks: 14 passed in 5.70 s; final full suite: **1,634 passed
in 14.02 s**. Commands: `.venv/Scripts/python.exe -m pytest -q`,
`.venv/Scripts/python.exe -m compileall src tests scripts`, `git diff --check`.
Compilation and whitespace checks passed. These validate implementation and
rejection behavior; they do not approve the production dataset scientifically.

## RUN-004 — 2026-10-13: immutable source reuse and CLOSE candidate

Purpose: exercise the proposed distinct CLOSE contract without changing
original source acceptance or generating targets. Starting commit `a124b9a`;
protocol 1.1.0 unchanged. Original RUN-001 source and manifest hashes were
independently reverified by repeating RUN-002's audit against the original
report; no full Yahoo/VIX reacquisition. Baseline 1,634 tests passed in 14.28 s.

```powershell
.venv/Scripts/python.exe -m vrp.vix_close_candidate --raw-root data/raw --spx-manifest 2026-10-13T142430Z/gspc_manifest.json --vix-manifest 2026-10-13T142430Z/vix_manifest.json --processed-root data/processed
```

Parameters: proposed transformation `vix-close-candidate/1.0.0`, locked XNYS
4.13.2/window, no fills or source stitching, reject invalid CLOSE/available
range bounds, preserve OPEN diagnostics, drop missing VIX origins only.
All 9,088 SPX source rows preserved, including 21 outcome-support rows.

Initial development execution: candidate directory `a6d85fa6da2bc8c7`;
9,063 origins. After replacing repeated date-set construction with a cached
set, the same candidate was generated and verified under the final source
hash at `data/processed/candidates/ad54efed0d346f17/`. The manifest pins the
implementation SHA-256 as well as all original source hashes. Both artifacts
are explicitly unapproved; the earlier development artifact is not used for
review or later production. No retention rule changed during optimization.

Final derived artifact hashes:

- CLOSE CSV: `9f8790dcafd695b9d59a6cbb97189a3490ef7255c4cdf82a715ec1f945138f60`.
- Candidate origin CSV: `3a0f110988728dd82e571c318749aa852b0d32dc2f915bd9cbdbcecf11261384`.
- Manifest: `f346c8b0bb1f68270243f87f523c799ea5565812036d9e029f18b2f32c2c84e9`.
- Sanitized metadata copy: `data/manifests/2026-10-13_vix_close_candidate.json`.

Validation: candidate CLOSE eligibility passed; scientific approval
**CANDIDATE_UNAPPROVED**, confirmatory execution prohibited. Available/expected
origins: full 9,063/9,067, OOS 4,780/4,780, proposed post-2003-calendar-year
5,535/5,535, post-2014-10-06 2,827/2,827. Alternate 2003-01-01 boundary has
5,787/5,787; reporting both is date-coverage diagnosis, not a new inferential
specification. Both authors must clarify the underspecified post-2003 boundary.

Focused candidate/footprint tests: 38 passed in 7.70 s; with two additional
integration regressions the full suite passed **1,674 tests in 17.56 s**.
Compilation and git diff --check passed. Test development first found one
incorrect expected error message: a candidate outside the acquisition root
was rejected by the path guard before schema validation. The regression now
also copies synthetic candidate metadata into the test root and verifies
strict schema rejection. No production guard was changed.

## RUN-005 — 2026-10-13: publication evidence and correction footprints

Purpose: distinguish source publication from origin eligibility; investigate
missing predictor dates and the scope of hypothetical close corrections.
Only new small supporting files were acquired, with default verified TLS.
Original raw files remain immutable. No CLOSE replacement or RVAR/VRP run.

- Three official Cboe notices acquired into `data/raw/2026-10-13T150635Z/`.
  Exact URLs/hashes/byte counts and retrieval time are recorded in
  `notice_manifest.json`, identically copied to
  `data/manifests/2026-10-13_vix_publication_notices.json`.
- Four small FRED `VIXCLS` windows acquired into
  `data/raw/2026-10-13T150732Z/`: 1991-02-28–1991-03-04,
  1997-01-30–1997-02-03, 1997-11-25–1997-11-28 and
  1999-12-30–2000-01-03. Each used `fetch_bytes` then `write_immutable`;
  request URL, hash and actual availability are in
  `fred_vix_missing_dates_manifest.json` and its sanitized copy
  `data/manifests/2026-10-13_fred_vix_missing_dates.json`.
- FRED identifies Cboe as supplier of VIXCLS. This is corroborating publication
  evidence, not an independent calculation or approved replacement source.
  Only 1999-12-31 has a finite positive close among the four investigated
  dates; the other three have missing placeholders. No values stitched.

Supporting acquisitions are reproducible using each manifest's `source_url`
with `vrp.data.fetch_bytes` and `write_immutable` at its `relative_path`.
Use a fresh timestamp for changed live provider bytes, never overwrite old
acquisitions. No auxiliary download is required to replay the following run:

```powershell
.venv/Scripts/python.exe scripts/diagnose_source_blockers.py --raw-root data/raw --processed-root data/processed --candidate-manifest data/processed/candidates/ad54efed0d346f17/candidate_close_manifest.json --notice-manifest 2026-10-13T150635Z/notice_manifest.json --fred-vix-manifest 2026-10-13T150732Z/fred_vix_missing_dates_manifest.json --report data/manifests/2026-10-13_source_blocker_diagnostics.json
```

Output SHA-256:
`face1e09ac272f8496f6ad5dbad8192a7a8ed4e192fcf28f44c1338aa8eaed92`.
All input hashes are rechecked. Parameters: single discrepancy dates tested
one at a time; hypothetical reference is the local FRED SP500 observation;
original Yahoo remains canonical. Only signed changes `+epsilon,-epsilon`
to the two adjacent log returns and affected origin-date sets are calculated.
No baseline/corrected RVAR, premium, forecast, p-value or crisis output.

2021-08-11's possible correction reaches 23 primary-30c origin windows;
2019-08-12 reaches 21; each reaches 22 fixed-21 windows. These footprint
counts indicate overlap propagation, not evidence favoring a correction.
Adjacent hypothetical corrections must combine signed changes before
squaring. Only the 2019 discrepancy has independently explained provenance;
six other differences remain unresolved and all correction rules need review.

The 2004 non-session observation repeats the previous provider close, despite
the official closure notice. Holiday GTH trading is documented for 2022-05-30
and 2025-01-09. The precise CSV timestamp/source mechanism remains unconfirmed;
the other holiday dates have a plausible GTH explanation, not individual
publication attestation. Every non-XNYS row is excluded from candidate origins.

Reproducibility check after the proposal was drafted: reran RUN-005's diagnostic
command and RUN-004's candidate command against existing immutable artifacts.
Both succeeded and reproduced the identical manifests/output hashes above.
Confirmatory eligibility remains rejected; repeated success is inspection
repeatability, not methodological approval.

Implementation `2c820db` and evidence/proposal `58f726d` were published on
draft PR #2. [GitHub Actions passed at the evidence head](https://github.com/Slavov88/volatility-risk-premium/actions/runs/38420832539)
on locked Python 3.11. This external engineering check does not supply either
author's methodological sign-off or independent data-freeze acceptance.

## RUN-006 — 2026-10-13: pre-computation methodology authorization

Before any actual production return/target/VRP computation, record amendment
`2026-10-13-interim-vix-close/1.0.0` to protocol 1.1.0. Both authors' agreement
is reported by Aleksandar on 2026-10-13; no direct Venelin confirmation or
independent freeze acceptance. RUN-001–005 contain source/eligibility
computations only, not H1–H5 results. The fixed post-2003 boundary and seven
individual/joint alternate-close sensitivity cases precede outcomes.
Cboe inquiry is SENT — AWAITING CBOE RESPONSE as reported; no email metadata
invented. Technical source verification follows this first committed milestone.

## RUN-007 — 2026-10-13: archive-verified interim panel and repeated freeze

Authorization milestone `f940a1d`; archive-verifier milestone `80b78df`;
freeze implementation `55ce4a23b44188ae21c8343005c6104b9a8a5d21`. Original inputs
are RUN-001's unchanged SPX/VIX bytes/manifests and RUN-003's original XLS
(hash `9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566`); FRED VIXCLS
corroboration from RUN-005. Numeric OHLC!E2528 = 24.64, A2528 = 36525 under
Excel datemode 0, date 1999-12-31. Isolated parser xlrd==2.0.2 reused.

```powershell
.venv/Scripts/python.exe -m vrp.interim_panel --raw-root data/raw --spx-manifest 2026-10-13T142430Z/gspc_manifest.json --vix-manifest 2026-10-13T142430Z/vix_manifest.json --processed-root data/processed --authorization data/manifests/2026-10-13_interim_authorization.json --parser-path outputs/archive_inspection --code-commit 55ce4a23b44188ae21c8343005c6104b9a8a5d21
```

Executed twice, replaying all sources and provenance independently each time.
Same directory `data/processed/interim/40113d6646b0e7b8` and identical output bytes.
One mistyped commit argument failed the committed-code gate and wrote no
artifact; the exact commit above succeeded. Full coverage 9064/9067; OOS
4780/4780; from 2004-01-01 5535/5535; from 2014-10-06 2827/2827. Missing
only 1991-03-01, 1997-01-31, 1997-11-26. All 9088 SPX rows preserved.
Exact inputs/outputs, hashes, cells, warnings and review states in
`data/manifests/2026-10-13_interim_freeze.json` and freeze report.
Independent acceptance PENDING; technical replay passed. Original strict
builder still actually rejects with VIX acquisition not accepted. Historical
9063-row unapproved candidate independently reverified after this build.

## RUN-008 — 2026-10-13: actual six-target execution and predefined sensitivity

Target implementation `c53bb9c65dd5b7521ebe80070103a525d98b373c`;
freeze manifest SHA-256 `1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4`. Python 3.11.5; unchanged
requirements-dev.lock; pinned software versions and lock/code hashes in
`data/manifests/2026-10-13_provisional_targets.json`.

```powershell
.venv/Scripts/python.exe scripts/run_interim_targets.py --freeze-manifest data/processed/interim/40113d6646b0e7b8/interim_manifest.json --authorization data/manifests/2026-10-13_interim_authorization.json --parser-path outputs/archive_inspection --code-commit c53bb9c65dd5b7521ebe80070103a525d98b373c
```

Initial target CLI at c21c524 rejected a workspace-relative freeze path due
to duplicate root joining, before returns or targets. c53bb9c resolves paths
at the CLI boundary; a regression now checks this behavior. Actual execution
above ran twice with identical bytes/hashes for daily, six-target, audit,
descriptive and sensitivity outputs under `data/processed/interim/40113d6646b0e7b8/targets/bd7a172882ded86f`.
Parameters: all canonical SPX observations, exact forward XNYS sessions,
365/30 and 252/21, implied-minus-realized, decimal units, no imputation,
fixed 2004-01-01 and 2014-10-06 subsets; no model estimation/seed dependence.

9087 actual dated log returns; 9064 complete origins in all six target series
(54384 audited target values), no shortened or missing targets. Independent
numpy oracle max absolute variance error 2.220446049250313e-16. Descriptive
statistics use locked sample SD, bias-corrected Fisher skew/excess kurtosis
and linear quantiles; full statistics preserved. FRED SP500 SHA-256
4590145f9ed88e20b41bc1325fa7c538e7532e8b1289dac4b801b216c9bd77e6
supplies all seven individual/joint alternate-close CC scenarios, isolated
from canonical Yahoo. Source prices are not committed. Joint corrections
combine returns before squaring; no significance-driven source selection.

All analytical results are PROVISIONAL / NOT INDEPENDENTLY ACCEPTED.
No H1-H5 inference/GARCH/forecast ranking run or manuscript claim. Technical
checks are not independent scientific acceptance. Reviewable results and
limitations are summarized in the updated production data-freeze report.

Validation after all target/sensitivity and CLI/cell regressions: **1717 tests
passed in 16.46 s**. `python -m compileall src tests scripts` and
`git diff --check` passed. Actual post-run checks independently reverified
all original/derived hashes, single insertion, source row preservation,
old 9063-row candidate, original strict rejection and independent-review
rejection. Remote CI status will be recorded after publication.

Publication verification: PR #2 updated and remains draft against
agent/autonomous-research. GitHub Actions at 7842af4 passed tests/compilation:
https://github.com/Slavov88/volatility-risk-premium/actions/runs/38439995535.
Market-data-dependent source/target replay was executed locally and is not
claimed as a GitHub test using redistributable production inputs.

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

## RUN-009 - 2026-10-13: authorized provisional H1-H5 execution

Aleksandar authorized execution before Venelin's independent freeze review;
7522a81 recorded authorization before statistical outcomes. Independent
review remains PENDING, no signatures/acceptance supplied. Results become
visible before that review. Protocol 1.1.0 and interim amendment unchanged;
no new SPX/VIX dataset, source choice, exclusions or estimation sample.

Python 3.11.5; arch 8.0.0, statsmodels 0.15.0, scipy 1.17.1, numpy 2.4.6,
pandas 2.3.3, XNYS exchange-calendars 4.13.2; dependency lock unchanged.
GARCH processes use OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1,
MKL_NUM_THREADS=1, seed 42. Cold deterministic default starts, maxiter=1000,
ftol=1e-9; no retries or model replacement on failure. Three variants:
normal expanding, Student-t expanding, normal rolling five calendar years.
Percent fit returns and /10000 decimal variance conversion. Both horizons
derive from each recursive fit. Source/target hashes checked before every run.

### Exact execution commands

```powershell
.venv/Scripts/python.exe -m vrp.provisional_analysis --parser-path outputs/archive_inspection --code-commit c896f1245eecfc2341a2b8a975f5dde76979cda1 --output outputs/empirical_h1_h5/v1/h1_h2.json
.venv/Scripts/python.exe -m vrp.recursive_garch --variant normal_expanding --parser-path outputs/archive_inspection --code-commit 9aeb3b5712fc783d0016b2129aee6b3da62a3fa4 --output-root outputs/empirical_h1_h5/v1/garch
.venv/Scripts/python.exe -m vrp.recursive_garch --variant t_expanding --parser-path outputs/archive_inspection --code-commit 9aeb3b5712fc783d0016b2129aee6b3da62a3fa4 --output-root outputs/empirical_h1_h5/v1/garch
.venv/Scripts/python.exe -m vrp.recursive_garch --variant normal_rolling5y --parser-path outputs/archive_inspection --code-commit 9aeb3b5712fc783d0016b2129aee6b3da62a3fa4 --output-root outputs/empirical_h1_h5/v1/garch
.venv/Scripts/python.exe -m vrp.forecast_analysis --parser-path outputs/archive_inspection --code-commit cade4518bf2761b41f2558ef263bde4bbf1dfd71 --garch-root outputs/empirical_h1_h5/v1/garch --output outputs/empirical_h1_h5/v1/h3_h4.json
.venv/Scripts/python.exe -m vrp.regime_analysis --parser-path outputs/archive_inspection --code-commit cade4518bf2761b41f2558ef263bde4bbf1dfd71 --chronology data/manifests/2026-10-13_nber_chronology.json --forecasts outputs/empirical_h1_h5/v1/h3_h4.json --output outputs/empirical_h1_h5/v1/h5.json
.venv/Scripts/python.exe scripts/audit_empirical_execution.py --parser-path outputs/archive_inspection --root outputs/empirical_h1_h5/v1
.venv/Scripts/python.exe scripts/report_empirical_results.py --root outputs/empirical_h1_h5/v1 --parser-path outputs/archive_inspection
```

H1/H2 and H3/H4/H5 executed twice with identical hashes. Checkpoint resume
revalidated/reused all 4780 records per model, with no reduced-refit
approximation. Fifteen date-fixed fresh fits (first/final origin and first
origins of 2008/2020/2022 per variant) exactly reproduced parameters,
forecasts, warnings and residual diagnostics. Full set-intersection audit
independently confirms L0=21. All 14340 fits converged; zero forecast failures.

Input freeze: `1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4`; target manifest: `00532571aad5f8d9c43231933429fe6facbf7687a6332231ac8b7ad0ff73ccd9`.

| Result artifact | SHA-256 |
|---|---|
| execution_audit.json | `a37a4b74db24de665e0d1e109f237367a8f2c0110ada5d4a0ea8e106f38caeb6` |
| h1_h2.json | `6b07e43199d3ffd723e42c8ed3bf497c800421f79a6c56b33b95d9e9d67d5a25` |
| h3_h4.json | `03afa02ed0e6087ab507fcde105a066b591b74b10a9826cce553ce4310d5a1a5` |
| h5.json | `b2945442db51261cc5fde5555eab806e8413b35dc26a5292cfe6d80f49937b90` |

H1/H2 include all locked bandwidths, horizons, estimators, fixed subsets,
non-overlap and secondary VOLGAP. H3/H4 include all three model variants,
both horizons, common masks, paired squared-error and QLIKE HAC plus exactly
two Holm-adjusted secondary contrasts. H5 includes source-frozen monthly
NBER mapping, estimators/horizons/bandwidths/subsets, secondary gaps,
non-overlap and fixed-year cases. Report estimates are generated exclusively
from result JSON; full numerical precision remains in immutable outputs.

NBER HTML downloaded with default verified TLS at the manifest timestamp;
web-tool request returned 403 but direct official download succeeded.
Original HTML SHA-256:
99401340ae9b97310803cdcd0db0731ba4b4739f5425a83c370d268e3fa5795d.
Snapshot/monthly parsing committed at cade451 before H5 outcomes; 432 monthly
flags, 36 recession months, peak excluded/trough included. Case years unchanged.

Initial synthetic GARCH oracle failed before production due to forecast
versus fit backcast distinction; fixed in 9aeb3b5 without model changes.
A mistyped replay commit was rejected before analysis; correct commit
replayed identically. Initial fresh-fit audit compared integer lag keys to
JSON string keys; canonical JSON normalization fixed representation without
numeric changes, then 15 fresh fits matched. Plot generation initially used
unsupported auto_ylim spelling; corrected to installed auto_ylims. Final
publication/v2 preserves the preliminary visual version locally.

Near-unit persistence and standardized residual diagnostics remain explicit.
Residual tests cover 38 date-selected first/final-year anchors per variant,
not every fit. Return JB/Ljung-Box/ARCH-LM and descriptive leverage diagnostics
preceded fits. Numerical p=0 underflow labelled. No trimming, outcome-selected
specification/source/window changes, theoretical conditional-premium claim,
causality/efficiency claim or manuscript conclusion. Scientific review pending.
