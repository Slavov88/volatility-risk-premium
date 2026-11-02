"""Recover hash-identified core input bytes into an explicitly private directory.

Usage: python recover_core_sources.py PRIVATE_OUTPUT [--archive EXISTING_ARCHIVE]
A later Yahoo chart response may recover the identical historical normalized CSV.
Cboe/FRED series histories may append rows. Only a prefix with the recorded
original SHA-256 is accepted; no historical value is patched or substituted.
"""

from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import pandas as pd
import requests

EXPECTED = {
    "spx_candidate.csv": "dd7838e8470a5056e99b82dba808bf9df226ced891e0826e4425d55a8d0f544e",
    "vix_prefix.csv": "965f14ae8d58079536b5491219b647e6385592be2c466e6ac849f6ace0bbe1f7",
    "vixarchive.xls": "9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verified_write(path, data, expected):
    if sha(data) != expected:
        raise ValueError("Historical digest mismatch for " + path.name)
    if path.exists() and path.read_bytes() != data:
        raise ValueError("Existing output differs: " + str(path))
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--archive", type=Path, help="Use already downloaded bytes instead of HTTP"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    start = int(datetime(1990, 1, 2, tzinfo=timezone.utc).timestamp())
    end = int(datetime(2026, 2, 3, tzinfo=timezone.utc).timestamp())
    urls = {
        "yahoo-chart2.json": f"https://query2.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1={start}&period2={end}&interval=1d",
        "vix_current.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
        "vixarchive.xls": "https://cdn.cboe.com/resources/us/indices/vixarchive.xls",
    }
    payload = {}
    for name, url in urls.items():
        if args.archive:
            data = (args.archive / name).read_bytes()
        else:
            response = requests.get(
                url, headers={"User-Agent": "Mozilla/5.0"}, timeout=90
            )
            response.raise_for_status()
            data = response.content
        payload[name] = data
    response = json.loads(payload["yahoo-chart2.json"])["chart"]["result"][0]
    if response["meta"]["symbol"] != "^GSPC":
        raise ValueError("Unexpected index symbol")
    quote = response["indicators"]["quote"][0]
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(response["timestamp"], unit="s", utc=True)
            .tz_convert("America/New_York")
            .strftime("%Y-%m-%d"),
            "Open": quote["open"],
            "High": quote["high"],
            "Low": quote["low"],
            "Close": quote["close"],
            "Adj Close": response["indicators"]["adjclose"][0]["adjclose"],
            "Volume": pd.Series(quote["volume"], dtype="int64"),
        }
    )
    normalized = frame.to_csv(
        index=False, lineterminator="\n", float_format="%.10g"
    ).encode()
    if len(frame) != 9088:
        raise ValueError("Historical SPX row count mismatch")
    verified_write(
        args.output / "spx_candidate.csv", normalized, EXPECTED["spx_candidate.csv"]
    )
    prefix = payload["vix_current.csv"][:473635]
    verified_write(
        args.output / "recovered_VIX_History.csv", prefix, EXPECTED["vix_prefix.csv"]
    )
    verified_write(
        args.output / "vixarchive.xls",
        payload["vixarchive.xls"],
        EXPECTED["vixarchive.xls"],
    )
    # The reconstruction reads the verified historical prefix from this name.
    verified_write(args.output / "vix_current.csv", prefix, EXPECTED["vix_prefix.csv"])
    (args.output / "yahoo-chart2.json").write_bytes(payload["yahoo-chart2.json"])
    receipt = {
        "scope": "RECOVERY_OF_HASH_IDENTIFIED_INPUTS_ONLY",
        "http_urls": urls,
        "download_sha256": {name: sha(data) for name, data in payload.items()},
        "historical_source_sha256": EXPECTED,
        "n_spx": len(frame),
        "archive_mode": args.archive is not None,
        "missing_original_artifacts": [
            "SPX acquisition manifest",
            "full FRED SP500 response",
        ],
        "scientific_acceptance": "PENDING",
    }
    (args.output / "recovery_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
