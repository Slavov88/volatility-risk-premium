# Scientific execution log

Protocol version **1.1.0** throughout. Acquisition quality diagnostics are
scientific data-validation computations, not empirical hypothesis results.
No H1–H5 test or premium/forecast target was executed. Entries below record the
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
