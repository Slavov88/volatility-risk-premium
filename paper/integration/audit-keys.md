# Numerical source ledger


All printed empirical values are rounded from the following repository artifacts. Selectors use semantic field matches, not an assumed stable array order. Repeated abstract values inherit the same keys as their detailed results sections. Dates, design constants, and acquisition counts follow Sources E and I rather than statistical estimation.

**A.** `data/manifests/2026-10-13_h1_h5_execution_v2.json`: use `primary_results.h1`, `.h2`, and `.h5` and `garch_summary` only. Its historical H3/H4 fields are superseded and are not sources for this manuscript's forecasting estimates.

**B.** `data/manifests/empirical_calendar_repair_results_v1.json`: select `analyses[]` by `variant`, `period`, `family`, `horizon` and `mask`; use only `corrected.metrics` and `corrected.tests`, with test records selected by `lag`. Primary is `normal_expanding/full/cc/30c/overlapping`, lag 21. The corrected producer source hash recorded in `docs/h3_h4_corrected_results.md` is `f5ca96f49726028f830594c0f824e93f4a15894b31c4bfd697e89302554102fa`.

**C.** `docs/h3_h4_corrected_results.md`: publication companion identifying corrected-only H3/H4 tables, controls, repair scope, and supersession.

**D.** `docs/empirical_results_summary_calendar_v1.md`: status and summary companion; it does not supersede detailed numerical artifacts.

**E.** `paper/protocol_deviations.md`: dated interim CLOSE amendment, later provisional-execution authorization, data-source history, and pending review. Read alongside `paper/method_protocol.md` version 1.1.0.

**F.** `docs/h1_results.md`: full precision summary/extrema and robustness table. Row keys are subset/estimator/horizon/object/HAC lag. Underlying `h1_h2.json` SHA-256: `6b07e43199d3ffd723e42c8ed3bf497c800421f79a6c56b33b95d9e9d67d5a25`.

**G.** `docs/h2_results.md`: coefficient and calibration robustness tables. Row keys are subset/estimator/horizon/lag; underlying source is the same `h1_h2.json` as F.

**H.** `docs/h5_results.md`: regime regression and frozen-year tables. Underlying `h5.json` SHA-256: `b2945442db51261cc5fde5555eab806e8413b35dc26a5292cfe6d80f49937b90`. Corrected borrowed forecast-loss companions are not used for the crisis proxy means in this text.

**I.** `paper/method_protocol.md`, `paper/regime_definitions.md`, and `docs/h3_h4_calendar_correction.md`: design constants, fixed case windows, and forecast calendar information restriction. Input freeze SHA-256: `1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4`; target manifest SHA-256: `00532571aad5f8d9c43231933429fe6facbf7687a6332231ac8b7ad0ff73ccd9`.