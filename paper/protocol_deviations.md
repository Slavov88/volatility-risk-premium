# Protocol Deviations Log

**Authoritative protocol:** `paper/method_protocol.md`, version 1.1.0; substantive lock 2026-08-26; amendments 2026-08-27 and 2026-10-13

## 2026-10-13 — Author-reported interim VIX CLOSE amendment

**Amendment ID:** `2026-10-13-interim-vix-close/1.0.0`, supplementing base
protocol 1.1.0 without changing its horizons, units, hypotheses or sample limits.
Aleksandar Slavov communicated on 2026-10-13 that both authors, Aleksandar
Slavov and Venelin Mirchev, agree to implement this interim methodology.
This is author-reported agreement, not independently verified signatures or
direct confirmation from Venelin. Independent acceptance of the resulting
freeze remains **PENDING**; outputs are **PROVISIONAL / NOT INDEPENDENTLY ACCEPTED**.

1. Original acquisition required complete unique XNYS coverage, finite positive
   OHLC and valid OHLC ordering. The immutable Cboe CSV failed: four missing
   sessions, 28 non-XNYS dates, and 47 OPEN-only inconsistencies. The strict
   acquisition gate and provider archives remain unchanged and rejected.
2. The separate authorized pathway validates finite positive CLOSE, unique
   canonical dates and consistency with available HIGH/LOW bounds. OPEN-only
   defects remain 47 explicit warnings. Exclude all 28 non-XNYS observations;
   never shift dates, repair OPEN, interpolate or forward-fill.
3. Authorize exactly one official archival-source insertion: **1999-12-31,
   VIX CLOSE 24.64 percentage points**, conditional on verifying the original
   numeric cell/date/schema and SHA-256 of the official Cboe XLS at
   https://cdn.cboe.com/resources/us/indices/vixarchive.xls. Expected hash:
   `9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566`.
   Record cell reference, parser, source absence, transformation/code identity
   and review state. FRED VIXCLS may corroborate the same value but republishes
   Cboe; it is not an independent index calculation.
4. Exclude 1991-03-01, 1997-01-31 and 1997-11-26 as unavailable predictors.
   Repeated previous Yahoo closes are not verified observations. Any optional
   carry-forward experiment must remain separate and exploratory.
5. Yahoo ^GSPC stays canonical: preserve all 9,088 rows and 21 post-2025
   outcome-support rows. Missing VIX origins must never remove SPX returns.
   Register the alternate-FRED-close sensitivity for **all seven** discrepancy
   dates (2018-11-29, 2019-08-12, 2020-05-11, 2020-10-02, 2020-10-05,
   2020-10-06, 2021-08-11), individually and jointly. Compare affected CC
   targets and descriptive results; keep Yahoo baseline unchanged. Alternate
   GK estimates are admissible only if alternate CLOSE satisfies original
   OHLC bounds, otherwise report estimator unavailability. No source choice
   or subset selection may depend on significance.
6. Fix the post-2003 sensitivity start at **2004-01-01**, before empirical
   outcomes. Full sample and post-2014-10-06 remain as previously specified.
7. RUN-001–005 document only acquisition, eligibility and hypothetical
   return-change footprints. No empirical H1–H5, VRP or forecasting result
   was examined before these decisions. Bias direction is unknown; exclusions
   and mixed official publications remain measurement limitations.
8. Cboe inquiry: **SENT — AWAITING CBOE RESPONSE**, as reported by Aleksandar.
   No send date, acknowledgement, recipient or case number is established here.
   Authentic subsequent values or contradictions require a new versioned
   amendment, preserved interim baseline, source verification, independent
   rebuild/review and comparison; never overwrite earlier artifacts/results.
9. Implement a distinct immutable, hash-verified promotion pathway; preserve
   the previous unapproved candidate. Build twice, audit six complete targets
   and permit provisional descriptions. H1/H2 inferential execution awaits
   independent freeze acceptance. Green tests do not establish that acceptance.
10. Implementation commits, exact raw/derived hashes and replay evidence will
    be recorded in the execution log and freeze report as work is completed.
    This authorization does not retroactively approve earlier pending reviews.

## 2026-08-27 — Technical sample-tail support amendment

1. **Original rule:** The forecast-origin sample was locked through 2025-12-31, but the accompanying acquisition examples stopped S&P 500 data at an exclusive 2026-01-01 end.
2. **Reason for change:** Forward realized targets attached to valid late-2025 origins require outcome returns after 2025-12-31. Stopping the S&P 500 data at year-end would mechanically truncate or drop valid targets, contradicting the rule that targets are never shortened.
3. **Replacement rule:** Forecast origins remain frozen through 2025-12-31. S&P 500 OHLC/return outcome support extends through 2026-02-02 via `--end-exclusive 2026-02-03`, which is sufficient for both the 30-calendar-day primary target and the 21-trading-day robustness target of the final 2025 origin. Post-2025 rows are outcome support only and cannot become forecast origins or extend predictor/training information sets.
4. **Relevant results viewed before change:** No empirical VRP, forecast-ranking, or regime result had been generated or inspected.
5. **Likely effect:** The original acquisition boundary would have selectively removed or shortened late-2025 targets. The amendment preserves the pre-specified 2025 origin sample and complete-horizon construction; no expected sign change is imposed.
6. **Affected files:** `paper/method_protocol.md`, `README.md`, `docs/data_sources.md`, `data/raw/README.md`, `docs/data_dictionary.md`, `docs/methodology_decisions.md`, `src/vrp/config.py`, and `tests/test_config.py`.
7. **Coauthor review/approval status:** Pending.

The August 10 and August 23 design drafts are not recorded here as post-lock deviations because they pre-date the final August 26 protocol and no empirical VRP, forecast-ranking, or regime results had been generated before the methodological reconciliation. Their history is documented in `docs/methodology_decisions.md` and preserved in Git.

## 2026-09-28 — Drop FRED SP500 close validation

1. **Original rule:** FRED `SP500` closes validated the overlapping recent Yahoo `^GSPC` window. Discrepancies were reported and neither source was overwritten.
2. **Reason for change:** The operator removed FRED `SP500` validation after repeated official-transport timeouts. Yahoo `^GSPC` remains the sole S&P 500 OHLC source. FRED `DGS1MO` remains the short risk-free-rate source.
3. **Replacement rule:** Production S&P 500 acquisition uses Yahoo Finance `^GSPC` only. FRED `SP500` is not fetched and is not a validation overlay.
4. **Relevant results viewed before change:** No empirical VRP or forecast-ranking result prompted this change. The trigger was transport failure during raw acquisition.
5. **Likely effect:** Recent Yahoo closes are no longer checked against the FRED redistribution of the S&P 500 close. Index levels remain Yahoo `^GSPC`.
6. **Affected files:** `paper/method_protocol.md`, `docs/data_sources.md`, `docs/methodology_decisions.md`, `data/raw/README.md`, `src/vrp/spx_data.py`, and the vrp-agent SPX acquisition wrapper.
7. **Coauthor review/approval status:** Requested by the operator on 2026-09-28.

## Required format for future deviations

For every deviation, add a dated entry containing:

1. **Original rule**
2. **Reason the original rule cannot or should not be followed**
3. **Replacement rule**
4. **Whether relevant results had already been viewed**
5. **Likely direction of bias or effect, if known**
6. **Affected code, tables, figures, or paper sections**
7. **Coauthor review/approval status**

If a change is made after relevant results have been viewed, the modified specification is exploratory unless the original pre-specified analysis remains reported.


## 2026-10-13 — Restore independent close validation as non-blocking

1. **Original rule:** The 2026-09-28 deviation removed FRED SP500 close validation because repeated transport failures blocked acquisition.
2. **Reason for change:** Scientific-correctness review separated the canonical data source from the validation transport. Independent validation remains useful, especially because earlier feasibility work found several Yahoo/FRED close discrepancies, but a validation endpoint outage should not determine whether the canonical Yahoo snapshot can be acquired.
3. **Replacement rule:** Yahoo ^GSPC remains the canonical S&P 500 OHLC source. FRED SP500 is optional validation only. Validation failure is recorded as unavailable/pending and does not block acquisition. When validation succeeds, discrepancies are reported and Yahoo is never overwritten automatically.
4. **Relevant results viewed before change:** No empirical VRP, forecast-ranking, regression, GARCH, or regime result was generated to motivate this refinement.
5. **Likely effect:** Restores an independent recent close-quality check without reintroducing a network single point of failure.
6. **Affected files:** src/vrp/spx_data.py, tests/test_spx_data.py, docs/data_sources.md, docs/methodology_decisions.md, paper/method_protocol.md, and data/raw/README.md.
7. **Coauthor review/approval status:** Pending.


## 2026-10-13 — Pre-result H3/H5 refinement and 2014 VIX sensitivity

1. **Original rule:** H3 did not name one pairwise forecast contrast as primary; H5 did not name one regression/null; VIX robustness did not separately isolate the non-backfilled 2014 weekly-option inclusion change.
2. **Reason for change:** A scientific-correctness audit identified avoidable multiplicity/specification discretion and the documented Cboe spot-VIX transition beginning 2014-10-06.
3. **Replacement rule:** H3 primary inference is VIX versus GARCH under squared-error loss. VIX-versus-naive and GARCH-versus-naive are secondary with Holm adjustment across that two-test family. H5 uses `VRP_X = alpha + delta * recession + u`, two-sided `H0: delta=0`, and the H1 overlap-derived HAC rule. Post-2014-10-06 is a mandatory VIX-methodology sensitivity sample.
4. **Relevant results viewed before change:** No empirical VRP values, forecast losses/rankings, GARCH results, H3/H5 tests, or crisis outputs had been generated or inspected.
5. **Likely effect:** Reduces researcher degrees of freedom; empirical direction is unknown ex ante.
6. **Documentation:** Cboe Information Circular IC14-075 and Cboe's VIX maturity-interpolation research note.
7. **Coauthor review/approval status:** Pending.
8. **Protocol version:** 1.1.0.

## 2026-10-13 provisional execution before independent freeze review

Aleksandar explicitly authorizes H1-H5 execution before Venelin's independent
freeze review. This changes operational review order only: results become
visible before review. Statistical specifications, base protocol 1.1.0 and
interim dataset/amendment stay unchanged. Original strict gate remains
unchanged. No new Venelin signature or scientific acceptance is implied.
All outputs remain provisional pending independent coauthor review. Reviewer
rejection requires documented versioned revision/full re-execution, preserving
original outputs. No subsequent change may optimize observed significance.
