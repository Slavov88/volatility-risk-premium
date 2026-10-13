"""Rejection diagnosis must not become an alternative data promotion path."""
import json

import pandas as pd
import pytest

from test_processed_panel import sources
from vrp.acquisition_audit import audit_acquisitions, ohlc_defects, sanitized_spx_manifest
from vrp.processed_panel import PanelProvenanceError


def test_price_redaction_preserves_differences_and_original():
    original = {"fred_close_validation": {"validation": {"discrepancy_sample": [
        {"date": "2024-01-02", "yahoo_close": 100.0, "fred_close": 101.0, "absolute_difference": 1.0}
    ]}}}
    safe = sanitized_spx_manifest(original)
    assert safe["fred_close_validation"]["validation"]["discrepancy_sample"] == [
        {"date": "2024-01-02", "absolute_difference": 1.0}]
    assert original["fred_close_validation"]["validation"]["discrepancy_sample"][0]["yahoo_close"] == 100.0


def test_overlapping_ohlc_defects_count_rows_once_and_omit_prices():
    frame = pd.DataFrame({"Date": ["2024-01-02", "2024-01-03"],
        "OPEN": [10., 10.], "HIGH": [9., 12.], "LOW": [11., 8.], "CLOSE": [10., 11.]})
    result = ohlc_defects(frame, ("OPEN", "HIGH", "LOW", "CLOSE"))
    assert result["row_count"] == 1
    assert all(days == ["2024-01-02"] for days in result["categories"].values())
    assert "10.0" not in json.dumps(result)


def test_accepted_audit_is_reproducible_without_scientific_approval(sources, monkeypatch):
    import vrp.acquisition_audit as audit
    import vrp.processed_panel as builder
    monkeypatch.setattr(audit, "CONVENTIONS", builder.CONVENTIONS)
    root, output, spx, vix = sources
    result = audit_acquisitions(root, spx, vix)
    assert result == audit_acquisitions(root, spx, vix)
    assert result["status"] == "QUALITY_PASSED_PENDING_COAUTHOR_REVIEW"
    assert result["scientific_approval"] == "NOT_REVIEWED"
    assert result["alignment_diagnostic_only"]["panel_constructed"] is False
    assert not output.exists()


def test_rejected_vix_can_be_diagnosed_but_never_promoted(sources, monkeypatch):
    import vrp.acquisition_audit as audit
    import vrp.processed_panel as builder
    from vrp.vix_data import acquire_vix_history
    from datetime import date, datetime, timezone
    monkeypatch.setattr(audit, "CONVENTIONS", builder.CONVENTIONS)
    monkeypatch.setattr("vrp.vix_data.fetch_bytes", lambda _: b"DATE,OPEN,HIGH,LOW,CLOSE\n01/02/2024,13,14,12,13.2\n")
    root, output, spx, _ = sources
    result = acquire_vix_history(root, start_date=date(2024,1,2), end_exclusive=date(2024,1,4),
        retrieved_at=datetime(2024,1,6,12,tzinfo=timezone.utc))
    report = audit_acquisitions(root, spx, root / result.manifest_relative_path)
    assert report["status"] == "BLOCKED_VIX_QUALITY"
    assert report["vix_quality"]["missing_sessions"] == ["2024-01-03"]
    assert report["alignment_diagnostic_only"]["common_dates"] == 1
    assert not output.exists()


@pytest.mark.parametrize("target", ["spx", "vix", "vix_raw"])
def test_audit_rejects_hash_tampering(sources, monkeypatch, target):
    import vrp.acquisition_audit as audit
    import vrp.processed_panel as builder
    monkeypatch.setattr(audit, "CONVENTIONS", builder.CONVENTIONS)
    root, _, spx, vix = sources
    record = json.loads((spx if target == "spx" else vix).read_text())
    info = record["yahoo" if target == "spx" else "raw" if target == "vix_raw" else "normalized"]
    (root / info["relative_path"]).write_bytes(b"corrupted")
    with pytest.raises(PanelProvenanceError, match="SHA-256 mismatch"):
        audit_acquisitions(root, spx, vix)


def test_audit_rejects_forged_quality_report(sources, monkeypatch):
    import vrp.acquisition_audit as audit
    import vrp.processed_panel as builder
    monkeypatch.setattr(audit, "CONVENTIONS", builder.CONVENTIONS)
    root, _, spx, vix = sources
    record = json.loads(vix.read_text())
    record["quality"]["ohlc_order_violations"] = 100
    vix.write_text(json.dumps(record))
    with pytest.raises(PanelProvenanceError, match="recorded quality"):
        audit_acquisitions(root, spx, vix)


def test_cli_retains_nonzero_quality_status_and_identical_output(sources, monkeypatch, tmp_path):
    import vrp.acquisition_audit as audit
    import vrp.processed_panel as builder
    monkeypatch.setattr(audit, "CONVENTIONS", builder.CONVENTIONS)
    root, _, spx, vix = sources
    output = tmp_path / "audit.json"
    args = ["--raw-root", str(root), "--spx-manifest", str(spx),
        "--vix-manifest", str(vix), "--report", str(output)]
    assert audit.main(args) == 0
    original = output.read_bytes()
    assert audit.main(args) == 0
    assert output.read_bytes() == original
    assert json.loads(original)["scientific_approval"] == "NOT_REVIEWED"


def test_fred_replay_uses_rounded_difference_metadata(sources, monkeypatch):
    from vrp.spx_data import acquire_spx_index
    from test_processed_panel import _spx_frame
    from datetime import date, datetime, timezone
    import vrp.acquisition_audit as audit
    import vrp.processed_panel as builder
    monkeypatch.setattr(audit, "CONVENTIONS", builder.CONVENTIONS)
    root, _, _, vix = sources
    frame = _spx_frame()
    frame.loc[frame.index[1], "Close"] = 101.250000000123
    result = acquire_spx_index(root, date(2024,1,2), date(2024,1,4),
        retrieved_at=datetime(2024,1,7,12,tzinfo=timezone.utc),
        yahoo_download=lambda **_: frame, yfinance_version="fixture",
        fred_fetch=lambda _: b"observation_date,SP500\n2024-01-02,100\n2024-01-03,102.25\n")
    report = audit_acquisitions(root, root / result.manifest_relative_path, vix)
    assert report["fred_validation"]["validation"]["discrepancy_count"] == 1
    assert report["fred_validation"]["validation"]["discrepancy_sample"] == [
        {"date": "2024-01-03", "absolute_difference": 1.0}]
