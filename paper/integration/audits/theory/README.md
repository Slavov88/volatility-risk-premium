# Theory delivery — 2026-11-02

Version: theory-delivery/1.0.0. Prepared from repository commit
`27735e5653b5b778fb0e23ccc3e9079d4bdd6aa3` and the locked protocol 1.1.0 plus
its recorded interim/provisional execution supplements. No protocol choice,
raw market data, confirmatory result or repository commit was changed here.

## Contents

- `theory.md`: manuscript-ready theoretical framework and focused literature
  synthesis. It retains the original BSM sections and adds an explicit normal
  truncated-moment derivation, variance-swap/log-strip replication, jump
  correction, monitoring limits, VIX maturity interpolation/history, pricing
  kernel interpretation, sign mapping, and numerical validation evidence.
- `option_replay.md`: exact generated historical W3-02 validation report carried
  forward from the earlier theory work; six QuantLib cases and six fixed SPX
  quote rows. This is Track A, not a Track B empirical result.
- `check_theory.py` and `theory_checks.json`: independent Gaussian payoff and
  continuous-strip quadrature checks plus the six fixed-quote replay.
- `source_audit.md`: primary-source URL checks and access limits.

## Reproduce numerical checks

From the scratch workspace, run:

```bash
PYTHONPATH=repo/src prov-env/bin/python theory-delivery/check_theory.py
```

Replayed successfully 2026-11-02 with Python 3.12.14, SciPy 1.17.1 and
QuantLib 1.43 (repository optional validation dependency pins QuantLib 1.43).
Output matches `theory_checks.json`: six payoff cases, six strip cases and
six of six quote repricings inside their spreads. The quadratures check
analytic diffusion identities, not real-world exact replication or jump
errors. The fixed quotes are already embedded limited example rows; no
full licensed quote chain is redistributed.

The historical report's upstream provenance is
`repo/data/manifests/w3_02_option_quote_sample.json`: source ZIP SHA-256
`8517b069f4d41e44f950dc79a3cdab694359b0fae91664190011e39dd8e48b76`,
and 2022-09-15 CSV hash recorded from the source manifest
`054acc61106b15a21a2b166e975a506fb0559b9a8d7ec896817ab5e6eb8c208a`.
This delivery replays the preserved six rows and does not claim to have
re-downloaded or independently rehashed the full archive.

## Editorial integration

Replace the existing theory chapter with `theory.md` and deduplicate its
references against the manuscript's master list. Literature findings are
motivations, not this project's findings. Carr–Wu's negative realized-minus-
swap-rate premium maps to this project's positive implied-minus-realized
convention. The 2026 methodology is expressly identified as current
reference documentation; its operational details are not projected
unchanged into the historical sample. Keep all Track B empirical outputs
provisional pending independent review, as required by the execution
supplement. Nothing in this chapter implies coauthor acceptance.
