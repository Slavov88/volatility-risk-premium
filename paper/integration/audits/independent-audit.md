# Independent integration audit

Auditor: separate computational review agent, 2 November 2026. Base inspected: `27735e5653b5b778fb0e23ccc3e9079d4bdd6aa3`. This is a technical audit, not coauthor approval or acceptance of a data freeze.

## Scope and authoritative rules

Read `paper/method_protocol.md`, `paper/protocol_deviations.md`, `paper/cross_market_replication_protocol.md`, and calendar amendment/clarification. Inspected cross-market contrast, H3/H4, H5, H6/H7 scripts and relevant inference helpers. Original interim CLOSE authorization explicitly preserves provisional status and the rejected strict acquisition gate. Retrospective Nasdaq replication remains exploratory, irrespective of implementation tests.

## Findings

1. **Cross-market inference incomplete.** `scripts/compare_cross_market_ndx_spx.py` implements paired mean contrasts and stacked market-interaction OLS with date-grouped Bartlett HAC. Cross-market protocol §5 requires paired circular block bootstrap (63, 21 and126 dates; 1,000 draws; seed1729) and the specified H1–H5 multiplicity family. Neither required bootstrap nor cross-market Holm appears in that script. Reported HAC intervals can be descriptive sensitivity evidence, but do not complete the registered comparative inference.
2. **Paired comparison bandwidth qualification.** That comparison hardcodes HAC21 for both horizons. The parent method specifies mechanically derived L0 for30c and HAC20 for21t with sensitivity grids. The within-market H3/H4 script does implement those grids. Do not generalize the narrow paired-script finding to all Nasdaq inference.
3. **Estimator wording.** The comparison result's inference string calls its slope contrast a regression on market differences. Actual implementation estimates a stacked interaction model, preserving separate regressors and grouping scores by date. Use the latter description.
4. **H7 sensitivity wording.** Cross-market report quotes HAC21 p=.182 for combined versus VXN. The implementation also computes primary HAC63 and Holm from HAC63. A manuscript quoting the docs value should identify it as sensitivity rather than primary inference.
5. **Evidence boundary.** Full ignored cross-market daily results were absent at inspection. Public summary extraction is possible, but raw-data rerun or independent reconstruction of all Nasdaq tests is not established by the committed report and manifest hashes alone.

## Numeric exhibit checks

Independently loaded newly generated CSVs, recomputed two-sided normal p-values and 95% CI widths. All72 H1 rows,486 corrected H3 contrasts and486 corrected H4 coefficients passed; tolerances2e-5 for p-values and2e-6 for interval widths accommodate rounded summaries. Receipt: `independent-numeric-receipt.json`. This checks arithmetic consistency, not raw-data inference validity.

## Pending final assembly

At this checkpoint the manuscript and final PDF were not yet present. Final typography, equations, bibliography, source attribution and manuscript-table correspondence require review after assembly. No blanket scientific acceptance is issued.
