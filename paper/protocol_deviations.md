# Protocol Deviations Log

**Authoritative protocol:** `paper/method_protocol.md`, version 1.1.0; substantive lock 2026-08-26; amendments 2026-08-27 and 2026-10-13

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
