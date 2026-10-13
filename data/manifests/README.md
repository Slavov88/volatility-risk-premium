# Sanitized acquisition manifests

This directory is intentionally version-controlled.

Each reviewed production acquisition should contribute a compact JSON or Markdown manifest containing reproducibility metadata but **no restricted provider market data**.

At minimum record:

- dataset and scientific role;
- retrieval timestamp;
- source URLs/endpoints;
- request parameters;
- software/library versions;
- coverage and row counts;
- schema and missingness;
- SHA-256 hashes of local immutable artifacts;
- validation results and discrepancy summary;
- TLS/transport verification status;
- exchange-calendar name, exact calendar-library version, and expected session count;
- any licensing/redistribution note.

Raw files referenced by these hashes remain local under `data/raw/`.

The 2026-10-13 interim manifests additionally record communicated
authorization, the one expressly authorized archival insertion (date/value/
cell), source-code/commit identities and derived output hashes. Target audit,
descriptive aggregates and alternate-close sensitivity metadata contain no
raw market-price rows. Independent scientific acceptance remains pending.
