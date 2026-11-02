# Private reconstruction instructions

**Provisional; independent freeze acceptance is pending.** This is an audit reconstruction, not promotion of a production freeze. Keep all inputs and build directories private; they contain market data. The delivery consists of this README, the script, metadata receipts, environment observations, and provenance report. It does not include the raw inputs or reconstructed rows.

## Inputs and environment

From the workspace root, this recipe uses the existing `prov` checkout at commit `b03686ece031038b9daba03a9a4b1990d4e95674`, `prov-env/bin/python`, and isolated `prov-parser` (xlrd 2.0.2). The latter takes precedence over the xlrd 2.0.1 listed in `environment-observed.txt`. The observed runtime and package versions are in `runtime_receipt.json`; `environment-observed.txt` is an inventory, not a portable requirements file (it contains a local file URL). The checkout and environment are prerequisites and are not included in this delivery. The script uses the checkout's tracked freeze and target manifests and implementation. Its three positional paths are checkout, input archive, and output directory. Use a fresh private output directory; existing files at expected paths are overwritten.

The private archive needs these exact files:

| File | Expected SHA-256 | Recovery role |
|---|---|---|
| `spx_candidate.csv` | `dd7838e8470a5056e99b82dba808bf9df226ced891e0826e4425d55a8d0f544e` | Exact normalized historical Yahoo OHLC input |
| `yahoo-chart2.json` | `4bfec0d5d6b91b6421ae27e5121a935d03e49747388b3ce4dcd24f7467ef24e7` | Later chart response whose normalization exactly equals the SPX input |
| `vix_current.csv` | `a5409500cdb8fdd86ba926dcfc7de5b1a54d365d4b7850a1a50c803ae57fddd1` | The first 473,635 bytes hash to the historical source CSV |
| `vixarchive.xls` | `9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566` | Official archival cell used for the authorized insertion |

The existing downloads in `prov-archive/` satisfy this recipe. The Cboe endpoints are <https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv> and <https://cdn.cboe.com/resources/us/indices/vixarchive.xls>. Live downloads may change: verify their bytes against the hashes, and for the CSV verify the historical prefix rather than assuming a later response is identical. The exact recovery URL/parameters and headers for the retained Yahoo chart response are unavailable; use the retained response and normalized file. A newly downloaded response cannot be presumed equivalent. Original historical Yahoo HTTP bytes were not retained.

## Rebuild and verify

Run from the workspace root, with normal Python (do not use optimization flags):

```sh
PYTHONPATH=prov/src:prov-parser prov-env/bin/python prov-delivery/rebuild_recovered.py prov prov-archive prov-rebuilt-new > prov-rebuilt-new.log
```

The script verifies the SPX normalized source hash and chart normalization, historical VIX prefix and normalized hash, official XLS evidence, and all three historical freeze CSV hashes. It writes private rows, an independent numeric target audit, and a `receipt.json`. Compare the output hashes with `reconstruction_receipt.json` and `double_build_receipt.json`. The latter records two existing builds in the observed runtime. To check those retained builds without rerunning:

```sh
python - <<'PY'
import hashlib, json
from pathlib import Path
receipt = json.loads(Path('prov-delivery/double_build_receipt.json').read_text())
for name, record in receipt['files'].items():
    hashes = [hashlib.sha256((Path(root) / name).read_bytes()).hexdigest()
              for root in ('prov-rebuilt', 'prov-rebuilt-second')]
    if hashes != [record['sha256'], record['sha256']]:
        raise SystemExit(f'mismatch: {name}')
    print('OK', name, record['sha256'])
PY
```

Those retained builds were generated before the delivered script's hash checks were changed from Python `assert` statements to explicit exceptions. That change preserves the reconstruction operations and makes verification effective even under optimized Python; the two-build evidence refers to the prior script. Syntax of the delivered script was checked separately.

## Limits

The original SPX acquisition manifest and FRED SP500 response are missing. The original VIX manifest and freeze/target manifests are recovered, but the complete `verify_interim` chain cannot pass without the missing SPX manifest; no substitute has been fabricated. The original FRED alternate-close comparison cannot be replayed exactly. Current-runtime daily and six-target files differ in byte hash from the original recorded outputs even though the all-origin, all-six independent numerical audit passes. The cause is not established. Exact freeze CSV recovery, tests, and deterministic current-runtime builds do not constitute exact historical derived-output reproduction or independent acceptance. See `provenance.md` for details.
