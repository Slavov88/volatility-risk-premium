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


def test_acquisition_uses_exact_symbol_unadjusted_ohlc_and_manifest(tmp_path: Path) -> None:
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
        yfinance_version="1.5.2-test",
        fred_fetch=lambda _url: sample_fred_raw(),
    )

    assert calls[0]["tickers"] == "^GSPC"
    assert calls[0]["auto_adjust"] is False
    assert calls[0]["end"] == "2024-01-04"
    assert calls[0]["repair"] is False
    assert calls[0]["multi_level_index"] is False
    assert result.row_count == 2
    assert result.coverage_start == "2024-01-02"
    assert result.coverage_end == "2024-01-03"
    assert result.fred_validation.discrepancy_count == 0

    yahoo_path = tmp_path / result.yahoo_relative_path
    manifest = json.loads((tmp_path / result.manifest_relative_path).read_text())
    assert manifest["schema_version"] == 2
    assert manifest["yahoo"]["symbol"] == "^GSPC"
    assert manifest["yahoo"]["artifact_type"] == (
        "immutable normalized acquisition snapshot"
    )
    assert manifest["yahoo"]["provider_response_persisted"] is False
    assert manifest["yahoo"]["persisted_columns"] == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ]
    assert "raw_columns" not in manifest["yahoo"]
    assert "normalized acquisition snapshot" in manifest["yahoo"][
        "adjustment_policy"
    ]
    assert manifest["yahoo"]["request_parameters"]["auto_adjust"] is False
    assert manifest["yahoo"]["yfinance_version"] == "1.5.2-test"
    assert manifest["transport_note"] == "default verified TLS transports"
    assert manifest["fred_validation"]["artifact_type"] == "provider response bytes"
    assert hashlib.sha256(yahoo_path.read_bytes()).hexdigest() == result.yahoo_sha256


def test_fred_discrepancy_is_reported_without_changing_yahoo(tmp_path: Path) -> None:
    result = acquire_spx_index(
        raw_root=tmp_path,
        start_date=date(2024, 1, 1),
        end_exclusive=date(2024, 1, 4),
        retrieved_at=datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
        yahoo_download=lambda **_kwargs: sample_yahoo_frame(),
        yfinance_version="mock",
        fred_fetch=lambda _url: sample_fred_raw("101.50"),
    )

    validation = result.fred_validation
    assert validation.discrepancy_count == 1
    assert validation.discrepancy_sample[0]["date"] == "2024-01-03"
    stored = pd.read_csv(tmp_path / result.yahoo_relative_path)
    assert stored.loc[stored["Date"] == "2024-01-03", "Close"].item() == 101.25


def test_current_new_york_date_bar_is_rejected() -> None:
    frame = sample_yahoo_frame().iloc[[0]].copy()
    frame.index = pd.to_datetime(["2024-01-05"])
    with pytest.raises(PartialCurrentDayError, match="current-day"):
        normalize_yahoo_spx(
            frame,
            start_date=date(2024, 1, 1),
            end_exclusive=date(2024, 1, 5),
            retrieved_at=datetime(2024, 1, 5, 18, tzinfo=timezone.utc),
        )


def test_same_dated_snapshot_cannot_be_changed(tmp_path: Path) -> None:
    kwargs = {
        "raw_root": tmp_path,
        "start_date": date(2024, 1, 1),
        "end_exclusive": date(2024, 1, 4),
        "retrieved_at": datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
        "yfinance_version": "mock",
        "fred_fetch": lambda _url: sample_fred_raw(),
    }
    acquire_spx_index(
        **kwargs,
        yahoo_download=lambda **_download_kwargs: sample_yahoo_frame(),
    )
    changed = sample_yahoo_frame()
    changed.loc[pd.Timestamp("2024-01-03"), "Close"] = 999.0
    with pytest.raises(FileExistsError, match="immutable snapshot differs"):
        acquire_spx_index(
            **kwargs,
            yahoo_download=lambda **_download_kwargs: changed,
        )


def test_validation_requires_close_overlap(tmp_path: Path) -> None:
    with pytest.raises(DataValidationError, match="no usable close overlap"):
        acquire_spx_index(
            raw_root=tmp_path,
            start_date=date(2024, 1, 1),
            end_exclusive=date(2024, 1, 4),
            retrieved_at=datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
            yahoo_download=lambda **_kwargs: sample_yahoo_frame(),
            yfinance_version="mock",
            fred_fetch=lambda _url: (
                b"observation_date,SP500\n2023-12-29,99.00\n"
            ),
        )
