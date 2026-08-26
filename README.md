# Volatility Risk Premium

Reproducible research code for **The Volatility Risk Premium: An Empirical and Theoretical Investigation of the Gap Between Implied and Realized Volatility in Equity Index Markets**.

## Research question

Is the excess of S&P 500 option-implied variance over subsequently realized variance statistically robust and economically explicable, or does it weaken after careful horizon matching, overlap-aware inference, out-of-sample forecasting, and regime analysis?

This is a financial-economics research project. It is not a trading strategy, a return-prediction competition, or an exercise with a pre-selected conclusion.

## Two-track design

- **Track A — theory and small-scale validation:** derive Black–Scholes, implement a European-option pricer and implied-volatility inversion, and validate them on a small set of quotes.
- **Track B — large-N empirical study:** acquire VIX and S&P 500 index data, construct forward realized-variance targets, estimate an ex-post variance-risk-premium proxy, use overlap-robust inference, and compare VIX with genuinely out-of-sample GARCH and naive forecasts.

VIX is a model-free index constructed from a strip of SPX option prices. It is not the Black–Scholes implied volatility of one option.

## Source of truth

The authoritative pre-analysis specification is [`paper/method_protocol.md`](paper/method_protocol.md), dated 2026-08-26. Earlier design drafts remain in Git history, while [`docs/methodology_decisions.md`](docs/methodology_decisions.md) records how the specification evolved before empirical VRP or forecast-ranking results were generated.

## Canonical empirical objects

| Symbol | Definition | Role |
|---|---|---|
| `IVOL_t` | `VIX_t / 100` | Annualized decimal implied volatility. |
| `IVAR_t` | `IVOL_t**2` | Annualized decimal implied variance. |
| `RVAR_t,30c` | `(365 / 30) * sum(r_d**2 for t < d <= t + 30 calendar days)` | **Primary** annualized forward realized variance. |
| `RVOL_t,30c` | `sqrt(RVAR_t,30c)` | Primary-horizon realized volatility. |
| `VRP_X_t` | `IVAR_t - RVAR_t,30c` | **Primary ex-post variance-risk-premium proxy.** |
| `VOLGAP_t` | `IVOL_t - RVOL_t,30c` | Secondary intuitive volatility gap. |
| `RVAR_t,21t` | `(252 / 21) * sum(next 21 trading-day squared returns)` | Mandatory horizon robustness target. |

The sign convention is always **implied minus realized**. The theoretical conditional object `E_t^Q[variance] - E_t^P[variance]` is not directly observed.

## Methodological invariants

1. A predictor formed at date `t` is compared only with returns realized strictly after `t`.
2. The primary target is the exact forward **30-calendar-day** interval because VIX is a constant 30-day measure.
3. The fixed **21-trading-day** target is mandatory robustness, not the primary estimand.
4. Rolling targets require HAC/Newey–West or deterministic non-overlapping inference.
5. VIX, GARCH, and naive forecasts use the same target, horizon, units, dates, and missing-value mask.
6. Internal volatility and variance units are decimal annualized quantities; percentage conversion is presentation only.
7. No empirical claim enters the paper until it is reproducibly generated and audited by the other coauthor.

## Current status

The repository contains a locked pre-analysis protocol, research-design documentation, literature and VIX notes, and a tested exact-index acquisition layer. No empirical VRP, forecast-ranking, or crisis result should be treated as established until the post-protocol pipeline is implemented and audited.

The Yahoo/FRED feasibility comparison identified several close discrepancies that must be investigated during cleaning, and the earlier Yahoo feasibility acquisition used a local TLS-verification workaround. The final core-data freeze must use verified TLS.

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Reproduce the exact-index core acquisition

The confirmatory sample ends on 2025-12-31, so the canonical acquisition request uses an exclusive 2026-01-01 end:

```bash
vrp-download-spx --start-date 1990-01-02 --end-exclusive 2026-01-01
```

The command requests Yahoo Finance `^GSPC` with `auto_adjust=False`, rejects current-day bars, stores an immutable normalized acquisition snapshot, preserves FRED validation response bytes, records hashes and metadata, and reports close discrepancies without silently correcting either source.

After a reviewed production acquisition, copy a sanitized provenance manifest into `data/manifests/`; raw provider files remain ignored by Git.

### Legacy feasibility utility

The initial source-access utility remains for reproducibility only:

```bash
vrp-download-samples --start-date 2026-05-01 --end-date 2026-08-10
```

It includes an engineering-only SPY sample and a provisional Treasury source. SPY must never replace the S&P 500 price index in the core study.

Run tests with:

```bash
pytest
```

## Repository map

```text
data/raw/              Local immutable acquisition artifacts (ignored)
data/manifests/        Sanitized provenance manifests (tracked)
data/processed/        Reproducibly generated cleaned/analysis data (ignored except README)
docs/                  Research design, sources, methodology, and literature notes
paper/                 Locked protocol, regime definitions, deviations, manuscript
src/vrp/               Reusable research code
tests/                 Unit and integration tests
```

## Data and result provenance

Every production acquisition must record source URL, retrieval timestamp, request parameters, SHA-256 digest, schema, coverage, missingness, software version, validation results, and TLS/transport status. Restricted or redistributable-provider data remain local; compact sanitized manifests are committed so the provenance of local snapshots is independently auditable.
