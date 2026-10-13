import json
from datetime import date
from pathlib import Path

import pytest

from vrp.data import (
    source_specs,
    summarize_cboe_vix,
    summarize_nasdaq_spy,
    summarize_treasury_yield_curve,
    write_immutable,
)


def test_source_specs_label_spy_as_provisional_proxy() -> None:
    specs = source_specs(date(2026, 5, 1), date(2026, 8, 10))
    assert {spec.name for spec in specs} == {
        "cboe_vix",
        "treasury_yield_curve_2026",
        "nasdaq_spy_ohlc",
    }
    spy = next(spec for spec in specs if spec.name == "nasdaq_spy_ohlc")
    assert "proxy" in spy.status
    assert "fromdate=2026-05-01" in spy.url
    assert "todate=2026-08-10" in spy.url


def test_invalid_source_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="start_date"):
        source_specs(date(2026, 8, 10), date(2026, 5, 1))


def test_cboe_summary_validates_schema_and_missingness() -> None:
    raw = b"DATE,OPEN,HIGH,LOW,CLOSE\n01/02/1990,17.24,17.24,17.24,17.24\n"
    rows, start, end, columns, missing = summarize_cboe_vix(raw)
    assert rows == 1
    assert start == end == "1990-01-02"
    assert columns == ["DATE", "OPEN", "HIGH", "LOW", "CLOSE"]
    assert sum(missing.values()) == 0


def test_treasury_summary_reads_three_month_yield_and_missingness() -> None:
    raw = b"""<?xml version='1.0' encoding='utf-8'?>
    <feed xmlns='http://www.w3.org/2005/Atom'
      xmlns:d='http://schemas.microsoft.com/ado/2007/08/dataservices'
      xmlns:m='http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'>
      <entry><content><m:properties>
        <d:NEW_DATE>2026-08-06T00:00:00</d:NEW_DATE>
        <d:BC_3MONTH>3.90</d:BC_3MONTH>
      </m:properties></content></entry>
      <entry><content><m:properties>
        <d:NEW_DATE>2026-08-07T00:00:00</d:NEW_DATE>
        <d:BC_3MONTH></d:BC_3MONTH>
      </m:properties></content></entry>
    </feed>"""
    rows, start, end, columns, missing = summarize_treasury_yield_curve(raw)
    assert (rows, start, end) == (2, "2026-08-06", "2026-08-07")
    assert {"NEW_DATE", "BC_3MONTH"}.issubset(columns)
    assert missing["BC_3MONTH"] == 1


def test_nasdaq_summary_normalizes_coverage_dates() -> None:
    payload = {
        "data": {
            "tradesTable": {
                "rows": [
                    {
                        "date": "08/07/2026",
                        "open": "1",
                        "high": "2",
                        "low": "0.5",
                        "close": "1.5",
                        "volume": "100",
                    },
                    {
                        "date": "08/06/2026",
                        "open": "1",
                        "high": "2",
                        "low": "0.5",
                        "close": "1.5",
                        "volume": "100",
                    },
                ]
            }
        },
        "status": {"rCode": 200},
    }
    summary = summarize_nasdaq_spy(json.dumps(payload).encode("utf-8"))
    assert summary[:3] == (2, "2026-08-06", "2026-08-07")
    assert sum(summary[4].values()) == 0


def test_immutable_writer_is_idempotent_and_rejects_changes(tmp_path: Path) -> None:
    target = tmp_path / "source.csv"
    first_digest = write_immutable(target, b"a,b\n1,2\n")
    second_digest = write_immutable(target, b"a,b\n1,2\n")
    assert first_digest == second_digest
    with pytest.raises(FileExistsError, match="immutable snapshot differs"):
        write_immutable(target, b"a,b\n3,4\n")
