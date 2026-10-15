# empirical results summary

**PROVISIONAL — PENDING INDEPENDENT COAUTHOR REVIEW**

Aleksandar authorized provisional execution before Venelin's independent review on 2026-10-13. No independent acceptance/signature is implied. Protocol 1.1.0 and interim amendment remain fixed.

Input freeze SHA-256 `1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4`; target manifest SHA-256 `00532571aad5f8d9c43231933429fe6facbf7687a6332231ac8b7ad0ff73ccd9`. Result source hashes: `h1_h2.json: 6b07e43199d3ffd723e42c8ed3bf497c800421f79a6c56b33b95d9e9d67d5a25`, `h3_h4.json: 03afa02ed0e6087ab507fcde105a066b591b74b10a9826cce553ce4310d5a1a5`, `h3_h4_post2014.json: f29223a7fcc2b21145a6be9901cf002dca3ae80878c0339111f4e7513c022ddf`, `h5.json: b2945442db51261cc5fde5555eab806e8413b35dc26a5292cfe6d80f49937b90`, `execution_audit.json: a37a4b74db24de665e0d1e109f237367a8f2c0110ada5d4a0ea8e106f38caeb6`.

Point estimates use the frozen untrimmed sample; Bartlett HAC finite-sample correction N/(N-k), asymptotic normal confidence intervals/p-values, joint Wald chi-square where specified. Independent numpy least-squares and score-sandwich checks passed. Numeric p=0 in diagnostics means floating-point underflow, not a mathematical zero. Full numerical precision is retained in source JSON.

## Completed provisional empirical evidence

| Hypothesis | N | Primary estimate/test | Two-sided p | Status |
|---|---|---|---|---|
| H1 | 9064 | mean 0.01134891366; CI [0.007227904639, 0.01546992268] | 6.754702197667221e-08 | COMPUTED / PROVISIONAL |
| H2 | 9064 | joint chi² 42.50628358 | 5.886779893371626e-10 | COMPUTED / PROVISIONAL |
| H3 | 4780 | VIX-GARCH squared-loss mean -0.0004917178918 | 0.36109363333697164 | COMPUTED / PROVISIONAL |
| H4 | 4780 | gamma 0.2054921121; beta 0.6796657461 | gamma 0.3231234765139437; beta 0.00011860116942981839 | COMPUTED / PROVISIONAL |
| H5 | 9064 | delta -0.004222432517 | 0.8055478536097032 | COMPUTED / PROVISIONAL |

Full-sample H1 and H2 reject their nulls. Later-sample CC results weaken; primary post-2014 H1/H2 are not significant. VIX lower RMSE does not establish a significant paired advantage; GARCH has smaller MAE. Primary encompassing favors a VIX increment but not a GARCH increment; rolling robustness differs. Primary recession differences are uncertain; crisis mean premiums are negative in 2008 and 2020 while 2022 is positive. Negative/insignificant/contradictory outputs are preserved.

No result directly observes the theoretical conditional premium, establishes risk compensation, causality, irrationality or market efficiency. No manuscript conclusions were added. All three GARCH variants cover 4780 origins with zero failures, but near-unit persistence and residual-model diagnostics remain material. Review all hypotheses jointly without outcome-selected source/window/bandwidth changes.

Independent review tasks: reproduce exact source/target hashes; inspect the author-reported methodology and explicit Aleksandar execution authorization; verify H1/H2 HAC/Wald oracles and all robustness; audit chronological training/checkpoints/forecast recurrence/common masks; inspect parameter persistence and 38 residual anchors per variant; validate NBER monthly mapping and frozen case windows; inspect generated tables/figures. CI is implementation qualification, not independent scientific acceptance. If rejected, record a versioned revision and full re-execution preserving this baseline. Next concrete action: Venelin audits this complete review package.

Reports: [H1](h1_results.md), [H2](h2_results.md), [H3](h3_results.md), [H4](h4_results.md), [H5](h5_results.md). Figures/tables are reproducibly generated under `outputs/empirical_h1_h5/v1/publication/`; provider price files remain ignored.

## Cross-market extension (separate provisional evidence)

Nasdaq-100/VXN H1–H8 results, synchronized S&P comparisons, source coverage gates, exact output hashes, and remaining Russell/Europe blockers are documented in [cross_market_replication.md](cross_market_replication.md), [cross_market_results.md](cross_market_results.md), and [cross_market_data_provenance.md](cross_market_data_provenance.md). These exploratory results do not revise the S&P estimates above. Independent review remains pending.
