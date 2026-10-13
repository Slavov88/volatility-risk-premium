# Proposed VIX CLOSE acceptance contract — both authors' approval required

Date: **2026-10-13**. Authoritative protocol remains **1.1.0**.
Proposed transformation: **vix-close-candidate/1.0.0**.
Status: **CANDIDATE_UNAPPROVED**. Implementation commit: **2c820db**.
No production RVAR/VRP, H1–H5, GARCH, crisis result or manuscript conclusion
has been generated to justify this proposal.

## Decision requested

Authorize a distinct CLOSE-specific eligibility path for official immutable
Cboe VIX, retaining original finite positive eligible closes, preserving
available range checks, excluding all non-XNYS observations, and dropping
only four origins with missing VIX. Do not stitch the archived 1999-12-31
close or replace Yahoo SPX prices. Keep the full SPX outcome-support series.
This proposal is a reviewable methodological amendment, not a granted approval.

Approval must separately clarify the post-2003 boundary and how unresolved
Yahoo/FRED disagreements will be handled before scientific freeze acceptance.
The proposed literal post-2003-calendar-year start is 2004-01-01; the current
protocol does not specify an exact date. The alternate 2003-01-01 coverage is
shown for review only. Neither has been selected using outcomes.

## Original contract and actual defects

`vix_quality_report()` requires complete XNYS coverage, finite positive OHLC,
unique dates, no unexpected dates and internally consistent OHLC. The first
production snapshot was correctly rejected: 9,091 observed rows versus
9,067 expected origins, with four missing dates, 28 non-XNYS observations and
47 OPEN-only ordering failures. The original acquisition manifest remains
rejected and immutable; `processed_panel.py` and its strict production path
are unchanged.

All **9,091 frozen CLOSE values are finite and positive**. None violates its
available HIGH/LOW bounds, and the source has no duplicate retained dates.
Twenty OPEN values exceed HIGH; 27 fall below LOW. The new candidate also
checks the original raw date schema/duplicates and replays normalization,
strict-quality metadata and hashes instead of assuming CLOSE validity merely
because OPEN does not enter the predictor formula.

## Scientific rationale and independent corroboration

The research object's implied side is `IVOL = CLOSE/100`, `IVAR = IVOL**2`.
VIX OPEN is not a substitute predictor or target input. Separating CLOSE
validation from ancillary OHLC diagnostics therefore matches the measured
object, while range checks, immutable provenance and source cross-checks
remain safeguards. It does not prove that every published CLOSE is correct.

The separately published official 1990–2003 XLS archive agrees on all 3,528
overlapping finite closes. The currently linked official CSV endpoint is
byte-identical to the acquired history and is **not an independent calculation**.
All auxiliary hashes are in committed sanitized metadata and reverified locally.

The XLS has no usable value for 1991-03-01, no rows for the two 1997 dates,
and a finite close for 1999-12-31. Four small [FRED VIXCLS publication checks](https://fred.stlouisfed.org/series/VIXCLS),
whose source is Cboe, corroborate missing values on the first three dates and
a finite close on the fourth. FRED republishes Cboe; it is not an independent
VIX calculation and is not an authorized replacement. No stitching occurred.

## Provider publication versus origin eligibility

All 28 non-XNYS observations are preserved in the original source and listed
in the derived provenance. They never become candidate predictors or dates
for synthetic SPX returns.

- **2004-06-11:** [Cboe circular RG04-69](https://cdn.cboe.com/resources/regulation/circulars/regulatory/RG04-69.pdf)
  confirms full closure for the Reagan mourning day. The CSV CLOSE repeats
  the previous provider row. Its publication mechanism remains unexplained;
  it is excluded under XNYS regardless.
- **2022-05-30:** [Cboe's Memorial Day notice](https://cdn.cboe.com/resources/schedule_update/2022/Cboe-Holiday-Reminder-Closed-on-Monday-May-30-2022.pdf)
  documents SPX/VIX GTH activity on a day without RTH.
- **2025-01-09:** [Cboe's Carter mourning-day notice](https://cdn.cboe.com/resources/schedule_update/2025/Update-Cboe-to-Observe-National-Day-of-Mourning-on-Thursday-January-9-2025.pdf)
  documents GTH while equities and RTH are closed.
- The other 25 dates follow a U.S. holiday pattern. A GTH explanation is
  plausible but was not individually established for each CSV observation.
  Even the two documented schedules do not bind their CSV CLOSE to an exact
  timestamp. No date was shifted to another session.

## Proposed deterministic validation and transformation

1. Verify official Cboe identity, original raw/normalized SHA-256, frozen
   window, original manifest hash, TLS configuration and calendar version.
   Reproduce the original normalization and rejected strict-quality report.
2. Reject ambiguous/malformed dates and all duplicate dates, including
   identical duplicate closes. Do not infer a timezone correction or average
   conflicting values.
3. Define retained dates by the locked XNYS sample through 2025-12-31.
   Exclude non-session/out-of-window rows explicitly. Do not relabel these
   provider rows as price errors merely because they are origin-ineligible.
4. Every retained CLOSE must be finite and strictly positive. Every available
   finite positive HIGH/LOW bound must contain CLOSE, and two available bounds
   must be ordered. An inconsistent bound is fatal. Unavailable auxiliary
   bounds are reported; actual retained data have no unavailable bounds.
5. OPEN ordering defects remain date-labelled source warnings. OPEN/HIGH/LOW
   never replace CLOSE. No interpolation, carry, nearby-date substitution or
   cross-source stitching is permitted.
6. Drop only missing VIX predictor origins: **1991-03-01, 1997-01-31,
   1997-11-26, 1999-12-31**. Preserve all 9,088 SPX observations, including
   21 post-2025 outcome-support rows. Missing VIX does not remove outcome
   returns used by other origins or GARCH estimation.
7. Serialize a distinct candidate CLOSE CSV and candidate origin CSV, plus a
   separate immutable derived manifest. Pin transformation version,
   implementation hash, original source/manifest hashes, excluded dates,
   warnings, coverage, row losses and output hashes. Recompute the complete
   manifest and output bytes when verifying it.
8. Every current artifact is unapproved. `load_confirmatory_close_panel()`
   explicitly raises an approval error. Editing manifest approval fields or
   derived hashes cannot grant authorization; replay detects the changes.
   There is no force/skip-validation switch. Future approval requires an
   explicit authorized implementation/amendment, not a metadata relabel.

## Exact candidate coverage and H1–H5 consequences

| Origin window | Expected | Available | Missing |
|---|---:|---:|---:|
| Full 1990-01-02–2025-12-31 | 9,067 | 9,063 | 4 |
| OOS from 2007 (first session 2007-01-03) | 4,780 | 4,780 | 0 |
| Proposed post-2003 calendar year, from 2004-01-01 | 5,535 | 5,535 | 0 |
| Alternate 2003-01-01 boundary for review | 5,787 | 5,787 | 0 |
| Post-2014-10-06 | 2,827 | 2,827 | 0 |

Missing origins by year: 1991: **1**, 1997: **2**, 1999: **1**.
Excluded non-session observations by year: 2004: **1**, 2022: **5**,
2023: **7**, 2024: **7**, 2025: **8**. Candidate aligned origins: **9,063**.
No 2026 forecast origins. All raw SPX prices remain available for future
outcome construction; no production return series was computed here.

The omission fraction is **0.044116%**, which is small in count but does not
establish negligible statistical or economic selection effects. Missingness
could be related to market stress or measurement practice. H1/H2 and full
sample H5 eligibility lose these four dates; no regime result was calculated.
H3/H4 OOS VIX eligibility loses none. Model failures and incomplete targets
can still reduce future common masks, so these are predictor counts, not
claimed final hypothesis sample sizes. Derive overlap-aware HAC lags from
the approved eligible origin sequence later; do not reuse an assumed lag.

## SPX disagreements and proposed sensitivity

Yahoo remains canonical. The [Cboe 2019 recalculation notice](https://cdn.cboe.com/resources/release_notes/2019/Corrected-Closing-Settlement-Prices-for-Certain-SP-Indices-II.pdf)
independently explains the 2019-08-12 disagreement in favor of FRED's
corrected settlement value. Applying it to canonical Yahoo OHLC still
requires a methodological decision. The other six discrepancies remain
unresolved: 2021-08-11 (5.29 points), 2020-05-11 (0.13), 2018-11-29 (0.04),
2020-10-05 (0.03), 2020-10-02 (0.02), 2020-10-06 (0.02).
Targeted official Cboe/S&P DJI searches found no verified correction notice
explaining these six; failure to locate one is not proof none exists.

Before outcomes or significance are examined, propose retaining the unchanged
Yahoo core and separately registering a report-only sensitivity to the seven
identified close disagreements. A hypothetical change `C_s -> C'_s` changes
the return ending at `s` by `epsilon=log(C'_s/C_s)` and the next session's
return by `-epsilon`. Every forward window containing either return may
change; windows containing both need not cancel in squared-return space:
`(r+delta)^2-r^2 = 2*r*delta+delta^2`. Apply the unchanged 365/30 or 252/21
annualizer only in a separately approved sensitivity execution.

Source-only diagnostics computed signed log-return adjustments and origin
footprints without producing RVAR/VRP. The 2021 disagreement potentially
touches 23 primary origins; the 2019 disagreement touches 21. Each touches
22 fixed-21 origins. The nearby October 2020 disagreements can affect the
same return; combine signed changes before squaring. Do not decide which
source to prefer or which corrections to include from subsequent significance.
Exact date lists and classifications are in the blocker-diagnostics JSON.

## Alternatives and remaining risks

- Keeping the original full-OHLC gate as the only path leaves the study
  blocked. It remains the strict acquisition contract and is not weakened.
- Repairing OPEN values is unnecessary for the CLOSE object and would alter
  provider observations; no repair is proposed.
- Stitching the one finite archived close would mix publication sources and
  still leave three dates missing. It needs a separately approved combination
  rule, so it is not the primary candidate treatment.
- Filling or shifting dates would invent information and is rejected.
- Starting the primary sample later would discard substantial pre-2000
  history and change the estimand; it is not proposed to solve four omissions.
- The XLS overlap does not validate all post-2003 closes independently.
  Historical close-time synchronization and publication meaning on excluded
  days remain uncertain. CLOSE-only eligibility does not erase these limits.

## Reproduction and artifacts

See RUN-004/005 in `docs/experiment_log.md` for commands, input hashes and
supporting downloads. Review metadata:
`data/manifests/2026-10-13_vix_close_candidate.json` and
`data/manifests/2026-10-13_source_blocker_diagnostics.json`.
Local inspection data:
`data/processed/candidates/ad54efed0d346f17/candidate_vix_close.csv`,
`candidate_origin_panel.csv`, and `candidate_close_manifest.json`.
Provider/derived price rows remain ignored by Git. Full suite: **1,674 passed**;
original strict-gate tests remain operational. CI status is recorded in the
progress journal after publication.

## Required explicit sign-off

| Author | Proposed CLOSE contract / exclusions | Post-2003 boundary | Unchanged Yahoo core / sensitivity plan | Date and evidence |
|---|---|---|---|---|
| Venelin Mirchev | PENDING | PENDING | PENDING | No authorization recorded |
| Aleksandar Slavov | PENDING | PENDING | PENDING | Implementation request permits candidates only |

Both authors must authorize the revised methodology before confirmatory
execution. This is distinct from later independent acceptance of the actual
freeze and target diagnostics. After explicit approval: record the authorized
amendment and transformation version, freeze accepted derived inputs, build
the approved panel twice and verify hashes/row losses, construct locked
targets, then seek independent freeze acceptance before H1/H2. No PR is merged
and no approval is inferred from green tests or candidate generation.

## Subsequent authorization — 2026-10-13

The preceding proposal/sign-off table records the historical unapproved state.
It is superseded for implementation by the dated amendment in
`paper/protocol_deviations.md`: both authors' agreement **as reported by
Aleksandar Slavov on 2026-10-13**, without independently verified signatures
or direct confirmation from Venelin. CLOSE eligibility, 28 exclusions, 47
warnings, unchanged Yahoo baseline, all-seven discrepancy sensitivity and
2004-01-01 boundary are authorized. Exactly one verified official XLS CLOSE,
24.64 on 1999-12-31, is now authorized; the other three remain excluded.
Technical replay and independent freeze acceptance are separate gates; the
latter is pending. Previous candidate artifacts stay CANDIDATE_UNAPPROVED.
