# Volatility Risk Premium coauthor review draft

Start with `manuscript.pdf` for the paper and `supplement.pdf` for complete reporting. Editable sources are `manuscript.md` and `supplement.md`. Vector figures and supplementary CSVs are in `figures/` and `tables/`.

`COAUTHOR_REVIEW.md` identifies outstanding scientific decisions and exact-replay gaps. `REPRODUCIBILITY.md` gives environment, inputs, commands and evidence grades. `claim-audit.md` maps numerical claims to source selectors, while `audit-keys.md` identifies the original core results. `audits/` contains source recovery, independent inference, fresh-fit comparisons, theoretical checks, reviews and test receipts.

The core uses the locked 30-calendar-day window, the 21-trading-day robustness window and implied-minus-realized convention. H3/H4 use the corrected calendar record. H6–H8 and the Nasdaq comparison are exploratory. Every empirical result remains provisional pending independent coauthor acceptance. The package preserves the remaining source-chain, historical replay and cross-market inference gaps.

The integration PR targets the cross-market branch so its diff isolates the final manuscript and verification materials from the accumulated prior research. The prior branches and artifacts remain available at the commits in `RESEARCH_PLAN.md`.
