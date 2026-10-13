import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_workspace_relative_paths_resolved_before_freeze_verification(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/run_interim_targets.py"
    spec = importlib.util.spec_from_file_location("target_runner",path)
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    monkeypatch.setattr(runner,"code_identity",lambda commit:{})
    root = path.parents[1]
    monkeypatch.setattr(runner.subprocess,"run",lambda args,**kw:SimpleNamespace(returncode=0,
        stdout=(root/args[-1].split(":",1)[1]).read_bytes()))
    seen = []
    def verify(*args):
        seen.extend(args)
        raise ValueError("path boundary reached")
    monkeypatch.setattr(runner,"verify_interim",verify)
    with pytest.raises(ValueError,match="path boundary"):
        runner.run(Path("data/raw"),Path("data/processed"),Path("data/processed/interim/freeze.json"),
            Path("data/manifests/auth.json"),"a"*40)
    assert all(p.is_absolute() for p in seen)
    assert seen[2] == (Path.cwd()/"data/processed/interim/freeze.json").resolve()
