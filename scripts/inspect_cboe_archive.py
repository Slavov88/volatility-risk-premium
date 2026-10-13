"""Inspect an auxiliary Cboe XLS archive without changing production inputs.

xlrd is an isolated inspection dependency, not an empirical dependency.
Install xlrd==2.0.2 into outputs/archive_inspection and pass --parser-path.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from vrp.data import write_immutable
from vrp.vix_data import parse_cboe_vix
from vrp.dates import as_date

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--acquisition-directory", type=Path, required=True)
parser.add_argument("--parser-path", type=Path, required=True)
parser.add_argument("--report", type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.parser_path.resolve()))
import xlrd
if xlrd.__version__ != "2.0.2":
    raise RuntimeError("Archive inspection requires xlrd==2.0.2")

directory = args.acquisition_directory / "cboe"
archive = directory / "vixarchive.xls"
book = xlrd.open_workbook(archive)
sheet = book.sheet_by_index(0)
if sheet.row_values(1) != ["Date", "VIX Open", "VIX High", "VIX Low", "VIX Close"]:
    raise ValueError("Unexpected archive schema")
rows = {}
for i in range(2, sheet.nrows):
    day = xlrd.xldate_as_datetime(sheet.cell_value(i, 0), book.datemode).date().isoformat()
    if day in rows:
        raise ValueError("Duplicate archive date")
    rows[day] = sheet.row_values(i)[1:]

def finite_close(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False

frame = parse_cboe_vix((directory / "VIX_History.csv").read_bytes(),
    start_date=as_date("1990-01-02"), end_exclusive=as_date("2026-01-01"))
current = dict(zip(frame.Date, frame.CLOSE))
overlap = sorted(set(rows) & set(current))
differences = [d for d in overlap if not finite_close(rows[d][-1]) or abs(float(rows[d][-1]) - current[d]) > 1e-12]
missing = ["1991-03-01", "1997-01-31", "1997-11-26", "1999-12-31"]
linked = (directory / "linked_VIX_History.csv").read_bytes()
report = {
    "purpose": "Official alternate Cboe archive inspection only; no stitching or data correction",
    "archive_source_url": "https://cdn.cboe.com/resources/us/indices/vixarchive.xls",
    "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "parser": "xlrd==2.0.2; isolated outputs/archive_inspection; locked empirical environment unchanged",
    "rows": len(rows), "coverage_start": min(rows), "coverage_end": max(rows),
    "missing_current_csv_dates": {d: {"present_in_archive": d in rows,
        "archive_close_finite": finite_close(rows[d][-1]) if d in rows else None} for d in missing},
    "overlap_count": len(overlap), "overlap_close_discrepancy_count": len(differences),
    "overlap_close_discrepancy_dates": differences,
    "archive_rows_missing_open_high_low": sum(any(v == "n/a" for v in vals[:3]) for vals in rows.values()),
    "production_promotion": "NOT_APPROVED; original VIX rejection remains authoritative",
    "linked_csv_sha256": hashlib.sha256(linked).hexdigest(),
    "linked_csv_byte_identical_to_canonical": linked == (directory / "VIX_History.csv").read_bytes(),
    "correction_notice_source_url": "https://cdn.cboe.com/resources/release_notes/2019/Corrected-Closing-Settlement-Prices-for-Certain-SP-Indices-II.pdf",
    "correction_notice_sha256": hashlib.sha256((directory / "spx_2019_correction.pdf").read_bytes()).hexdigest(),
}
digest = write_immutable(args.report, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
print(f"inspection={args.report} sha256={digest}")
