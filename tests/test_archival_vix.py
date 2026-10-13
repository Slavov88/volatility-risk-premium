import copy
import pandas as pd
import pytest

from vrp.archival_vix import (AUTHORIZATION, ARCHIVE_SHA, ARCHIVE_URL, INSERT_DATE,
    TRANSFORMATION, insert_archival_close, verify_archive)
from vrp.processed_panel import PanelProvenanceError


@pytest.fixture
def evidence():
    return {"date": INSERT_DATE, "close": 24.64, "source_url": ARCHIVE_URL,
        "artifact_sha256": ARCHIVE_SHA, "unit": "annualized percentage points",
        "sheet": "OHLC", "date_cell": "A2528", "close_cell": "E2528",
        "numeric_cell_verified": True, "transformation_version": TRANSFORMATION}


def source():
    return pd.DataFrame({"Date": ["1999-12-30"], "CLOSE": [24.76]})


def test_exact_insertion_and_source_immutability(evidence):
    original = source(); before = original.copy(deep=True)
    result = insert_archival_close(original, evidence, AUTHORIZATION)
    pd.testing.assert_frame_equal(original, before)
    assert result.Date.tolist() == ["1999-12-30", INSERT_DATE]
    assert result.CLOSE.tolist() == [24.76, 24.64]
    assert result.vix_source.tolist() == ["cboe_csv", "cboe_xls_archival_insertion"]


@pytest.mark.parametrize("field,value", [("date", "1997-01-31"), ("close", 24.65),
    ("source_url", "https://example.org"), ("artifact_sha256", "0"*64),
    ("unit", "decimal"), ("close_cell", "E2529"), ("numeric_cell_verified", False)])
def test_evidence_drift_rejected(evidence, field, value):
    evidence[field] = value
    with pytest.raises(PanelProvenanceError, match="evidence mismatch"):
        insert_archival_close(source(), evidence, AUTHORIZATION)


@pytest.mark.parametrize("value", [24.64, 24.65])
def test_original_collision_even_if_same_value(evidence, value):
    data = pd.DataFrame({"Date": [INSERT_DATE], "CLOSE": [value]})
    with pytest.raises(PanelProvenanceError, match="collision"):
        insert_archival_close(data, evidence, AUTHORIZATION)


def test_duplicate_source_and_unauthorized_insertions(evidence):
    with pytest.raises(PanelProvenanceError, match="Duplicate"):
        insert_archival_close(pd.concat([source(), source()]), evidence, AUTHORIZATION)
    auth = copy.deepcopy(AUTHORIZATION)
    auth["allowed_insertions"].append({"date": "1997-01-31", "close": 19.47})
    with pytest.raises(PanelProvenanceError, match="Unauthorized"):
        insert_archival_close(source(), evidence, auth)
    with pytest.raises(PanelProvenanceError, match="Unauthorized"):
        insert_archival_close(source(), evidence, {})


def test_missing_tampered_archive_and_wrong_hash(tmp_path):
    descriptor = {"source_url": ARCHIVE_URL, "sha256": ARCHIVE_SHA, "relative_path": "archive.xls"}
    with pytest.raises(PanelProvenanceError, match="inaccessible"):
        verify_archive(tmp_path, descriptor)
    (tmp_path / "archive.xls").write_bytes(b"tampered")
    with pytest.raises(PanelProvenanceError, match="SHA-256 mismatch"):
        verify_archive(tmp_path, descriptor)
    descriptor["sha256"] = "0"*64
    with pytest.raises(PanelProvenanceError, match="contract mismatch"):
        verify_archive(tmp_path, descriptor)
