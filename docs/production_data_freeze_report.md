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
