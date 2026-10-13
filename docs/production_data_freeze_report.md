# Production acquisition audit — freeze blocked

Date: **2026-10-13**. Protocol **1.1.0**; source branch **456a77c**.
Scientific acceptance: **NOT APPROVED; independent coauthor review pending**.
This is a review package for the acquired snapshots, not an approved freeze.

| Source | Window / actual coverage | Rows | Quality |
|---|---|---:|---|
| Yahoo `^GSPC`, unadjusted OHLC | 1990-01-02 through 2026-02-02; exclusive end 2026-02-03 | 9,088 | Accepted: exact XNYS coverage; no missing/nonpositive OHLC or order violations |
| Official Cboe VIX | 1990-01-02 through 2025-12-31; exclusive end 2026-01-01 | 9,091 | Rejected: 4 missing sessions, 28 non-session rows, 47 OHLC violations |
| FRED `SP500`, validation only | Available 2016-10-13 through 2026-02-02 | 2,428 raw; 2,338 usable overlap | 90 missing/holiday entries; 2,331 overlap closes within one cent; 7 discrepancies |

Python 3.11.5 and all 51 packages in the unchanged dependency lock were
verified. XNYS uses locked exchange-calendars 4.13.2. Original SHA-256 hashes,
date lists and recomputed quality statistics are in
`data/manifests/2026-10-13_production_quality_audit.json`; acquisition/replay
commands and input hashes are in `docs/experiment_log.md`.

## VIX findings

Expected origin sessions: **9,067**. Missing dates:
**1991-03-01, 1997-01-31, 1997-11-26, 1999-12-31**.
These are sessions in the locked XNYS calendar and are present in Yahoo.
Provider-only dates and all defect dates are enumerated in the audit JSON.

The 28 non-session observations comprise 2004-06-11 plus 27 dates in
2022–2025, including 2025-01-09 and exchange holidays. They are not silently
accepted as index forecast origins. The 47 OHLC defects occur in 1992–2006:
20 have HIGH below OPEN, 27 have LOW above OPEN; none has HIGH below CLOSE,
LOW above CLOSE or HIGH below LOW. Although only CLOSE is the required VIX
predictor, the **existing production gate requires valid VIX OHLC**. It was
not relaxed here. This distinction is a concrete item for methodological
review, not evidence that the rejected file is acceptable.

[Cboe's current historical-data page](https://www.cboe.com/tradable-products/vix/vix-historical-data)
links a second current CSV endpoint and a 1990–2003 XLS archive. The current
linked CSV is byte-identical to the configured endpoint. The XLS provides a
finite close for 1999-12-31; 1991-03-01 is present with textual `n/a`, while
the two 1997 missing dates are absent. Its 3,528 overlapping closes agree
with the current CSV. The XLS has 508 rows without OPEN/HIGH/LOW and does
not itself pass the existing production contract. No values were stitched.
Exact auxiliary hashes and diagnostic metadata are in
`data/manifests/2026-10-13_cboe_archive_inspection.json`.

## Yahoo/FRED findings

The seven above-one-cent differences recur on the same feasibility dates:

| Date | Absolute index-point difference | Investigation status |
|---|---:|---|
| 2021-08-11 | 5.29 | Unresolved; no primary correction notice established in this session |
| 2019-08-12 | 1.05 | Official Cboe recalculation notice supports FRED; Yahoo unchanged |
| 2020-05-11 | 0.13 | Unresolved |
| 2018-11-29 | 0.04 | Unresolved |
| 2020-10-05 | 0.03 | Unresolved |
| 2020-10-02 | 0.02 | Unresolved |
| 2020-10-06 | 0.02 | Unresolved |

The [Cboe notice, reference C2019081302](https://cdn.cboe.com/resources/release_notes/2019/Corrected-Closing-Settlement-Prices-for-Certain-SP-Indices-II.pdf)
states that S&P DJI recalculated the 2019-08-12 closing values. It supplies
independent evidence for one discrepancy, but not a reviewed correction rule
for Yahoo's canonical OHLC. No replacement, averaging or deletion occurred.
Discrepancy metadata are retained; actual provider prices remain local.

## Panel boundary and replay

- Yahoo contains **21** post-2025 outcome-support rows. Eligible origin
  sessions remain **9,067**; the raw date intersection is **9,063**.
- Intersection counts are diagnostics only. The actual verified-panel builder
  rejected the VIX snapshot with `PanelProvenanceError: VIX: acquisition not
  accepted`; **no panel or target dataset was produced**.
- The rejection audit reproduced identical bytes and digest
  `a3cab6ddf0399d436fab797616cb145ffcc9e27cc001edf2c5958028ba78943f`.
  This is audit repeatability, not panel/dataset repeatability.
- SPX/FRED source hashes were verified, VIX normalization replayed from raw
  provider bytes, recorded quality independently recomputed. No TLS checking
  was disabled. Default library certificate verification succeeded; manifest
  configuration is not a separate cryptographic transport attestation.

## Artifacts and review actions

Local immutable provider artifacts: `data/raw/2026-10-13T142430Z/`.
Tracked sanitized metadata: four dated JSON files in `data/manifests/`.
The sanitized SPX manifest deliberately omits Yahoo/FRED observed closes;
its hash differs from the original raw manifest, whose hash is recorded in
the audit. Replay uses **original local acquisition manifests**.

1. Coauthor reviews the four missing VIX dates, holiday observations and
   OPEN-only anomalies. Obtain source clarification/corrected official data;
   any alternative source stitching, explicit exclusions or close-only gate
   needs a documented methodological decision/deviation and review.
2. Resolve remaining Yahoo/FRED differences with authoritative evidence;
   assess the 2019 correction without silently changing canonical Yahoo.
3. After both reviewed source gates pass, build the origin panel twice,
   check exact hashes/counts, then construct all six forward targets and
   origin-aligned proxy/gap diagnostics. Keep pre-review outputs provisional.
4. Obtain independent freeze acceptance before H1/H2 and later OOS analysis.

No favorable or negative empirical VRP conclusion can be drawn at this stage.

## Follow-up: separate unapproved CLOSE candidate (2026-10-13)

The original acquisition findings and rejection above are unchanged. A
distinct inspection-only CLOSE contract now generates **9,063** candidate
origins, with original source replay, explicit exclusions and derived hashes.
No approved panel, production target or inferential freeze exists.
See `docs/vix_close_acceptance_proposal.md` for the exact contract, both-author
sign-off requirements and 1,674 passing tests. Full metadata are in
`data/manifests/2026-10-13_vix_close_candidate.json` and
`data/manifests/2026-10-13_source_blocker_diagnostics.json`.

New official Cboe closure/GTH notices and small FRED VIXCLS checks support
the publication/eligibility distinction and corroborate missing values on
three dates. They do not authorize source stitching. All four missing origins
remain excluded in the candidate. The 2019 SPX correction explanation remains
verified, while six other Yahoo/FRED differences remain unresolved. No
canonical source observations were changed.

## 2026-10-13 authorized interim freeze and provisional targets

**Current technical status: PASSED. Scientific status: PROVISIONAL / NOT INDEPENDENTLY ACCEPTED.**

Both-author methodology agreement is recorded as reported by Aleksandar Slavov on 2026-10-13, not verified signatures or direct Venelin confirmation. Base protocol 1.1.0 plus amendment `2026-10-13-interim-vix-close/1.0.0`. The preceding blocked/unapproved sections describe historical gates. Original strict acquisition still fails; this is a distinct authorized interim pathway.

The original XLS SHA-256 matches its earlier archive. Sheet OHLC, Excel datemode 0: A2528 serial 36525 decodes to 1999-12-31; E2528 is numeric 24.64 annualized percentage points, contained by archived HIGH/LOW. FRED VIXCLS republishes the same Cboe value and corroborates it; no independent calculation is claimed. Exactly this observation is inserted. Three missing origins remain excluded; 28 non-XNYS rows excluded and 47 original OPEN warnings preserved.

| Window | Expected XNYS origins | Eligible | Missing |
|---|---:|---:|---|
| full_sample (from 1990-01-02) | 9067 | 9064 | 1991-03-01, 1997-01-31, 1997-11-26 |
| oos_from_2007 (from 2007-01-01) | 4780 | 4780 | None |
| post_2003 (from 2004-01-01) | 5535 | 5535 | None |
| post_2014_10_06 (from 2014-10-06) | 2827 | 2827 | None |

All 9,088 original Yahoo SPX observations are preserved numerically without replacement, including 21 support-only rows in 2026. Their original normalized snapshot bytes are unchanged. Derived canonical CSV uses 17-digit serialization, hence has a different hash. Returns use the full SPX source before VIX origin masking: 9,087 dated returns; first price has no prior observed price/return. No return is invented or bridged across a missing session. No 2026 origins.

Freeze implementation commit: `55ce4a23b44188ae21c8343005c6104b9a8a5d21`. Target implementation commit: `c53bb9c65dd5b7521ebe80070103a525d98b373c`. Source-code fingerprints are in the manifests and independently checked against Git blobs (LF-normalized for checkout portability).

| Original artifact | SHA-256 |
|---|---|
| archive | `9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566` |
| fred_vix | `cf5fd219cd8cd428b287c6f260baaefd746e11ca8ef1eb19ffc9741204d58bcb` |
| spx | `dd7838e8470a5056e99b82dba808bf9df226ced891e0826e4425d55a8d0f544e` |
| vix_normalized | `10b2faa178208d7553f96597b40e63807668af77b3f8242f73afb8b8a40b0f94` |
| vix_raw | `965f14ae8d58079536b5491219b647e6385592be2c466e6ac849f6ace0bbe1f7` |

| Derived artifact | SHA-256 |
|---|---|
| Interim manifest | `1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4` |
| canonical_spx_ohlc.csv | `ad8baf5121a081d633d6283c936f6956f82974446dfd871fc905ab31ff34a74e` |
| interim_origin_panel.csv | `5293bc8b5e3388090216fb27e50d5a989c67e817dde67cc40358c3522e3a32f5` |
| interim_vix_close.csv | `457f46b6850ef6481fc272deb0e097b5da1134e1610c7d86c225448758eb6353` |
| Empirical manifest | `00532571aad5f8d9c43231933429fe6facbf7687a6332231ac8b7ad0ff73ccd9` |
| alternate_close_sensitivity.json | `2542a1503a7d2e543878ce6f23bfda8432348ae195eae23798dd113ac2f16e75` |
| canonical_daily.csv | `774147ffba6e298a49ef2ba1059503515e2dec1317500d4f37acf980cd7a51e2` |
| descriptive_statistics.json | `bc93ca5c9d69a17d2dbb927fb1509bc578b343156ee1b9437898b8248aa0787c` |
| six_forward_targets.csv | `cdd63f219d61584c8f3fa15e8f80c23ef351a6e902cb93027eed9b5e79dba3a5` |
| target_audit.json | `7b8d05616a1477e40c1eb86b65fe21a26e87e4b24429ef5ce056911eaed88bb5` |

Two independent builds from the same immutable inputs produced identical freeze output bytes, hashes and dates. Two actual executions separately recomputed all returns, targets, audits, descriptions and sensitivity outputs with identical bytes and hashes; immutable writer rejects differences. Original raw sources and historical candidate were reverified afterward, not modified.

All six target series (CC, Parkinson, GK; each 30c/21t) have **9,064 complete targets and zero missing**. Independent numpy audit recomputes all 54,384 origin/target combinations, including units, premium sign, endpoints, expected session sets, support rows and unchanged predictors. Maximum absolute RVAR difference: `2.220446049250313e-16`. Exact 30c windows contain 15-22 sessions; 21t windows contain exactly 21. Audit pass is technical evidence, not coauthor acceptance. No H1-H5 inference, forecast ranking or economic-mechanism test executed.

### Provisional descriptive results

| Fixed subset | N | Mean IVAR | Mean CC RVAR 30c | Mean VRP_X 30c | Positive VRP_X fraction |
|---|---:|---:|---:|---:|---:|
| full_sample | 9064 | 0.043909446 | 0.032560532 | 0.011348914 | 0.859996 |
| oos_from_2007 | 4780 | 0.047012666 | 0.039540770 | 0.007471895 | 0.826569 |
| post_2003 | 5535 | 0.043230998 | 0.035629768 | 0.007601230 | 0.841192 |
| post_2014_10_06 | 2827 | 0.038435225 | 0.031766762 | 0.006668463 | 0.828794 |

Variance values are annualized decimal variance, not volatility percentage points. Full-sample mean secondary VOLGAP is 0.041168834 annualized decimal volatility (4.1168834 volatility percentage points). Descriptions alone do not establish significance, forecast miscalibration or a risk-compensation mechanism. Full distributional statistics for all six families and fixed subsets are in the hashed descriptive JSON. No conclusions added to the manuscript.

All seven alternate FRED closes were evaluated individually and jointly as separate pre-registered CC sensitivity scenarios. Joint changes affect 111 30c and 112 21t origins. Full-sample primary mean VRP change is 5.84032514509e-07; maximum absolute 30c target change is 0.000239699541791. Adjacent October 2020 corrections are combined before squaring. These do not authenticate the alternate prices or resolve source disagreements. Canonical Yahoo remains unchanged. Range-estimator alternate-price sensitivities were not executed; any OHLC conflicts are explicit in the sensitivity JSON. Optional unverified carry-forward VIX scenario was not run.

### Independent review and response handling

Venelin should inspect the dated authorization/amendment, verify original source and derived hashes, reparse A2528/E2528, reproduce XNYS eligibility, source preservation and all target audits, and record actual independent acceptance/rejection with its evidence. No signature is supplied by this execution. See RUN-007/008 for exact commands. H1/H2 inferential execution remains gated until independent freeze acceptance; then use locked overlap-HAC/non-overlap and calibration robustness, followed by recursive GARCH/OOS H3/H4 and frozen-regime H5.

Cboe inquiry **SENT — AWAITING CBOE RESPONSE**, author-reported only. Six Yahoo/FRED disagreements remain unexplained; 2019-08-12 has official correction support but is still an alternate-source sensitivity. Exact historical VIX-close synchronization and non-session publication mechanisms remain limitations. Authentic later Cboe values or contradiction of the archive require a new versioned amendment, preserved baseline/results, independently reviewed rebuild and explicit comparison.
