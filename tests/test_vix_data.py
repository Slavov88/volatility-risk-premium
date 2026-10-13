from datetime import date

import pandas as pd
import pytest

from vrp.vix_data import (
    VixDataValidationError,
    parse_cboe_vix,
    vix_quality_report,
)


def raw_vix(rows: list[str]) -> bytes:
    return (
        "DATE,OPEN,HIGH,LOW,CLOSE\n" + "\n".join(rows) + "\n"
    ).encode("utf-8")


def test_parse_and_quality_accept_complete_window() -> None:
    frame = parse_cboe_vix(
        raw_vix([
            "01/02/2024,13,14,12,13.2",
            "01/03/2024,13.2,14.2,12.8,13.5",
        ]),
        start_date=date(2024, 1, 2),
        end_exclusive=date(2024, 1, 4),
    )
    report = vix_quality_report(
        frame,
        start_date=date(2024, 1, 2),
        end_exclusive=date(2024, 1, 4),
    )
    assert report.accepted
    assert list(frame["Date"]) == ["2024-01-02", "2024-01-03"]


def test_vix_quality_rejects_missing_session_and_bad_ohlc() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2024-01-02"],
            "OPEN": [13.0],
            "HIGH": [12.0],
            "LOW": [11.0],
            "CLOSE": [13.2],
        }
    )
    report = vix_quality_report(
        frame,
        start_date=date(2024, 1, 2),
        end_exclusive=date(2024, 1, 4),
    )
    assert not report.accepted
    assert report.missing_sessions == ("2024-01-03",)
    assert report.ohlc_order_violations == 1


def test_vix_parser_rejects_duplicate_dates() -> None:
    with pytest.raises(VixDataValidationError, match="duplicate"):
        parse_cboe_vix(
            raw_vix([
                "01/02/2024,13,14,12,13.2",
                "01/02/2024,13,14,12,13.2",
            ]),
            start_date=date(2024, 1, 2),
            end_exclusive=date(2024, 1, 3),
        )


def test_vix_acquisition_rejects_current_day_window(tmp_path) -> None:
    from datetime import datetime, timezone

    from vrp.vix_data import acquire_vix_history

    retrieved = datetime(2024, 1, 5, 12, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="current-day VIX"):
        acquire_vix_history(
            tmp_path,
            start_date=date(2024, 1, 2),
            end_exclusive=date(2024, 1, 6),
            retrieved_at=retrieved,
        )
