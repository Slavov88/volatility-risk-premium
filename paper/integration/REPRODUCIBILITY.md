# Reproduce the paper and assess the evidence

The integration starts at cross-market commit `27735e5653b5b778fb0e23ccc3e9079d4bdd6aa3`. `RESEARCH_PLAN.md` pins all source branches. The manuscript uses the corrected calendar record at `b03686ece031038b9daba03a9a4b1990d4e95674`. The earlier empirical-production H3/H4 fields remain historical. H1/H2/formal H5 come from the unchanged empirical record, checked against fresh observations. All results remain provisional pending independent coauthor acceptance.

## Environment

The research dependencies are the repository's `requirements-dev.lock` and `requirements-quant-extension.lock`. The original execution record used Python 3.11.5. This reconstruction used CPython 3.12.14 on Linux with NumPy 2.4.6, SciPy 1.17.1, pandas 2.3.3, statsmodels 0.15.0, arch 8.0.0 and exchange-calendars 4.13.2. Package locks match, while Python/platform differ. The cause of historical target-byte differences is not established. The package inventory and runtime receipt record the actual environment.

Run from the repository root. Use a clean virtual environment and keep provider data in a private directory. The following commands illustrate an installation, not a claim that any later environment is the historical runtime.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.lock -r requirements-quant-extension.lock
python -m pip install -r paper/integration/requirements-paper.lock
python -m pip install -e . --no-deps --no-build-isolation
export PYTHONPATH="$PWD/src"
python -m pytest
```

The integration suite completed 1,839 tests. Its log is `audits/integration-tests.log`. A separate corrected-branch provenance run passed 1,816 tests. These checks do not accept a source or grant scientific approval.

## Public artifacts and arithmetic

```bash
python paper/integration/make_exhibits.py
python paper/integration/audits/econometrics/audit_core_results.py "$PWD"
python paper/integration/audits/extensions/verify_extensions.py
python paper/integration/verify_package.py
```

The first command builds the summary exhibits and full corrected H3/H4 tables from hash-pinned public manifests. The next two check aggregate identities and tracked Git blobs. The extension checker requires the original commit objects, so use a full clone. It does not recreate private per-origin predictions or ETF ledgers. `verify_package.py` checks the final package's byte inventory. Run it before regenerating figures because producer/library metadata can change their byte hashes. The CSV tables remain the full numerical supplement.

## Recover private core observations

The recovery script downloads free official Cboe history/workbook and a Yahoo chart response with verified TLS. It accepts only the normalized historical SPX digest, original Cboe prefix digest and workbook digest. If a provider revises historical values, the script fails and that failure requires investigation. It does not change the source policy.

```bash
python paper/integration/audits/recover_core_sources.py /PRIVATE/archive
python paper/integration/audits/provenance/rebuild_recovered.py \
  "$PWD" /PRIVATE/archive /PRIVATE/build-a
python paper/integration/audits/provenance/rebuild_recovered.py \
  "$PWD" /PRIVATE/archive /PRIVATE/build-b
```

An already downloaded archive can be tested using `--archive /PRIVATE/old-downloads`. Core raw inputs and reconstructed observations are intentionally excluded from the public package. Source recovery reproduces three original freeze CSV hashes and the target audit hash. Two fresh builds produced the same eight output hashes. Their daily-return and six-target digests differ from the original recorded outputs. The original SPX acquisition manifest and historical FRED SP500 response are missing, so the complete original provenance chain remains unverifiable. The strict VIX acquisition remains rejected. The recovery script is not a replacement manifest and does not satisfy the independent freeze gate.

The private target files below are under `interim/40113d6646b0e7b8/targets/bd7a172882ded86f` inside the chosen build directory. Define paths to that directory and a new private fit directory explicitly.

```bash
vrp_target_dir=/PRIVATE/build-a/interim/40113d6646b0e7b8/targets/bd7a172882ded86f
vrp_fit_dir=/PRIVATE/fresh-fits
python paper/integration/audits/econometrics/independent_core.py \
  "$PWD" "$vrp_target_dir/six_forward_targets.csv" \
  "$vrp_target_dir/canonical_daily.csv" /PRIVATE/core-audit.json
for variant in normal_expanding t_expanding normal_rolling5y; do
  python paper/integration/audits/econometrics/fresh_refits.py \
    "$PWD" "$vrp_target_dir/six_forward_targets.csv" \
    "$vrp_target_dir/canonical_daily.csv" "$vrp_fit_dir" "$variant"
done
python paper/integration/audits/econometrics/compare_fresh.py \
  "$PWD" "$vrp_fit_dir" /PRIVATE/fresh-comparison.json
python paper/integration/audits/econometrics/independent_forecast_inference.py \
  "$vrp_target_dir/six_forward_targets.csv" "$vrp_fit_dir" /PRIVATE/forecast-audit.json
python paper/integration/audits/econometrics/garch_diagnostics.py \
  "$vrp_target_dir/canonical_daily.csv" "$vrp_fit_dir" /PRIVATE/garch-diagnostics.json
```

Fresh fitting uses the registered producer routine. Independent NumPy inference checks use separate covariance code. Every model completed 4,780 origins, all 72 masks matched, and no reported p-value crossed 5%. The complete fresh aggregate results and numerical difference receipt are stored losslessly as `.json.gz`; their decompressed SHA-256 values are recorded. They can be read using Python `gzip.open` or `gzip -dc`. Private checkpoint payloads and raw market observations are excluded. Fifteen fixed leakage-anchor repeats matched in this runtime after changing future returns. These checks do not recover the original historical cache.

## Descriptive figures and source sensitivity

```bash
python paper/integration/audits/return_diagnostics.py /PRIVATE/archive/spx_candidate.csv \
  > /PRIVATE/returns.json
python paper/integration/audits/descriptive_supplement.py \
  /PRIVATE/archive/spx_candidate.csv "$vrp_target_dir/six_forward_targets.csv"
python paper/integration/audits/alternate_range.py \
  /PRIVATE/archive/spx_candidate.csv /PRIVATE/FRED_SP500.csv > /PRIVATE/discrepancies.csv
```

The source sensitivity requires all seven FRED cells to match the original recorded signed adjustments exactly. The original full FRED response remains unavailable. All seven individual scenarios and the joint scenario are retained. Garman–Klass calculations were completed after seeing the core results under the already allowed, OHLC-compatible source sensitivity. No baseline or inferential sample was replaced. Parkinson depends on highs and lows, which these substitutions do not change.

## External-market reconstruction

```bash
python paper/integration/audits/extensions/fetch_pinned_sources.py \
  --checkout "$PWD" --output /PRIVATE/cross-market-sources
python paper/integration/audits/extensions/rebuild_paired_h1_h2.py \
  --checkout "$PWD" --source-dir /PRIVATE/cross-market-sources \
  --spx-targets "$vrp_target_dir/six_forward_targets.csv" \
  --output /PRIVATE/paired-market.json
```

This recovers the original Nasdaq/FRED and VXN/FRED byte prefixes by their pinned hashes and recomputes the individual and paired H1/H2 statistics. The extra H1 block-bootstrap results are a partial registered replay. The full paired H1–H5 bootstrap/Holm family is incomplete. The H2 slope comparison uses a stacked interaction regression with date-grouped scores. H7's primary lag is 63; quoted lag-21 values are sensitivity estimates. The separate exploratory supplement identifies which findings were re-executed and which remain traced only to reports.

## Theory and typesetting

```bash
python paper/integration/audits/theory/check_theory.py
python paper/integration/render.py
python -c 'import sys; sys.path.insert(0,"paper/integration"); from render import render; render("supplement")'
```

Typesetting used Pandoc 3.1.3 and Typst 0.15.0. PDFs include vector figures. The renderer removes decorative LaTeX equation boxes and normalizes whitespace inside display math before Pandoc conversion; it preserves their mathematical content. A compatibility definition maps Pandoc's partial-derivative symbol. The final manuscript and supplement were visually inspected after rendering, including the theoretical equations and multi-column tables. Figure/table sources and exact package hashes are in the inventory. Rendered PDF byte identity across platforms is not asserted.

## Required human decisions and technical gaps

`COAUTHOR_REVIEW.md` identifies each unresolved acceptance item. Scientific decisions include accepting the interim CLOSE pathway, archive insertion and exclusions, the treatment of source discrepancies and protocol amendments, and the conclusions. Technical gaps include the missing original SPX manifest/FRED response, historical derived-byte/cache replay and the incomplete cross-market inferential family. A later revision must preserve this version and record any source or specification change before recomputation.
