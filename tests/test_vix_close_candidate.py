"""Candidate scientific eligibility stays separate from original acquisition."""
from datetime import date
import hashlib
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from test_processed_panel import sources
import vrp.processed_panel as strict
import vrp.vix_close_candidate as candidate
from vrp.calendar import exchange_sessions
from vrp.returns import log_returns
from vrp.vix_data import vix_quality_report


def frame(dates=("2024-01-02", "2024-01-03")):
    return pd.DataFrame([{"Date": d, "OPEN": 30., "HIGH": 14., "LOW": 12., "CLOSE": 13.} for d in dates])


def validate(data):
    return candidate.validate_close_history(data, start_date=date(2024,1,2), end_exclusive=date(2024,1,4))


def test_bad_open_is_warning_and_old_ohlc_gate_still_rejects():
    data = frame()
    close, report = validate(data)
    assert len(close) == 2 and list(close.CLOSE) == [13.,13.]
    assert report["source_ohlc_diagnostics"]["row_count"] == 2
    assert not vix_quality_report(data, start_date=date(2024,1,2), end_exclusive=date(2024,1,4)).accepted
    assert report["approval_status"] == "CANDIDATE_UNAPPROVED"


def test_missing_sessions_drop_only_origins():
    close, report = validate(frame(("2024-01-02",)))
    assert close.Date.tolist() == ["2024-01-02"]
    assert report["expected_eligible_origins"] == 2
    assert report["missing_predictor_origins"] == ["2024-01-03"]
    assert report["missing_origins_by_year"] == {"2024": 1}
    assert report["missing_oos_origins"] == ["2024-01-03"]


def test_holiday_weekend_and_post_cutoff_rows_are_excluded():
    data = frame(("2025-12-24", "2025-12-25", "2025-12-26", "2025-12-27", "2025-12-31", "2026-01-02"))
    close, report = candidate.validate_close_history(data, start_date=date(2025,12,24), end_exclusive=date(2026,1,1))
    assert "2026-01-02" not in set(close.Date)
    assert report["rejected_non_session_dates"] == ["2025-12-25", "2025-12-27"]
    assert report["outside_origin_window_dates"] == ["2026-01-02"]
    assert report["missing_predictor_origins"] == ["2025-12-29", "2025-12-30"]


@pytest.mark.parametrize("bad", [0., -1., float("nan"), float("inf"), "n/a", None])
def test_invalid_eligible_closes_are_fatal(bad):
    data = frame()
    data["CLOSE"] = data.CLOSE.astype(object)
    data.loc[0,"CLOSE"] = bad
    with pytest.raises(candidate.CloseCandidateError, match="Invalid eligible"):
        validate(data)


@pytest.mark.parametrize("second", [13., 15.])
def test_identical_or_conflicting_duplicates_rejected(second):
    data = frame(("2024-01-02", "2024-01-02"))
    data.loc[1,"CLOSE"] = second
    with pytest.raises(candidate.CloseCandidateError, match="Duplicate"):
        validate(data)


@pytest.mark.parametrize("bad", ["2024-1-2", "2024-01-02T09:00:00", "2024-W01-2", date(2024,1,2)])
def test_ambiguous_dates_rejected(bad):
    data = frame()
    data.loc[0,"Date"] = bad
    with pytest.raises((ValueError, TypeError)):
        validate(data)


@pytest.mark.parametrize("column,value", [("CLOSE",15.), ("CLOSE",11.), ("LOW",15.)])
def test_close_inconsistent_with_available_range_is_fatal(column, value):
    data = frame()
    data.loc[0,column] = value
    with pytest.raises(candidate.CloseCandidateError, match="CLOSE/range"):
        validate(data)


def test_unavailable_auxiliary_bounds_are_explicit_warning():
    close, report = validate(frame().drop(columns=["OPEN","HIGH","LOW"]))
    assert len(close) == 2
    assert report["unavailable_high_or_low_dates"] == ["2024-01-02","2024-01-03"]


def test_historical_special_closures_remain_ineligible():
    data = frame(("2001-09-10","2001-09-11","2001-09-12","2001-09-13","2001-09-14","2001-09-17"))
    close, report = candidate.validate_close_history(data,start_date=date(2001,9,10),end_exclusive=date(2001,9,18))
    assert close.Date.tolist() == ["2001-09-10","2001-09-17"]
    assert len(report["rejected_non_session_dates"]) == 4
    assert report["missing_predictor_origins"] == []


@pytest.fixture
def bundle(sources, monkeypatch):
    monkeypatch.setattr(candidate,"CONVENTIONS",SimpleNamespace(**vars(strict.CONVENTIONS),oos_start_year=2007))
    root, out, spx, vix = sources
    return root, out, spx, vix


def build(bundle):
    root, out, spx, vix = bundle
    return candidate.build_candidate_close_panel(root, spx, vix, out)


def test_candidate_replays_bytes_and_refuses_confirmatory_execution(bundle):
    root, out, _, _ = bundle
    manifest = build(bundle)
    first = manifest.read_bytes()
    assert build(bundle) == manifest and manifest.read_bytes() == first
    panel = candidate.verify_candidate_close_panel(root,out,manifest)
    assert panel.origin.tolist() == ["2024-01-02","2024-01-03"]
    assert panel.ivar.tolist() == pytest.approx([.132**2,.135**2])
    record = json.loads(first)
    assert record["spx_outcome_support"]["removed_rows"] == 0
    assert record["row_losses"]["common_origins"] == 2
    assert not set(panel.columns) & {"rvar","vrp_x","log_return"}
    with pytest.raises(candidate.CandidateNotApprovedError,match="both authors"):
        candidate.load_confirmatory_close_panel(root,out,manifest)
    copied = root / "unapproved_derived.json"
    copied.write_bytes(first)
    with pytest.raises(strict.PanelProvenanceError,match="invalid schema/source"):
        strict.build_verified_origin_panel(root,bundle[2],copied,out)


@pytest.mark.parametrize("kind", ["spx","raw","normalized","derived"])
def test_hash_tampering_rejected(bundle,kind):
    root,out,spx,vix = bundle
    manifest = build(bundle)
    if kind == "derived":
        info = json.loads(manifest.read_text())["outputs"]["candidate_origin_panel.csv"]
        path = out / info["relative_path"]
    else:
        record = json.loads((spx if kind == "spx" else vix).read_text())
        info = record["yahoo" if kind == "spx" else kind]
        path = root / info["relative_path"]
    path.write_bytes(b"tampered")
    with pytest.raises(strict.PanelProvenanceError,match="SHA-256 mismatch"):
        candidate.verify_candidate_close_panel(root,out,manifest)


@pytest.mark.parametrize("field,value", [("contract_version","fake"),("approval_status","APPROVED"),
    ("protocol_version","9.0"),("confirmatory_execution_allowed",True),("original_vix_acquisition_accepted",False)])
def test_provenance_or_self_authorized_approval_rejected(bundle,field,value):
    root,out,_,_ = bundle
    manifest=build(bundle)
    record=json.loads(manifest.read_text())
    record[field]=value
    manifest.write_text(json.dumps(record))
    with pytest.raises(strict.PanelProvenanceError):
        candidate.verify_candidate_close_panel(root,out,manifest)


def test_missing_vix_does_not_delete_spx_outcome_returns(bundle):
    root,out,spx,vix=bundle
    # Create a distinct immutable synthetic missing-predictor acquisition.
    from vrp.vix_data import acquire_vix_history
    from datetime import datetime,timezone
    from unittest.mock import patch
    raw=b"DATE,OPEN,HIGH,LOW,CLOSE\n01/02/2024,30,14,12,13\n"
    with patch("vrp.vix_data.fetch_bytes",return_value=raw):
        missing=acquire_vix_history(root,start_date=date(2024,1,2),end_exclusive=date(2024,1,4),
            retrieved_at=datetime(2024,1,6,12,tzinfo=timezone.utc))
    manifest=candidate.build_candidate_close_panel(root,spx,root/missing.manifest_relative_path,out)
    report=json.loads(manifest.read_text())
    assert report["original_vix_acquisition_accepted"] is False
    assert report["validation"]["missing_predictor_origins"] == ["2024-01-03"]
    spx_record=json.loads(spx.read_text())
    before=(root/spx_record["yahoo"]["relative_path"]).read_bytes()
    full_spx=strict._load_spx(root,spx_record)
    returns=log_returns([date.fromisoformat(d) for d in full_spx.Date],full_spx.Close.tolist())
    assert returns[0][0] == date(2024,1,3)
    assert report["spx_outcome_support"]["preserved_source_rows"] == 2
    assert hashlib.sha256(before).hexdigest() == spx_record["yahoo"]["sha256"]
    with pytest.raises(strict.PanelProvenanceError,match="acquisition not accepted"):
        strict.build_verified_origin_panel(root,spx,root/missing.manifest_relative_path,out)


def test_tail_integration_preserves_all_2026_support_without_new_origins(tmp_path,monkeypatch):
    from datetime import datetime,timezone
    from vrp.spx_data import acquire_spx_index
    from vrp.vix_data import acquire_vix_history
    conventions=SimpleNamespace(**{**vars(candidate.CONVENTIONS),
        "sample_start":"2025-12-24","sample_end":"2025-12-31"})
    monkeypatch.setattr(candidate,"CONVENTIONS",conventions)
    monkeypatch.setattr(strict,"CONVENTIONS",conventions)
    root=tmp_path/"raw"
    out=tmp_path/"processed"
    sessions=exchange_sessions(date(2025,12,24),date(2026,2,2))
    spx_data=pd.DataFrame({"Open":100.,"High":102.,"Low":99.,"Close":101.,"Adj Close":101.,"Volume":1000.},index=pd.to_datetime(sessions))
    timestamp=datetime(2026,3,1,12,tzinfo=timezone.utc)
    spx=acquire_spx_index(root,date(2025,12,24),date(2026,2,3),retrieved_at=timestamp,
        yahoo_download=lambda **_:spx_data,yfinance_version="fixture")
    raw=("DATE,OPEN,HIGH,LOW,CLOSE\n"+"\n".join(d.strftime("%m/%d/%Y")+",30,14,12,13"
        for d in sessions if d<=date(2025,12,31) and d!=date(2025,12,29))+"\n").encode()
    monkeypatch.setattr("vrp.vix_data.fetch_bytes",lambda _:raw)
    vix=acquire_vix_history(root,start_date=date(2025,12,24),end_exclusive=date(2026,1,1),retrieved_at=timestamp)
    manifest=candidate.build_candidate_close_panel(root,root/spx.manifest_relative_path,root/vix.manifest_relative_path,out)
    report=json.loads(manifest.read_text())
    panel=candidate.verify_candidate_close_panel(root,out,manifest)
    assert panel.origin.max()=="2025-12-31"
    assert report["spx_outcome_support"]["post_cutoff_rows"]==21
    assert report["spx_outcome_support"]["preserved_source_rows"]==len(sessions)
    assert report["validation"]["missing_predictor_origins"]==["2025-12-29"]
    assert report["coverage"]["oos_from_2007"]["missing"]==["2025-12-29"]


def test_derived_data_rehashing_cannot_hide_changed_bytes(bundle):
    root,out,_,_=bundle
    manifest=build(bundle)
    record=json.loads(manifest.read_text())
    info=record["outputs"]["candidate_origin_panel.csv"]
    path=out/info["relative_path"]
    altered=path.read_bytes().replace(b"2024-01-02",b"2024-01-04")
    path.write_bytes(altered)
    info["sha256"]=hashlib.sha256(altered).hexdigest()
    manifest.write_text(json.dumps(record))
    with pytest.raises(candidate.CloseCandidateError,match="provenance/validation replay"):
        candidate.verify_candidate_close_panel(root,out,manifest)
