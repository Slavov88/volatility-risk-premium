# Provenance and reconstruction audit — 2026-11-02

Status: provisional / not independently accepted. The locked protocol is 1.1.0; the interim data amendment is `2026-10-13-interim-vix-close/1.0.0`. This audit does not grant scientific acceptance or amend specifications. No raw market rows are intended for publication.

## Source bytes recovered

- Yahoo canonical normalized SPX: `dd7838e8470a5056e99b82dba808bf9df226ced891e0826e4425d55a8d0f544e`, 726,983 bytes, 9,088 OHLC rows from 1990-01-02 through 2026-02-02. All 21 post-2025 rows remain target support only. The recovered current Yahoo chart JSON (`4bfec0d5d6b91b6421ae27e5121a935d03e49747388b3ce4dcd24f7467ef24e7`) independently normalizes to exactly these canonical CSV bytes using the committed serializer (`%.10g`, LF, original OHLC/Adj Close/Volume column order). This verifies recovery of original normalized observations, not identity of the historical Yahoo HTTP response, which was never persisted in the original acquisition.
- Cboe current CSV download is `a5409500cdb8fdd86ba926dcfc7de5b1a54d365d4b7850a1a50c803ae57fddd1`. Its first 473,635 bytes exactly match original CSV `965f14ae8d58079536b5491219b647e6385592be2c466e6ac849f6ace0bbe1f7`. This is hash-verified recovery of the historical byte prefix, not an assumption based only on equivalent rows. Parsing the prefix with the committed parser reproduces normalized hash `10b2faa178208d7553f96597b40e63807668af77b3f8242f73afb8b8a40b0f94`.
- Official Cboe XLS: `9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566`. Isolated xlrd 2.0.2 verifies sheet OHLC, date cell A2528, Excel datemode 0/date serial 36525, numeric CLOSE E2528=24.64 and original absence from CSV. Only the authorized 1999-12-31 insertion is made.
- FRED VIX corroboration response `cf5fd219cd8cd428b287c6f260baaefd746e11ca8ef1eb19ffc9741204d58bcb` is recovered; FRED republishes Cboe and is not an independent index calculation.
- Original FRED SP500 validation response `4590145f9ed88e20b41bc1325fa7c538e7532e8b1289dac4b801b216c9bd77e6` is not recovered. Current response `60a8a21e1059640755b0fa247e12e79e28c4dfa4933801d5d0898bed96eada68` begins 2016-10-31 rather than original 2016-10-13 and cannot substitute silently. Therefore exact alternate-close report replay remains unavailable.

## Acquisition identity and transport evidence

Historical acquisition metadata records Yahoo via yfinance 1.5.2, `^GSPC`, daily, start=1990-01-02, end-exclusive=2026-02-03, auto_adjust=False, repair=False, keepna=True, actions=False, prepost=False, threads=False, multi_level_index=False, group_by=column. Historical timestamp is 2026-10-13T14:24:30.131093+00:00. The tracked sanitized manifest reports default library TLS and no verification override. Canonical source page: https://finance.yahoo.com/quote/%5EGSPC/history/ . Recovered chart JSON is from the Yahoo chart service; no retained request/response headers establish the precise query or retrieval timestamp of that later recovery. Its timestamp and transport are therefore not backdated to the historical acquisition.

Historical Cboe endpoint is https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv ; timestamp 2026-10-13T14:24:30.124133+00:00; tracked source manifest states urllib default TLS verification without override. Archive endpoint is https://cdn.cboe.com/resources/us/indices/vixarchive.xls . Recovery response headers, retrieval timestamps and TLS receipts were not retained in the inherited local artifacts, so this audit verifies bytes and historical metadata separately and does not invent recovery transport evidence.

The original VIX source manifest is recovered byte-for-byte as tracked `2026-10-13_vix_production_rejected.json`, hash `68c11d8fe5a9f454761a898b1bd6bdee499c7a55b30ce370ec28549fc8805d92`. Original SPX source manifest `29bb559550a8470b1b8c034cf752b8bd3919b2585069ed27d252ddc2bb6873a5` is unavailable; sanitized tracked metadata has a different hash. Thus the full `verify_interim` source-manifest chain cannot pass. No replacement manifest was fabricated.

## Freeze and derived outputs

The original freeze manifest is recovered exactly from tracked JSON: `1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4`; original target manifest `00532571aad5f8d9c43231933429fe6facbf7687a6332231ac8b7ad0ff73ccd9` also matches. These are metadata recovery, distinct from executing their full verification chain.

| Output | Fresh SHA-256 | Exact original hash? |
|---|---|---|
| canonical_spx_ohlc.csv | ad8baf5121a081d633d6283c936f6956f82974446dfd871fc905ab31ff34a74e | yes |
| interim_vix_close.csv | 457f46b6850ef6481fc272deb0e097b5da1134e1610c7d86c225448758eb6353 | yes |
| interim_origin_panel.csv | 5293bc8b5e3388090216fb27e50d5a989c67e817dde67cc40358c3522e3a32f5 | yes |
| canonical_daily.csv | f262250e873ecd46b5ef9372c607a2165dd1b1cb30b56d7365d8df7e70de62b2 | no: original 774147ffba6e298a49ef2ba1059503515e2dec1317500d4f37acf980cd7a51e2 |
| six_forward_targets.csv | 3c7fc89fc510659fca0a976ad0d61f780aa93505cc2764f53d38a3a14d671fbc | no: original cdd63f219d61584c8f3fa15e8f80c23ef351a6e902cb93027eed9b5e79dba3a5 |
| target_audit.json | 7b8d05616a1477e40c1eb86b65fe21a26e87e4b24429ef5ce056911eaed88bb5 | yes |

Reconstruction retains 9,064 valid predictor origins, excludes the 28 non-XNYS VIX rows and three unavailable predictors, and preserves all SPX returns before predictor masking. The all-origin/all-six independent NumPy target audit passes; maximum absolute formula discrepancy is 2.220446049250313e-16. Every horizon is complete. The reconstructed daily/targets and descriptions do not match original byte hashes. The target source-code hashes match the recorded implementation. Runtime differs: current Python 3.12.14 on Linux/glibc2.39 versus recorded Python 3.11.5. Python summation/math/platform effects are plausible, but the exact cause of the original/fresh byte differences is not established without original derived bytes or the historical runtime. Do not call this exact derived-output reproduction.

Observed scientific package versions are NumPy2.4.6, pandas2.3.3, scipy1.17.1, statsmodels0.15.0, arch8.0.0, exchange-calendars4.13.2, yfinance1.5.2. Full observed environment and lock identities are recorded separately. Current lock hash `6a509e331b4c7cc91753dd01ef07523bc2d9eb3b5d2f3455333e1a7a24cad347` differs from original target-report lock `52ebfe3b7cfed527551d7bc982b3989bd1fa530c9a60b1b9d9dbbf59559031c9`.

## Reproduction and tests

Run privately: `PYTHONPATH=prov/src:prov-parser prov-env/bin/python prov-delivery/rebuild_recovered.py prov prov-archive prov-rebuilt`. The script requires the specified checkout, local recovered raw inputs and xlrd 2.0.2; it writes private market data and publishes no data. See prov-delivery/README.md for prerequisites, exact commands, and verification limits. Do not put `prov-archive` or `prov-rebuilt` into Git. The reconstruction receipt records exact and nonmatching hashes explicitly. `prov` checkout is b03686ece031038b9daba03a9a4b1990d4e95674; the full corrected-branch test suite passed: **1816 tests, 24.52s**. Raw external-data replay and full manifest-chain acceptance are separate from unit tests.

The retained two-build receipt was checked against both output directories: all eight recorded hashes match. The delivered script subsequently replaced assert-based hash checks with explicit exceptions; this does not alter the reconstruction operations, and syntax was checked, but the retained builds predate that edit.

Fresh reconstructed files were shared with the econometric auditor for independent H1/H2/H5 calculations and fresh H3/H4 model fits. This provenance audit does not claim recovery of missing historical GARCH caches, or independently accepted coauthor signoff. No push was performed.
