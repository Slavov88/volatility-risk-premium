# Cross-Market Replication Protocol

**Version:** 1.0  
**Registration date:** 2026-10-15  
**Status:** Registered historical external replication; all new-market findings remain exploratory pending independent review.  
**Parent baseline:** PR #6 head `0910d8e26355832bdbd63abbc10a65a70bbc4d77` (Task 2/3 development chain; all recorded checks passed; PR open, draft, no reviews).  
**Registration rule:** This commit precedes acquisition of new market panels and inspection of their H1–H8 outcomes. Source feasibility and public provider documentation may be inspected before registration; no cross-market hypothesis estimates have been generated or examined.

## 1. Questions and scope

This protocol tests whether the existing S&P 500/VIX empirical patterns recur in other equity markets. It is a retrospective study of historical observations, not prospective blind validation. The S&P 500 results and methods are frozen in their existing protocols and artifacts. No historical S&P 500 result will be rewritten. New-market findings are a pre-specified external replication, but remain exploratory because the extension follows the original S&P 500 analyses and because market-specific data quality and index construction differ.

The ordered markets are:

| Priority | Underlying and implied-volatility index | Investable proxy | Calendar and currency | Status before acquisition |
|---|---|---|---|---|
| Reference | S&P 500 / VIX | SPY | XNYS, USD | Reuse frozen original inputs and results as reference; do not refit or overwrite them. |
| 1 | Nasdaq-100 / Cboe VXN | QQQ | Nasdaq U.S. sessions, USD | Proceed only after source, license, coverage, timestamp, and alignment gates pass. |
| 2 | Russell 2000 / Cboe RVX | IWM | U.S. sessions, USD | Proceed only after source, license, coverage, timestamp, and alignment gates pass. |
| 3 | EURO STOXX 50 / VSTOXX (30-day V2TX) | EUR-listed EURO STOXX 50 ETF candidate, provisionally iShares Core EURO STOXX 50 UCITS ETF (EUN2; verify exchange, currency, distributions, and inception before use) | Xetra/Eurex-aligned sessions, EUR | Blocked unless authorized full-history index data and a reproducible underlying price source are available. |
| Optional | DJIA / VXD | DIA | U.S. sessions, USD | Excluded from the primary family; may be added only by a dated protocol amendment before acquiring or inspecting VXD/DIA hypothesis outcomes and only if coverage and comparability pass. |

Markets are not assumed to share the same volatility-index formula, option universe, close timestamp, annualization, trading session, or estimand. Each provider methodology and historical transition will be described separately. A proxy ETF return is not an underlying-index return and is used only for H8.

## 2. Sources and data eligibility gates

The initial source candidates are fixed as follows. A source is accepted only after recording retrieval timestamp, exact request/URL, provider and source series identifiers, units, definition, coverage, licensing terms, response bytes, and SHA-256. If a source fails a gate, record the failure and do not silently substitute, backfill, splice, or interpolate.

| Data | Priority source | Fixed use and gate |
|---|---|---|
| NDX close | Nasdaq Global Indexes historical data; FRED `NASDAQ100` is an independently accessible distribution of Nasdaq daily closing index data and may be the operational source if its terms and coverage are suitable. | Price index close only. No ETF or Nasdaq Composite substitution. Record revisions and any provider limits. |
| VXN close | Cboe historical/index data; FRED `VXNCLS` is a Cboe-sourced daily close series and may be used as an accessible frozen distribution after copyright/use review. | Index points, daily close. Verify first valid date, missingness, time convention, and methodology. Do not infer a historical observation time from current dissemination. |
| RUT close | FTSE Russell/Russell official index data; an accessible independent distributor may be used only if the identifier and close definition are verified. | Russell 2000 price index, not IWM, total return, or a reconstructed constituent portfolio. |
| RVX close | Cboe historical/index data; FRED `RVXCLS` is a Cboe-sourced daily close series and may be used as an accessible frozen distribution after copyright/use review. | Index points, daily close. Verify first valid date, missingness, time convention, and methodology. |
| QQQ, IWM | Issuer/primary exchange corporate-action and price data where available; otherwise pinned `yfinance` Yahoo Finance normalized snapshots may be used only as a clearly labeled secondary vendor source after independent checks. | Raw OHLC, distributions, splits, adjusted-close reconciliation. Never use adjusted prices for signal construction or silently apply vendor-adjusted levels as execution prices. |
| EURO STOXX 50, VSTOXX, EUN2 candidate | STOXX official methodology and index data; Deutsche Börse/Xetra and fund issuer product/corporate-action records. | STOXX's help page says public historical index access is limited to three months and full history requires a historical license. Do not access restricted history without an existing authorized entitlement. An ETF candidate cannot replace the underlying index for H1–H7. |
| Regimes | NBER U.S. business-cycle chronology for U.S. markets; CEPR Euro Area Business Cycle Dating Committee chronology for a European market if that market passes its data gate. | Ex-post description only. Historical labels never enter forecasts or trades. Record vintage/revision status. |
| Cash yields | Frozen Task 3 initial-release U.S. Treasury proxies for U.S. H8; for a European H8 replication, a separately registered EUR cash proxy would be required. | The U.S. rate is not silently applied to EUR assets. No market H8 result without currency-consistent, as-of rates or an explicit zero-cash benchmark. |

Documented source pages consulted at registration:

- Nasdaq-100 overview and history: <https://indexes.nasdaq.com/Index/Overview/NDX>.
- Nasdaq Global Index policies and methodologies: <https://www.nasdaq.com/products/global-indexes/policies>.
- Cboe VXN and RVX dashboards: <https://www.cboe.com/us/indices/dashboard/vxn> and <https://www.cboe.com/us/indices/dashboard/rvx>.
- Cboe selected broad-based volatility-index methodology: <https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Selected_Broad_Based_Index_Equity_and_ETF_Volatility_Indices.pdf>.
- FRED Cboe VXN and RVX distribution records: <https://fred.stlouisfed.org/series/VXNCLS> and <https://fred.stlouisfed.org/series/RVXCLS>.
- FRED Nasdaq-100 distribution record: <https://fred.stlouisfed.org/series/NASDAQ100>.
- STOXX VSTOXX description and methodology: <https://stoxx.com/index/v2tx/>.
- STOXX access and history rules: <https://www.stoxx.com/help> and <https://stoxx.com/legal/stoxx-conditions-of-use/>.
- STOXX index files guide: <https://www.stoxx.com/document/Resources/Technical%20Documentation/Index_Files_Guide.pdf>.
- FTSE Russell index resources: <https://www.lseg.com/en/ftse-russell/indices/russell-us>.
- NBER chronology: <https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions>.
- CEPR Euro Area chronology: <https://cepr.org/surveys-reports/euro-area-business-cycle-dating-committee>.

The cited pages document candidate definitions and access constraints, not accepted data freezes. Dataset eligibility is determined by actual acquired files and their audit. Because Cboe/FRED values are copyrighted and STOXX historical index levels are restricted, only hashes, metadata, and legally redistributable summaries will be committed; raw observations stay outside Git unless terms explicitly permit redistribution.

### Registration amendment (2026-10-15, before outcomes)

The author confirmed in this task that written permissions cover research use and public sharing of derived results from all proposed providers. This authorization does not waive provider login requirements or expand the stated license scope. No raw series will be committed. The specific license documents and their effective dates are not present in this checkout, so the reproducibility record will identify this reliance on the author's attestation and retain the original provider terms as constraints. If a provider requires authenticated access unavailable in this environment, that market remains blocked until its entitled data file is supplied.

## 3. Samples, alignment, and horizons

The candidate synchronized panel is **2007-01-01 through 2025-12-31**. It is used only for market/date cells with actual valid underlying, volatility-index, and target support. Forecast and portfolio evaluation begins in 2012 for H6–H8, preserving the original five-year training/warm-up design. Report each market's maximum admissible history separately, including first simultaneous valid predictor/underlying date, first supported target date, first honest OOS forecast date, and end date. No artificial common history is created.

For H1–H5, report both the maximum admissible market-specific sample and the synchronized 2007–2025 comparison where supported. H3/H4 forecasts must be strictly out of sample, with estimates using only information available at the origin and the original recursive GARCH specifications. A start later than 2007 is allowed only when a registered minimum-history or data-coverage gate requires it; the reason and the affected common mask are recorded before inference. H6–H8 use the original 2012–2025 common evaluation window, with the original warm-up and matured-label eligibility rules. Full forward outcomes after the last allowed 2025 origin may support that origin's target only; they may not create new origins.

Primary target: exact forward 30-calendar-day annualized close-to-close realized variance, using the market's own underlying price index. Mandatory robustness: 21 future scheduled local exchange sessions, annualized with the same market-specific convention as the source protocol. No SPY/QQQ/IWM ETF prices enter H1–H7 underlying targets. No weekends or holidays are manufactured. Realized targets use actual historical exchange sessions. Forecast-time horizon construction uses only regular sessions and holiday rules knowable at the forecast origin, not finalized future unscheduled closures. VIX/VXN/RVX/VSTOXX units are checked against provider definitions; percentage points are converted to decimal volatility before squaring. Any maturity, close-timestamp, or annualization mismatch is reported and blocks a pooled interpretation if it cannot be resolved.

Use local exchange dates as the primary key, retain source timestamps and IANA time zones, and explicitly handle DST. Do not shift dates to force US and European closes into false simultaneity. Synchronized cross-market inference pairs observations by the documented calendar-date rule and repeats on the exact shared-origin mask.

## 4. Hypothesis mapping and outcomes

All mappings preserve the parent protocols (`paper/method_protocol.md`, `paper/quant_extension_protocol.md`, and `paper/quant_failure_diagnostic_plan.md`). No market-specific model, target, threshold, training rule, or economic gate is selected after seeing its evaluation outcomes.

| Hypothesis | Replication and primary outcome |
|---|---|
| H1 | (IVAR_t=(IV_t/100)^2), (VRP^X_t=IVAR_t-RVAR^{CC}_{t,30c}). Report mean, median, dispersion, distribution, HAC 95% interval/test of the registered two-sided zero-mean null, and fixed period/regime sensitivities. Do not call this noisy ex-post proxy the conditional theoretical VRP. |
| H2 | (RVAR^{CC}_{t,30c}=\alpha+\beta IVAR_t+u_t); HAC inference and joint Wald test (\alpha=0,\beta=1), with the same common valid target mask. Calibration rejection is not irrationality or proof of inefficiency. |
| H3 | Compare implied variance, the original Gaussian expanding GARCH primary forecast, Student-t expanding and Gaussian rolling-five-year GARCH robustness, and the registered trailing-variance benchmark. Primary loss is squared error; report RMSE, MAE, QLIKE, paired overlap-aware HAC loss differences, and Holm-adjusted secondary families exactly as in the parent H3 protocol. Same dates, targets, units, and masks. |
| H4 | Original common-OOS encompassing regression (RVAR=\alpha+\beta IVAR+\gamma GARCH+u); test both incremental coefficients with registered robust inference. Same H3 mask and forecast construction; report collinearity and instability, not coefficient signs alone. |
| H5 | Regress the VRP proxy on an ex-post local recession indicator using the parent HAC design; fixed 2008/2020/2022 stress descriptions where each market's sample supports them. U.S. chronology for U.S. markets, CEPR chronology for Europe. These labels never affect forecasts/trades. |
| H6 | Original fixed event (1[RVAR^{CC}_{30c}>1.5 IVAR]), original A–D models, training-only scaling, monthly refits, matured labels, 500-row/class support gate, Brier primary and fixed secondary metrics/10% retrospective alert budget. Thresholds and practical screen remain unchanged. |
| H7 | Original six forecasts (IVAR, cached/recursive Gaussian GARCH, trailing-30, EWMA, HAR-style ridge, nonnegative IVAR/GARCH/trailing combination), fixed model training and QLIKE primary. Report each constituent and full out-of-sample inference. |
| H8 | Original five policies (buyhold, trailing, VIX/implied, GARCH, combination), mapped only to the market's corresponding investable proxy. Preserve 10% target, long-only 0–100% cap, next-open execution, distributions, cash, fees, and all original costs. U.S. uses Task 3 as-of cash-rate scenarios; Europe requires an approved EUR cash-yield protocol. |

For all hypotheses retain full-sample metrics, post-2014 sensitivity (or the market-specific documented methodology transition), fixed 2012–2016/2017–2021/2022–2025 panels for H6–H8, and relevant prescribed 21-trading-session and non-overlap sensitivities. No crisis deletion, arbitrary winsorization, or evaluation-selected specification.

## 5. Cross-market inference and multiplicity

Within-market estimation remains primary. Cross-market contrasts are differences in the relevant estimand on the exact synchronized mask, with effect size, confidence interval, and adjusted p-value. Correlated markets are not independent replications. Primary inference for U.S. pairwise differences uses synchronized paired circular block bootstrap (block 63 trading dates, 1,000 resamples, seed 1729) and HAC sensitivity; the European market, if admissible, uses its own local chronology and a separately reported synchronized-date sensitivity. Blocks preserve serial dependence, within-date market dependence, and overlapping horizons. Also report 21- and 126-session block sensitivities. Retain valid-draw counts; do not treat bootstrap intervals as prospective guarantees.

Use two-sided 5% tests and 95% intervals. Apply Holm family-wise adjustments across the predeclared new-market primary H1–H5 market contrasts and within the existing H6/H7/H8 test families; show raw and adjusted values. Label exploratory all-market and subgroup comparisons. Report effect magnitudes and uncertainty even when tests do not reject. Missing coverage, low power, or unavailable data yields a blocked/inconclusive cell, never a null conclusion.

## 6. Recession, crisis, and market-structure sensitivities

Use jurisdiction-specific published chronology; it is retrospective descriptive classification only. Keep the U.S. 2008/2020/2022 case windows as already frozen. For Europe, use CEPR peak-to-trough months only where the committee chronology covers the date; no U.S. NBER labels are projected onto Europe. Index methodology changes, option-universe changes, volatility-series starts, fund inception, dividend conventions, and market-calendar differences are recorded by date. Post-2014-10-06 is retained for comparability with the VIX weekly-option transition but is not presumed to be the relevant transition for VXN or RVX; document and report their actual change points separately.

Robustness set: synchronized 2007–2025 versus maximum market history; 30-calendar-day versus 21-local-session targets; registered alternative realized-variance estimators where source inputs support them; all original GARCH variants; non-overlapping target origins; parent HAC lag sensitivities; post-2014 and fixed periods; fixed crisis windows; data-source overlap/revision checks; and strategy-cost/cash-yield sensitivities. Any additional outcome-motivated analysis is labeled post hoc and cannot replace primary results.

## 7. Data audit, missingness, and adversarial checks

Preserve separate raw, validated, quarantined, and research-ready layers. Freeze deterministic SHA-256 manifests and record exact provider revision/vintage where possible. Validate date uniqueness/order, missing observations against exchange calendars, OHLC relationships, return discontinuities, percent/decimal units, annualization, ETF splits/dividends, close timestamps and time zones, methodology transitions, and source-revision overlap. No silent interpolation, backfill, calendar completion, or cross-source splice.

Tests must inject future unscheduled closures and delayed/revised observations and prove earlier predictions remain unchanged; test calendar holiday/DST alignment, minimum matured training history, future-fit reuse, target leakage, variance-horizon identity, correct unit scaling, ETF distribution/split accounting, next-open execution, and deterministic hashes. Tests assert numeric behavior and fail-closed exclusions. Existing frozen S&P 500 manifests, results, source files, and H8 ledgers are hash-checked before and after.

## 8. Decisions, gates, and interpretation

At each stage report `SUPPORTED`, `REJECTED`, `INCONCLUSIVE`, `EXPLORATORY`, or `BLOCKED`, with its exact registered criterion. Failure to reject is not evidence of a true null. A smaller forecast error without adjusted uncertainty is not superiority. A cash-based return increase is not evidence of alpha, nor is a Treasury quote a broker compensation promise. A forecast gain is not economic utility. Market-level findings generalize only to the documented sample, instruments, conventions, and assumptions.

No primary outcome is generated until this protocol is committed. Source or model deviations require a dated, committed amendment before the affected outcome is calculated. Do not purchase data, access restricted data, contact providers, or distribute copyrighted observations without authorization already available in the repository/account. If data are unavailable under current access, complete admissible U.S. markets and report European/optional markets as blocked with evidence and exact acquisition path needed for continuation.

## 9. Reproducibility and outputs

Use a separate versioned namespace `outputs/cross_market/v1` and manifests under `data/manifests/cross_market_*_v1.json`; preserve all original and Task 1–3 namespaces byte-for-byte. Each output records protocol commit, code revision, source/data hashes, environment, configuration, random seed, masks, failures, and output hashes. Raw restricted data are not committed. Reports and tables distinguish replay from committed compact artifacts versus reruns requiring licensed/reacquired data.

The final research report must include market-level H1–H8 results, coverage and source limits, synchronized inference, robustness, blocked cells, reproducibility instructions, and a consolidated status table. All conclusions remain provisional pending independent coauthor review; no PR merge is authorized.
