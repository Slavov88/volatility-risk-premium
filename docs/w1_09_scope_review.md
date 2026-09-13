# W1-09 scope review and approval

**Tracker task:** W1-09  
**Review date:** 2026-09-12  
**Reviewer role:** auditor  
**Dependency reviewed:** W1-01 research question and project scope  
**Authoritative protocol:** `paper/method_protocol.md`, version 1.0.1  
**Decision:** **approved for core execution**, subject to the protocol's existing pre-analysis gates

This approval covers scope only. It does not approve empirical results, final conclusions, submission, a data-source change, or any alteration of the locked scientific design.

## Central-question test

The approved work must help answer the following locked question:

> Is the observed excess of option-implied over subsequently realized S&P 500 variance statistically robust and economically explicable as compensation for volatility/tail risk, or does it weaken materially once horizon alignment, overlapping observations, non-normality, forecast design, and regime dependence are handled correctly?

A task belongs in the core only if it does at least one of the following:

1. defines or estimates the locked empirical objects and hypotheses;
2. tests robustness, calibration, forecast performance, or regime dependence required by the protocol;
3. supplies theory needed to interpret the implied-realized variance gap without conflating VIX with a single-option Black--Scholes implied volatility; or
4. makes those analyses valid, reproducible, and auditable through data provenance, diagnostics, testing, or traceability.

## Approved core scope

| Work package | Scope decision | Link to the central question |
|---|---|---|
| Locked research design and terminology | Core | Fixes the estimand, sign convention, hypotheses, interpretation limits, and anti-specification-mining rule. |
| Official VIX and S&P 500 index data, validation, cleaning, alignment, and provenance | Core enabling work | Supplies the implied measure and subsequent realized outcomes while protecting the timing and exact-index requirements. |
| Exact forward 30-calendar-day close-to-close realized variance and `VRP_X = IVAR - RVAR` | Primary core analysis | Directly measures the locked ex-post variance-premium proxy at the VIX horizon. |
| H1 mean proxy inference and H2 Mincer--Zarnowitz calibration | Core | Tests robustness of the gap and calibration of VIX variance. |
| H3 out-of-sample VIX/GARCH(1,1)/naive forecast comparison and H4 encompassing | Core | Determines whether the gap survives a disciplined forecast design and whether VIX contains incremental information. |
| H5 NBER regime analysis and pre-defined 2008, 2020, and 2022 case studies | Core | Evaluates the locked regime-dependence and crisis-behaviour component. |
| Required diagnostics, common masks, leakage tests, overlap-aware inference, and deterministic non-overlap analysis | Core controls | Prevents invalid inference or forecast rankings from answering the question spuriously. |
| Black--Scholes theory, pricer, implied-volatility solver, and small-scale option validation | Supporting core track | Provides the option-pricing foundation and validates the required distinction between single-option IV and model-free VIX; it may not redefine Track B. |
| Reproducible tables, figures, manifests, tests, and paper traceability | Core enabling work | Makes every reported answer reproducible and auditable. |

All robustness analyses enumerated in Section 17 of the protocol remain mandatory core work. “Robustness” does not mean optional or stretch, and none may be promoted to the primary specification.

## Week 1 artifact disposition

| Artifact/work completed through W1-08 | Disposition | Audit rationale |
|---|---|---|
| Research design, protocol, decision ledger, and data definitions | Retain | Directly fixes the question and the pre-analysis implementation contract. |
| Stochastic-calculus and Black--Scholes notes | Retain as supporting core | Needed for the bounded Track A derivation and for keeping Black--Scholes IV conceptually separate from VIX. |
| Economic-theory memo | Retain as supporting core | Provides the risk-aversion, replication, and crash-insurance interpretation needed by the “economically explicable” part of the question. |
| VIX methodology note | Retain | Establishes the option-strip definition, variance units, and exact 30-calendar-day alignment. |
| Targeted literature matrix | Retain | Supports the locked measurement, overlap, calibration, forecast, and interpretation choices without predetermining results. |
| Data-source feasibility and acquisition code | Retain as core enabling work | Establishes access and provenance for required inputs; production TLS verification and discrepancy investigation remain open gates. |

No completed Week 1 task is removed. Each has an explicit mapping to the central question or to a validity requirement. This is not permission to expand any of those tasks beyond the bounded uses stated above.

## Removed from the core task list

The following do not answer the locked confirmatory question and are therefore **not core tasks**:

- trading-strategy design, backtests, portfolio construction, or transaction-cost optimization;
- equity-return predictability;
- large-scale option-surface construction or independent VIX replication;
- machine-learning forecast models;
- Heston calibration or other advanced volatility-model substitution;
- cross-market or cross-asset comparisons;
- event studies beyond the pre-defined 2008, 2020, and 2022 case studies;
- unplanned crisis windows, alternative regime definitions, or result-selected subsamples;
- extra realized-variance estimators, forecast losses, or model variants not required by the locked protocol; and
- publication packaging or submission work before the core evidence has reproduced and passed audit.

These items must not be scheduled, implemented, or used to replace weak or unexpected core findings.

## Stretch-goal gate

The removed items above are stretch goals only if all of the following are satisfied:

1. the complete core pipeline reproduces from raw data to final core outputs;
2. all protocol-required tests, robustness checks, provenance checks, and traceability checks pass or any failure is transparently reported;
3. the production acquisition uses verified TLS and the material Yahoo/FRED discrepancies have been resolved through the protocol's review gate;
4. the pre-defined case-study windows are frozen before regime outputs are calculated;
5. the extension is labelled exploratory and cannot alter, replace, or suppress a locked core specification or result; and
6. a separate extension-scope approval is recorded before work begins.

## Approval record

The core scope above is approved for implementation. Stretch work is explicitly separated and remains unapproved pending the extension gate. No locked scientific choice was changed during this review, and no empirical result was used to add, remove, or reclassify a core analysis.
