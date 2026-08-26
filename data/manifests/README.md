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
- any licensing/redistribution note.

Raw files referenced by these hashes remain local under `data/raw/`.
