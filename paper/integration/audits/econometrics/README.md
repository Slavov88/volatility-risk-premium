# Econometrics audit (provisional)

These scripts run against the corrected checkout and the recovered source-data
reconstruction. They never substitute historical GARCH caches for fresh fits.
Provider data and newly fitted per-origin records are intentionally outside
this portable delivery. See the provenance receipt for source restrictions.

Use the project dependency lock in a compatible Python environment. This run
used Python 3.12.12 and `arch==8.0.0`, `numpy==2.4.6`, `scipy==1.17.1`,
`pandas==2.3.3`, `statsmodels==0.15.0`. Historic execution used Python 3.11.5.

```
python independent_core.py CHECKOUT TARGETS_CSV DAILY_CSV observation_core_receipt.json
PYTHONPATH=CHECKOUT/src python fresh_refits.py CHECKOUT TARGETS_CSV DAILY_CSV NEW_DIRECTORY normal_expanding
PYTHONPATH=CHECKOUT/src python fresh_refits.py CHECKOUT TARGETS_CSV DAILY_CSV NEW_DIRECTORY t_expanding
PYTHONPATH=CHECKOUT/src python fresh_refits.py CHECKOUT TARGETS_CSV DAILY_CSV NEW_DIRECTORY normal_rolling5y
python compare_fresh.py CHECKOUT NEW_DIRECTORY fresh_comparison_receipt.json
python independent_forecast_inference.py TARGETS_CSV NEW_DIRECTORY independent_forecast_receipt.json
PYTHONPATH=CHECKOUT/src python check_leakage.py DAILY_CSV leakage_receipt.json
python audit_core_results.py CHECKOUT
```

`independent_core.py` uses independent NumPy OLS and score-sandwich HAC; it
reconstructs all six targets independently from the entire canonical SPX daily
history. NBER month labels use the locked peak/trough chronology. Its original
HTML snapshot has not been recovered, so original source-byte replay is not
claimed for that external chronology.

`fresh_refits.py` calls the corrected producer's specified cold-start fitting
routine for every origin; this is a fresh execution, not an independent GARCH
implementation. It records failures and uses a common finite evaluation mask.
The current run started with an empty NEW_DIRECTORY. Resumption reuses only its
own new checkpoints, protected by configuration identity, never historical fits.
It evaluates all 72 corrected cells using the producer's checked HAC routines.

`compare_fresh.py` compares the new fits' aggregate output with the committed
corrected aggregate manifest. It compares common-origin hashes and counts (the committed manifest does not contain origin lists) and records every
numeric difference and every 5% inference classification change. It does not
claim byte-exact reproduction or silently declare a numerical tolerance passed.
`leakage_receipt.json` establishes exact same-runtime repeat at fifteen fixed
anchors, including pre-closure dates, after all future returns are perturbed;
it is not a claim of a full historical-cache replay.

`audit_core_results.py` remains the earlier aggregate-only audit. Its receipt
is not evidence of observation-level estimation or raw-data provenance.

The 72-cell comparison and independent primary H3/H4 inference are recorded in
`fresh_comparison_receipt.json` and `independent_forecast_receipt.json`. No numerical
tolerance was fixed before these results, so none is claimed to have passed.

`garch_diagnostics.py` summarizes all fresh checkpoints and repeats the fixed
first/final annual residual-diagnostic fits. Run with
`PYTHONPATH=CHECKOUT/src python garch_diagnostics.py DAILY_CSV NEW_DIRECTORY garch_diagnostics_receipt.json`.
The JSON receipt includes per-anchor diagnostics and input hashes; the companion
`garch_parameter_summary.csv` and `garch_anchor_diagnostics.csv` provide tables.
These report fresh computations, not historical checkpoint recovery. Parameters
are fitted using percentage returns; omega is in percentage-squared units.
