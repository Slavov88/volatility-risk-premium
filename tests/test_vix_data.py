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


def test_vix_current_day_guard_uses_new_york_date(tmp_path) -> None:
    from datetime import datetime, timezone

    from vrp.vix_data import acquire_vix_history

    # 02:00 UTC on Jan 6 is still Jan 5 in New York.
    retrieved = datetime(2024, 1, 6, 2, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="current-day VIX"):
        acquire_vix_history(
            tmp_path,
            start_date=date(2024, 1, 2),
            end_exclusive=date(2024, 1, 6),
            retrieved_at=retrieved,
        )


def test_vix_cli_rejects_iso_week_date_and_trailing_text() -> None:
    from vrp.vix_data import build_parser

    parser = build_parser()
    for invalid in ("2024-W01-1", "2024-01-02junk", "2024-1-2"):
        with pytest.raises(SystemExit):
            parser.parse_args([
                "--start-date", invalid,
                "--end-exclusive", "2024-01-04",
            ])


def test_acquisition_end_to_end_preserves_hashes_manifest_and_methodology(
    tmp_path, monkeypatch
) -> None:
    import hashlib
    import json
    from datetime import datetime, timezone

    import vrp.vix_data as module

    response = raw_vix([
        "01/02/2024,13,14,12,13.2",
        "01/03/2024,13.2,14.2,12.8,13.5",
    ])
    requested = []
    def fake_fetch(url: str) -> bytes:
        requested.append(url)
        return response

    monkeypatch.setattr(module, "fetch_bytes", fake_fetch)
    result = module.acquire_vix_history(
        tmp_path,
        start_date=date(2024, 1, 2),
        end_exclusive=date(2024, 1, 4),
        retrieved_at=datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
    )
    assert requested == [module.CBOE_VIX_URL]
    assert result.quality.accepted
    manifest = json.loads((tmp_path / result.manifest_relative_path).read_text())
    raw_path = tmp_path / result.raw_relative_path
    normalized_path = tmp_path / result.normalized_relative_path
    assert raw_path.read_bytes() == response
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == result.raw_sha256
    assert hashlib.sha256(normalized_path.read_bytes()).hexdigest() == result.normalized_sha256
    assert manifest["raw"]["sha256"] == result.raw_sha256
    assert manifest["normalized"]["sha256"] == result.normalized_sha256
    assert manifest["quality"]["accepted"] is True
    assert manifest["quality"]["expected_session_count"] == 2
    assert manifest["methodology"]["weekly_inclusive_start"] == "2014-10-06"
    assert manifest["frozen_window"] == {
        "start_inclusive": "2024-01-02",
        "end_exclusive": "2024-01-04",
    }
    assert list(pd.read_csv(normalized_path)["CLOSE"]) == [13.2, 13.5]


def test_vix_cli_accepts_quality_and_rejects_invalid_quality_preserving_artifacts(
    tmp_path, monkeypatch, capsys
) -> None:
    import vrp.vix_data as module

    valid = raw_vix([
        "01/02/2024,13,14,12,13.2",
        "01/03/2024,13.2,14.2,12.8,13.5",
    ])
    monkeypatch.setattr(module, "fetch_bytes", lambda _: valid)
    ok = module.main([
        "--start-date", "2024-01-02",
        "--end-exclusive", "2024-01-04",
        "--raw-root", str(tmp_path / "accepted"),
    ])
    assert ok == 0
    assert "quality=accepted" in capsys.readouterr().out

    incomplete = raw_vix(["01/02/2024,13,14,12,13.2"])
    monkeypatch.setattr(module, "fetch_bytes", lambda _: incomplete)
    bad = module.main([
        "--start-date", "2024-01-02",
        "--end-exclusive", "2024-01-04",
        "--raw-root", str(tmp_path / "rejected"),
    ])
    assert bad == 2
    assert "quality=rejected" in capsys.readouterr().out
    import json
    manifest_paths = list((tmp_path / "rejected").rglob("vix_manifest.json"))
    assert len(manifest_paths) == 1
    manifest = json.loads(manifest_paths[0].read_text())
    assert manifest["quality"]["accepted"] is False
    assert manifest["quality"]["missing_sessions"] == ["2024-01-03"]
    assert (manifest_paths[0].parent / manifest["raw"]["relative_path"]).exists()


def test_vix_immutable_snapshot_refuses_modified_existing_file(
    tmp_path, monkeypatch
) -> None:
    from datetime import datetime, timezone
    import vrp.vix_data as module

    monkeypatch.setattr(module, "fetch_bytes", lambda _: raw_vix([
        "01/02/2024,13,14,12,13.2",
        "01/03/2024,13.2,14.2,12.8,13.5",
    ]))
    kwargs = {
        "start_date": date(2024, 1, 2),
        "end_exclusive": date(2024, 1, 4),
        "retrieved_at": datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
    }
    first = module.acquire_vix_history(tmp_path, **kwargs)
    raw_file = tmp_path / first.raw_relative_path
    raw_file.write_bytes(b"altered acquisition bytes")
    with pytest.raises(FileExistsError, match="immutable snapshot differs"):
        module.acquire_vix_history(tmp_path, **kwargs)
