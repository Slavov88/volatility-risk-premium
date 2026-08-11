# Methodology decisions

**Decision record date:** 2026-08-10
**Result-state at decision:** No empirical VRP or forecast-ranking results had
been generated. Locked decisions cannot be changed after results are inspected.

| ID | Decision | Status | Rationale / implementation consequence |
|---|---|---|---|
| D-001 | Primary proxy is \(VRP^X_t=IVAR_t-RVAR_{t,H}\), explicitly an **ex-post variance-risk-premium proxy**; \(VOLGAP_t=IVOL_t-RVOL_{t,H}\) is secondary and is never called VRP. | Locked 2026-08-10 | Preserves variance units and the implied-minus-realized sign while distinguishing the unobserved conditional theoretical premium. |
| D-002 | Store returns, volatility, and variance as decimals; convert VIX by \(IVOL=VIX/100\), then square to \(IVAR\). | Locked 2026-08-10 | Prevents unit drift and factors-of-100 errors. |
| D-003 | Primary target is the actual 30-calendar-day forward return-date set, annualized by \(365/30\); 21 trading days is robustness with 20/22 sensitivities. | Locked 2026-08-10 | Matches the constant-calendar-horizon research object without shortening end targets. |
| D-004 | Close-to-close is the primary realized-variance estimator; Parkinson and Garman-Klass are robustness estimators. | Locked 2026-08-10 | Estimator disagreement is reported and explained; it is not a fifth formal hypothesis. |
| D-005 | Use exactly H1 mean proxy, H2 calibration, H3 VIX-versus-GARCH OOS MSE loss differential, and H4 NBER regime equality. | Locked 2026-08-10 | Limits multiplicity and removes the obsolete formal H5. |
| D-006 | Fixed-21 HAC uses `maxlags=20`; calendar-target \(L_0\) is derived mechanically from overlap, with 42/63 sensitivities and one predetermined non-overlap sample. | Locked 2026-08-10 | Inference acknowledges induced serial dependence without bandwidth selection on results. |
| D-007 | Primary OOS design uses the first ten complete aligned calendar years and expanding re-estimation at every origin. | Locked 2026-08-10 | Rolling ten-year, post-2003, and 2010+ designs are robustness only. |
| D-008 | Formal regimes are NBER recession versus non-recession. The classification attaches to forecast origin \(t\), is used ex post only, and is never a predictor. Under the monthly external chronology, every eligible daily origin inherits the value for its calendar month. The chronology version and deterministic daily mapping must be recorded before H4. The 2008, 2020, and 2022 episodes remain separate case studies. | Locked 2026-08-10 | Prevents look-ahead interpretation, makes daily-origin labeling reproducible, and avoids treating economically distinct episodes as one homogeneous regime. |
| D-009 | Primary long-history exact-index OHLC candidate is Yahoo Finance `^GSPC` with `auto_adjust=False`; FRED `SP500` close validates overlap; SPY remains engineering-only. | Locked 2026-08-10 | Persist an immutable normalized Yahoo acquisition snapshot plus fetched FRED response bytes, hashes, manifests, discrepancy reports, and software-version provenance. |
| D-010 | VIX is a model-free SPX option-strip measure, never a single-option Black-Scholes IV. | Required invariant | Mandated by the proposal and current Cboe methodology. |
| O-001 | Map the free Cboe historical CSV `CLOSE` field to an exact daily timestamp/convention across history. | Open provenance limitation; not an implementation blocker | Operationally, daily VIX `CLOSE` is the end-of-day predictor at origin \(t\), and its target begins with the first return ending strictly after \(t\). Current primary documents support a last RTH value near 4:15 p.m. ET but do not bind every historical observation to that timestamp; no exact synchronization with the normally 4:00 p.m. SPX cash close is assumed. |
| O-002 | Aggregate daily GARCH conditional variances to the variable-session 30-calendar-day target used in H3. | Open before H3 | Before comparison, lock and test the rule that sums conditional variances for exchange sessions with return-ending dates \(t<d\leq t+30\) calendar days and annualizes the sum by \(365/30\). The timing, exchange calendar, and missing-session behavior must be frozen before forecast rankings are inspected. |

## Non-negotiable implementation tests

- Date-labelled inputs prove the primary target includes only return-ending
  dates \(t<d\leq t+30\) calendar days and rejects shortened final targets.
- Altering data after an origin cannot change its predictor.
- Competing forecasts use an identical target/date mask.
- Dimensional checks distinguish variance from volatility and percentage points
  from decimals.
- Acquisition artifacts and source bytes, SHA-256 hashes,
  schema/coverage/missingness, software versions,
  and row-loss reports are generated rather than hand-written.
