"""Synthetic acquisition fixtures for manifest-enforced production panel building."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import vrp.processed_panel as builder
import vrp.vix_data as vix_module
from vrp.processed_panel import PanelProvenanceError, build_verified_origin_panel
from vrp.spx_data import acquire_spx_index
from vrp.vix_data import acquire_vix_history


def _raw_vix(*, complete: bool = True) -> bytes:
    rows = [
        "DATE,OPEN,HIGH,LOW,CLOSE",
        "01/02/2024,13,14,12,13.2",
    ]
    if complete:
        rows.append("01/03/2024,13.2,14.2,12.8,13.5")
    return ("\n".join(rows) + "\n").encode("utf-8")


def _spx_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "Open": [99.0, 100.0],
            "High": [101.0, 102.0],
            "Low": [98.0, 99.0],
            "Close": [100.0, 101.25],
            "Adj Close": [100.0, 101.25],
            "Volume": [1000, 1100],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    frame.index.name = "Date"
    return frame


@pytest.fixture
def sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "raw"
    out = tmp_path / "processed"
    # A tiny test-only frozen window; the production ScientificConventions
    # object itself remains immutable and fully locked to 1990-2026.
    monkeypatch.setattr(
        builder, "CONVENTIONS",
        SimpleNamespace(
            sample_start="2024-01-02",
            sample_end="2024-01-03",
            spx_target_support_end_exclusive="2024-01-04",
            vix_weekly_methodology_start="2014-10-06",
            protocol_version="1.1.0",
        ),
    )
    timestamp = datetime(2024, 1, 5, 12, tzinfo=timezone.utc)
    spx = acquire_spx_index(
        root,
        date(2024, 1, 2),
        date(2024, 1, 4),
        retrieved_at=timestamp,
        yahoo_download=lambda **_: _spx_frame(),
        yfinance_version="fixture",
    )
    monkeypatch.setattr(vix_module, "fetch_bytes", lambda _: _raw_vix())
    vix = acquire_vix_history(
        root,
        start_date=date(2024, 1, 2),
        end_exclusive=date(2024, 1, 4),
        retrieved_at=timestamp,
    )
    return root, out, root / spx.manifest_relative_path, root / vix.manifest_relative_path


def test_verified_panel_builds_only_from_accepted_and_hashed_inputs(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    result = build_verified_origin_panel(root, spx_manifest, vix_manifest, output)
    assert result.origin_count == 2
    assert result.first_origin == "2024-01-02"
    assert result.last_origin == "2024-01-03"
    panel_bytes = (output / result.panel_relative_path).read_bytes()
    assert hashlib.sha256(panel_bytes).hexdigest() == result.panel_sha256
    panel = pd.read_csv(output / result.panel_relative_path)
    assert list(panel["spx_close"]) == [100.0, 101.25]
    assert list(panel["ivar"]) == pytest.approx([0.132**2, 0.135**2], rel=1e-12)
    assert not (set(panel.columns) & {"rvar", "vrp_x"})
    manifest = json.loads((output / result.manifest_relative_path).read_text())
    assert manifest["row_losses"]["common_origins"] == 2
    assert manifest["row_losses"]["missing_vix_on_spx"] == []
    assert manifest["row_losses"]["vix_without_spx"] == []
    assert manifest["spx_source_manifest_sha256"] == hashlib.sha256(spx_manifest.read_bytes()).hexdigest()
    assert manifest["vix_source_manifest_sha256"] == hashlib.sha256(vix_manifest.read_bytes()).hexdigest()
    assert manifest["panel"]["sha256"] == result.panel_sha256
    repeated = build_verified_origin_panel(root, spx_manifest, vix_manifest, output)
    assert repeated == result


def test_spx_tampered_artifact_is_rejected(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    record = json.loads(spx_manifest.read_text())
    (root / record["yahoo"]["relative_path"]).write_bytes(b"modified snapshot")
    with pytest.raises(PanelProvenanceError, match="SPX: SHA-256 mismatch"):
        build_verified_origin_panel(root, spx_manifest, vix_manifest, output)


def test_vix_tampered_raw_artifact_is_rejected(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    record = json.loads(vix_manifest.read_text())
    (root / record["raw"]["relative_path"]).write_bytes(b"modified raw VIX")
    with pytest.raises(PanelProvenanceError, match="VIX raw: SHA-256 mismatch"):
        build_verified_origin_panel(root, spx_manifest, vix_manifest, output)


def test_rejected_vix_quality_manifest_cannot_be_promoted(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    record = json.loads(vix_manifest.read_text())
    record["quality"]["accepted"] = False
    vix_manifest.write_text(json.dumps(record))
    with pytest.raises(PanelProvenanceError, match="VIX: acquisition not accepted"):
        build_verified_origin_panel(root, spx_manifest, vix_manifest, output)


def test_frozen_window_mismatch_is_rejected(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    record = json.loads(spx_manifest.read_text())
    record["frozen_window"]["end_exclusive"] = "2024-01-05"
    spx_manifest.write_text(json.dumps(record))
    with pytest.raises(PanelProvenanceError, match="locked protocol"):
        build_verified_origin_panel(root, spx_manifest, vix_manifest, output)


def test_unsafe_manifest_or_artifact_path_is_rejected(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    with pytest.raises(PanelProvenanceError, match="outside|escapes"):
        build_verified_origin_panel(root, output / "invalid.json", vix_manifest, output)

    record = json.loads(spx_manifest.read_text())
    record["yahoo"]["relative_path"] = "../../outside.csv"
    spx_manifest.write_text(json.dumps(record))
    with pytest.raises(PanelProvenanceError, match="traversal"):
        build_verified_origin_panel(root, spx_manifest, vix_manifest, output)


def test_manifest_quality_is_recomputed_not_trusted_blindly(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    record = json.loads(spx_manifest.read_text())
    record["production_quality"]["expected_session_count"] = 1
    spx_manifest.write_text(json.dumps(record))
    with pytest.raises(PanelProvenanceError, match="independent quality"):
        build_verified_origin_panel(root, spx_manifest, vix_manifest, output)


def test_source_identity_must_be_official_and_canonical(sources) -> None:
    root, output, spx_manifest, vix_manifest = sources
    record = json.loads(vix_manifest.read_text())
    record["source_url"] = "https://example.org/fake-vix.csv"
    vix_manifest.write_text(json.dumps(record))
    with pytest.raises(PanelProvenanceError, match="VIX: invalid schema/source"):
        build_verified_origin_panel(root, spx_manifest, vix_manifest, output)
