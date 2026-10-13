"""Lossless-cache adversaries: exact bytes, corruption and original-source scope."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import pandas as pd
import pytest


def fixture(tmp_path):
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('cash_cache_test',root/'scripts/h8_cash_cache_io.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=tmp_path;module.CACHE=tmp_path/'outputs/h8_cash_yield'
    path=module.CACHE/'v2/example.csv';path.parent.mkdir(parents=True)
    frame=pd.DataFrame({'cash':[.25,.30],'nav':[1.,1.02]})
    raw=frame.to_csv(index=False,float_format='%.17g',lineterminator='\n').encode()
    archive=path.with_name(path.name+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:z.writestr(path.name,raw)
    index={'entries':[{'logical_path':path.relative_to(tmp_path).as_posix(),'logical_sha256':hashlib.sha256(raw).hexdigest(),
                      'logical_bytes':len(raw),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}]}
    (module.CACHE/'archive_storage.json').write_text(json.dumps(index))
    return module,path,frame,raw,index


def test_cache_preserves_exact_csv_and_refuses_changed_numeric_output(tmp_path):
    module,path,frame,raw,_=fixture(tmp_path)
    assert module.read_bytes(path)==raw
    digest=hashlib.sha256(raw).hexdigest();module.checked_hash(path,digest)
    assert module.csv_immutable(path,frame)==digest
    assert module.PandasAdapter().read_csv(path,float_precision='round_trip').equals(frame)
    changed=frame.copy();changed.loc[0,'nav']+=1e-15
    with pytest.raises(ValueError):module.csv_immutable(path,changed)


def test_cache_rejects_corruption_and_never_substitutes_for_original_h8(tmp_path):
    module,path,frame,raw,index=fixture(tmp_path)
    archive=path.with_name(path.name+'.zip');archive.write_bytes(b'corrupt')
    with pytest.raises(ValueError):module.read_bytes(path)
    outside=tmp_path/'original_h8.csv'
    with zipfile.ZipFile(outside.with_name(outside.name+'.zip'),'w') as z:z.writestr(outside.name,raw)
    assert not module.archived(outside)
    with pytest.raises(FileNotFoundError):module.PandasAdapter().read_csv(outside)
