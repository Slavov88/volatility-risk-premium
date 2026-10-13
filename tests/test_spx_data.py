import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from vrp.spx_data import (
    DataValidationError,
    PartialCurrentDayError,
    acquire_spx_index,
    normalize_yahoo_spx,
    production_quality_report,
    require_production_quality,
)


def sample_yahoo_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "Open": [99.0, 100.0],
            "High": [101.0, 102.0],
            "Low": [98.0, 99.0],
            "Close": [100.0, 101.25],
            "Adj Close": [100.0, 101.25],
            "Volume": [1_000, 1_100],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    frame.index.name = "Date"
    return frame


def sample_fred_raw(second_close: str = "101.25") -> bytes:
    return (
        "observation_date,SP500\n"
        "2024-01-02,100.00\n"
        f"2024-01-03,{second_close}\n"
    ).encode("utf-8")


def test_acquisition_records_quality_and_keeps_fred_optional(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_download(**kwargs: object) -> pd.DataFrame:
        calls.append(kwargs)
        return sample_yahoo_frame()

    result = acquire_spx_index(
        raw_root=tmp_path,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
        retrieved_at=datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
        yahoo_download=fake_download,
        yfinance_version="test",
    )
    assert calls[0]["tickers"] == "^GSPC"
    assert calls[0]["auto_adjust"] is False
    assert result.production_quality.accepted
    assert result.fred_validation_status == "not_requested"

    manifest = json.loads(
        (tmp_path / result.manifest_relative_path).read_text()
    )
    assert manifest["schema_version"] == 4
    assert manifest["production_quality"]["accepted"] is True
    assert manifest["fred_close_validation"]["status"] == "not_requested"
    yahoo_path = tmp_path / result.yahoo_relative_path
    assert hashlib.sha256(yahoo_path.read_bytes()).hexdigest() == result.yahoo_sha256


def test_production_gate_rejects_missing_exchange_session() -> None:
    frame = normalize_yahoo_spx(
        sample_yahoo_frame().iloc[[0]],
        date(2024, 1, 1),
        date(2024, 1, 4),
        datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
    )
    report = production_quality_report(
        frame,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
    )
    assert not report.accepted
    assert report.missing_sessions == ("2024-01-03",)
    with pytest.raises(DataValidationError, match="quality gate"):
        require_production_quality(
            frame,
            start_date=date(2024, 1, 1),
            end_exclusive=date(2024, 1, 4),
        )


def test_production_gate_rejects_nan_nonpositive_and_bad_ohlc() -> None:
    normalized = normalize_yahoo_spx(
        sample_yahoo_frame(),
        date(2024, 1, 1),
        date(2024, 1, 4),
        datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
    )

    nan_frame = normalized.copy()
    nan_frame.loc[0, "Close"] = float("nan")
    assert not production_quality_report(
        nan_frame,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
    ).accepted

    zero_frame = normalized.copy()
    zero_frame.loc[0, "Open"] = 0.0
    assert not production_quality_report(
        zero_frame,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
    ).accepted

    bad_order = normalized.copy()
    bad_order.loc[0, "High"] = 97.0
    report = production_quality_report(
        bad_order,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
    )
    assert report.ohlc_order_violations == 1
    assert not report.accepted


def test_fred_validation_is_non_blocking_and_never_overwrites_yahoo(tmp_path: Path) -> None:
    result = acquire_spx_index(
        raw_root=tmp_path,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
        retrieved_at=datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
        yahoo_download=lambda **_: sample_yahoo_frame(),
        yfinance_version="test",
        fred_fetch=lambda _: sample_fred_raw("101.50"),
    )
    assert result.fred_validation_status == "available"
    assert result.fred_validation is not None
    assert result.fred_validation.discrepancy_count == 1
    stored = pd.read_csv(tmp_path / result.yahoo_relative_path)
    assert stored.loc[stored["Date"] == "2024-01-03", "Close"].item() == 101.25


def test_fred_transport_failure_does_not_block_yahoo_acquisition(tmp_path: Path) -> None:
    def fail(_: str) -> bytes:
        raise TimeoutError("validation endpoint unavailable")

    result = acquire_spx_index(
        raw_root=tmp_path,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
        retrieved_at=datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
        yahoo_download=lambda **_: sample_yahoo_frame(),
        yfinance_version="test",
        fred_fetch=fail,
    )
    assert result.fred_validation_status == "unavailable"
    assert (tmp_path / result.yahoo_relative_path).exists()


def test_current_new_york_date_bar_is_rejected() -> None:
    frame = sample_yahoo_frame().iloc[[0]].copy()
    frame.index = pd.to_datetime(["2024-01-05"])
    with pytest.raises(PartialCurrentDayError, match="current-day"):
        normalize_yahoo_spx(
            frame,
            date(2024, 1, 1),
            date(2024, 1, 6),
            datetime(2024, 1, 5, 18, tzinfo=timezone.utc),
        )
