# Volatility Risk Premium

Reproducible research code for **The Volatility Risk Premium: An Empirical and
Theoretical Investigation of the Gap Between Implied and Realized Volatility in
Equity Index Markets**.

## Research question

Is the excess of S&P 500 option-implied variance over subsequently realized
variance statistically robust and economically explicable, or does it weaken
after accounting for overlapping observations, non-normality, forecast
construction, and market regimes?

This is a financial-economics replication and extension project. It is not a
trading strategy, a return-prediction competition, or an exercise with a
pre-selected conclusion.

## Two-track design

- **Track A - theory and small-scale validation:** derive Black-Scholes,
  implement a European-option pricer and implied-volatility inversion, and
  validate them on a small set of quotes.
- **Track B - large-N empirical study:** acquire VIX and equity-index data,
  construct forward realized-variance targets, estimate the ex-post variance-
  risk-premium proxy, use robust inference, and compare VIX with genuinely out-
  of-sample GARCH variance forecasts.

VIX is a model-free index constructed from a strip of SPX option prices. It is
not the Black-Scholes implied volatility of one option. The two tracks use
related but distinct objects.

## Current status

The repository has a current pre-analysis methodological specification and a
tested exact-index acquisition layer. No empirical VRP,
forecast-ranking, or crisis result has been estimated yet. Any expected sign in
the protocol is a literature-motivated hypothesis, not a project finding.

The current empirical-track work products are:

- the substantively locked research design and analysis protocol, recorded in
  version control and awaiting coauthor review;
- VIX methodology and terminology notes;
- an eight-source literature matrix;
- a tested acquisition architecture and local feasibility snapshots for Cboe
  VIX, Treasury rates, and engineering-only SPY data; and
- the Yahoo Finance `^GSPC` exact-index OHLC pipeline with
  `auto_adjust=False`, immutable manifests, and FRED `SP500` close validation.

## Canonical notation

| Symbol | Definition | Role |
|---|---|---|
| `IVOL_t` | `VIX_t / 100` | Annualized decimal implied volatility. |
| `IVAR_t` | `IVOL_t**2` | Annualized decimal implied variance. |
| `RVAR_t,30c` | `(365 / 30) * sum(r_d**2 for t < d <= t + 30 calendar days)` | Primary annualized forward realized variance. |
| `RVOL_t,30c` | `sqrt(RVAR_t,30c)` | Annualized forward realized volatility. |
| `VRP_X_t` | `IVAR_t - RVAR_t,30c` | Primary **ex-post variance-risk-premium proxy**. |
| `VOLGAP_t` | `IVOL_t - RVOL_t,30c` | Secondary volatility gap; never called VRP. |

The empirical sign convention is always implied variance minus realized
variance. The theoretical conditional object
`E_t^Q[variance] - E_t^P[variance]` is not directly observed.

## Methodological invariants

1. A forecast formed at date `t` is compared with volatility realized **after**
   `t`; predictor construction must not access future observations.
2. The primary target uses actual return-ending dates strictly after `t` and no
   later than `t + 30` calendar days; incomplete end targets are rejected.
3. Overlapping targets require HAC/Newey-West inference and a predetermined
   non-overlapping robustness design.
4. VIX and GARCH forecasts must be evaluated against the same realized
   target, horizon, units, and test dates.
5. Internal volatility units are decimal annualized volatility; percentages are
   presentation-only conversions.
6. No empirical claim enters the paper until generated reproducibly and audited
   by the other coauthor.

See [the current protocol](paper/method_protocol.md),
[methodology decisions](docs/methodology_decisions.md), and
[the VIX note](docs/vix_methodology.md).

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Reproduce exact-index acquisition

The core empirical-track command uses an inclusive start and exclusive frozen
end:

```bash
vrp-download-spx --start-date 1990-01-01 --end-exclusive 2026-08-10
```

It requests Yahoo Finance `^GSPC` with `auto_adjust=False`, rejects any current-
day bar, and persists an immutable normalized acquisition snapshot. The Yahoo
artifact is produced from the `yfinance` DataFrame by schema and numeric
normalization, date normalization and sorting, and deterministic CSV
serialization; it is not a byte-identical Yahoo network response. The command
also stores the FRED validation response as fetched bytes, records hashes and
manifest metadata, and reports close discrepancies without correcting the
persisted Yahoo values. See [data source feasibility](docs/data_sources.md).

### Legacy feasibility utility

The following source-access utility is retained for reproducibility of the
initial feasibility check, not as the core empirical-data pipeline:

```bash
vrp-download-samples --start-date 2026-05-01 --end-date 2026-08-10
```

It includes an engineering-only SPY sample. SPY is not part of the final
empirical dataset and must never replace the S&P 500 index.

Run the test suite with:

```bash
pytest
```

## Repository map

```text
data/                  Local raw/interim/processed data (downloads ignored)
docs/                  Research design, source, methodology, and literature notes
paper/                 Pre-analysis protocol and eventual manuscript
src/vrp/               Reusable research code
tests/                 Unit and integration tests
```

## Data and result provenance

Every acquisition records the source URL, retrieval timestamp, SHA-256 digest,
byte count, schema, coverage, and missingness. Provider responses stored as
fetched bytes remain distinguishable from normalized acquisition snapshots.
Processed data will be rebuilt from these immutable acquisition artifacts;
cleaning decisions and row losses will be logged.

Source and licensing restrictions may prevent redistributing some raw files.
The repository therefore tracks code and provenance, not unreviewed bulk data.
