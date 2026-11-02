# Final editorial and rendering check

Reviewed `manuscript.md`/15-page PDF and `supplement.md`/10-page PDF, source tables and recent receipts. Abstract values agree with corrected H1/H3 sources and retain provisional status; its contrast of unconditional gap, predictive association and uncertain comparative loss is appropriately cautious. Main displayed mathematics is visible in the rendered manuscript, and no manuscript text block extends outside its page. This is a visual and selective source check, not a re-estimation or mathematical proof of every formula. No new incorrect numerical claim was identified.

## Revised rendering and remaining editorial items

The revised 15-page manuscript and 10-page supplement PDFs have no extracted text blocks outside their page boundaries. The supplement table header is no longer stranded on page 3. The historical three versus fresh two GARCH boundary fits are now distinguished in the manuscript. The theory and alternative-close selectors have been added to the revised companion claim audit, which must accompany the deliverable.

The title remains “The Volatility Risk Premium: An Empirical and Theoretical Investigation of the Gap Between Implied and Realized Volatility in Equity Index Markets.” The plural scope is wider than the S&P 500/VIX confirmatory core. Suggested: “The Volatility Risk Premium: Evidence from S&P 500 Implied and Realized Variance.” If the existing title is intentional, narrow it with an S&P 500 subtitle.

## Coverage and interpretation

- The supplement now provides distribution, time-series/histogram, returns and squared-return diagnostics, H1/H2/H5 tables, corrected H3/H4 tables, and fixed-anchor GARCH residual checks. It calls the CSVs in the companion directory the complete numerical tables; the standalone PDF contains an inventory rather than their full rows. Deliver the companion tables and audit receipts together with the PDF, or change the claim if publishing the PDF alone. Diagnostic tests at 38 anchors per model do not establish residual adequacy at every origin; the supplement states this distinction.
- Appendix C now reconciles seven sensitivity dates: the 2019-08-12 difference has official recalculation support and six remain unexplained. Neither that resolution nor arithmetic checks constitute freeze acceptance. Full original historical replay remains unavailable, as disclosed.
- The extension distinguishes overlapping event origins from independent events, the 1.5 threshold selected after H1–H5, unlike-risk portfolio comparators, and the incomplete cross-market family; partial H1 bootstrap does not complete registered H1–H5 inference.
- The references list includes sources used for the main theory and methods. The 2019 Cboe recalculation notice supporting the new Appendix C factual claim should be added explicitly to the reference list, using the URL already in `docs/production_data_freeze_report.md`, rather than leaving its provenance only in the review package.
- Minor wording: replace “reject a zero VIX contribution” with “reject a zero VIX coefficient conditional on GARCH” in H4; call the H3 abstract interval HAC for consistency. These do not alter conclusions. Spelling and numerical units were consistent in the inspected claims.
