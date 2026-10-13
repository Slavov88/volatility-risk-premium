"""The archive's textual n/a sentinel cannot be counted as a usable close."""
from datetime import datetime
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("sentinel", ["n/a", "", float("nan"), float("inf")])
def test_archive_missing_close_is_not_numeric_availability(tmp_path, monkeypatch, sentinel):
    rows = [["disclaimer"], ["Date", "VIX Open", "VIX High", "VIX Low", "VIX Close"],
        [1, "n/a", "n/a", "n/a", sentinel], [2, "n/a", "n/a", "n/a", 12.0]]
    sheet = SimpleNamespace(nrows=len(rows), row_values=lambda i: rows[i], cell_value=lambda i, j: rows[i][j])
    book = SimpleNamespace(datemode=0, sheet_by_index=lambda _: sheet)
    fake_xlrd = SimpleNamespace(__version__="2.0.2", open_workbook=lambda _: book,
        xldate_as_datetime=lambda n, mode: datetime(1991,3,1) if n == 1 else datetime(1999,12,31))
    monkeypatch.setitem(sys.modules, "xlrd", fake_xlrd)
    directory = tmp_path / "cboe"
    directory.mkdir()
    (directory / "vixarchive.xls").write_bytes(b"synthetic XLS test double")
    raw = b"DATE,OPEN,HIGH,LOW,CLOSE\n12/31/1999,12,13,11,12\n"
    for name in ("VIX_History.csv", "linked_VIX_History.csv"):
        (directory / name).write_bytes(raw)
    (directory / "spx_2019_correction.pdf").write_bytes(b"synthetic notice")
    report = tmp_path / "report.json"
    monkeypatch.setattr(sys, "argv", ["inspect", "--acquisition-directory", str(tmp_path),
        "--parser-path", str(tmp_path / "parser"), "--report", str(report)])
    script = Path(__file__).parents[1] / "scripts/inspect_cboe_archive.py"
    original_path = sys.path.copy()
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.path[:] = original_path
    result = json.loads(report.read_text())
    assert result["missing_current_csv_dates"]["1991-03-01"] == {
        "present_in_archive": True, "archive_close_finite": False}
    assert result["missing_current_csv_dates"]["1999-12-31"]["archive_close_finite"] is True
    assert result["overlap_close_discrepancy_count"] == 0
    assert result["production_promotion"].startswith("NOT_APPROVED")
