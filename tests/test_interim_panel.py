import copy
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

import vrp.interim_panel as interim
from vrp.archival_vix import AUTHORIZATION
from vrp.processed_panel import PanelProvenanceError


@pytest.mark.parametrize("field,value", [("status", "APPROVED"),
    ("independent_freeze_acceptance", "ACCEPTED"), ("communicated_on", "2026-10-14"),
    ("allowed_insertions", [{"date": "1991-03-01", "close": 21.23}])])
def test_unauthorized_metadata_rejected_before_loading_sources(tmp_path, field, value):
    auth = copy.deepcopy(AUTHORIZATION); auth[field] = value
    path = tmp_path / "auth.json"; path.write_text(json.dumps(auth))
    with pytest.raises(PanelProvenanceError, match="Unauthorized"):
        interim.render_interim(tmp_path, Path("spx"), Path("vix"), path, "0"*40)


def test_missing_authorization_and_nonexistent_commit(tmp_path):
    with pytest.raises(PanelProvenanceError, match="authorization"):
        interim.render_interim(tmp_path, Path("spx"), Path("vix"), tmp_path / "absent", "0"*40)
    for commit in ["HEAD", "0"*40]:
        with pytest.raises(PanelProvenanceError, match="commit"):
            interim.code_identity(commit)


@pytest.fixture
def replay(tmp_path, monkeypatch):
    base = Path("interim/test")
    content = {"test.csv": b"origin,ivar\n1999-12-31,0.06071296\n"}
    report = {"source_manifests": {"spx": {"relative_path": "spx.json"}, "vix": {"relative_path": "vix.json"}},
        "implementation": {"commit": "a"*40}, "authorization": AUTHORIZATION,
        "review_status": interim.REVIEW, "confirmatory_execution_allowed": False,
        "outputs": {"test.csv": {"relative_path": (base / "test.csv").as_posix(),
            "sha256": hashlib.sha256(content["test.csv"]).hexdigest()}}}
    panel = pd.DataFrame({"origin": ["1999-12-31"]}); spx = panel.copy()
    monkeypatch.setattr(interim, "render_interim", lambda *args: (base, content, report, panel, spx))
    path = interim.build_interim(tmp_path, tmp_path, Path("spx"), Path("vix"), Path("auth"), "a"*40)
    return tmp_path, path, content, report


def test_immutable_repeat_and_full_replay(replay):
    root, path, content, _ = replay
    original = path.read_bytes()
    again = interim.build_interim(root, root, Path("spx"), Path("vix"), Path("auth"), "a"*40)
    assert again == path and path.read_bytes() == original
    panel, _, report = interim.verify_interim(root, root, path, Path("auth"))
    assert panel.origin.tolist() == ["1999-12-31"]
    with pytest.raises(PanelProvenanceError, match="pending"):
        interim.require_independent_acceptance(report)


@pytest.mark.parametrize("change", ["approval", "authorization", "origins", "extra_metadata"])
def test_modified_manifest_cannot_self_authorize(replay, change):
    root, path, _, _ = replay
    record = json.loads(path.read_bytes())
    if change == "approval": record["confirmatory_execution_allowed"] = True
    elif change == "authorization": record["authorization"]["status"] = "ACCEPTED"
    elif change == "origins": record["row_losses"] = {"common_origins": 999}
    else: record["exploratory_imputation"] = True
    path.write_text(json.dumps(record))
    with pytest.raises(PanelProvenanceError, match="replay mismatch"):
        interim.verify_interim(root, root, path, Path("auth"))


def test_modified_output_rejected(replay):
    root, path, _, record = replay
    (root / record["outputs"]["test.csv"]["relative_path"]).write_bytes(b"changed")
    with pytest.raises(PanelProvenanceError, match="SHA-256"):
        interim.verify_interim(root, root, path, Path("auth"))
