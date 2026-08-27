# Protocol Deviations Log

**Authoritative protocol:** `paper/method_protocol.md`, version 1.0.1; substantive lock 2026-08-26, technical amendment 2026-08-27

## 2026-08-27 — Technical sample-tail support amendment

1. **Original rule:** The forecast-origin sample was locked through 2025-12-31, but the accompanying acquisition examples stopped S&P 500 data at an exclusive 2026-01-01 end.
2. **Reason for change:** Forward realized targets attached to valid late-2025 origins require outcome returns after 2025-12-31. Stopping the S&P 500 data at year-end would mechanically truncate or drop valid targets, contradicting the rule that targets are never shortened.
3. **Replacement rule:** Forecast origins remain frozen through 2025-12-31. S&P 500 OHLC/return outcome support extends through 2026-02-02 via `--end-exclusive 2026-02-03`, which is sufficient for both the 30-calendar-day primary target and the 21-trading-day robustness target of the final 2025 origin. Post-2025 rows are outcome support only and cannot become forecast origins or extend predictor/training information sets.
4. **Relevant results viewed before change:** No empirical VRP, forecast-ranking, or regime result had been generated or inspected.
5. **Likely effect:** The original acquisition boundary would have selectively removed or shortened late-2025 targets. The amendment preserves the pre-specified 2025 origin sample and complete-horizon construction; no expected sign change is imposed.
6. **Affected files:** `paper/method_protocol.md`, `README.md`, `docs/data_sources.md`, `data/raw/README.md`, `docs/data_dictionary.md`, `docs/methodology_decisions.md`, `src/vrp/config.py`, and `tests/test_config.py`.
7. **Coauthor review/approval status:** Pending.

The August 10 and August 23 design drafts are not recorded here as post-lock deviations because they pre-date the final August 26 protocol and no empirical VRP, forecast-ranking, or regime results had been generated before the methodological reconciliation. Their history is documented in `docs/methodology_decisions.md` and preserved in Git.

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
