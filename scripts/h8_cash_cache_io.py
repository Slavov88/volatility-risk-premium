"""Lossless access to Task3-only archived CSV caches; never changes model code."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import zipfile
import pandas as pandas_original
from vrp.quant_extension import ROOT,csv_immutable as original_csv,checked_hash as original_hash

CACHE=ROOT/'outputs/h8_cash_yield'


def archived(path):
    if not isinstance(path,(str,Path)):return False
    path=Path(path)
    try:path.resolve().relative_to(CACHE.resolve())
    except ValueError:return False
    return not path.exists() and path.with_name(path.name+'.zip').exists()


def read_bytes(path):
    path=Path(path)
    if not archived(path):return path.read_bytes()
    index=json.loads((CACHE/'archive_storage.json').read_bytes())
    key=path.resolve().relative_to(ROOT.resolve()).as_posix()
    entry=next(r for r in index['entries'] if r['logical_path']==key)
    archive=path.with_name(path.name+'.zip')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=entry['archive_sha256']:raise ValueError('Cache archive hash mismatch')
    with zipfile.ZipFile(archive) as z:
        if z.namelist()!=[path.name] or z.getinfo(path.name).file_size!=entry['logical_bytes']:raise ValueError('Cache archive schema')
        raw=z.read(path.name)
    if hashlib.sha256(raw).hexdigest()!=entry['logical_sha256']:raise ValueError('Logical CSV hash mismatch')
    return raw


def checked_hash(path,expected):
    if archived(path):
        if hashlib.sha256(read_bytes(path)).hexdigest()!=expected:raise ValueError('Archived CSV provenance mismatch')
    else:original_hash(path,expected)


def csv_immutable(path,frame):
    if not archived(path):return original_csv(path,frame)
    raw=frame.to_csv(index=False,float_format='%.17g',lineterminator='\n').encode()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=hashlib.sha256(read_bytes(path)).hexdigest():raise ValueError('Archived immutable CSV differs')
    return digest


class PandasAdapter:
    def __getattr__(self,name):return getattr(pandas_original,name)
    def read_csv(self,path,*args,**kwargs):
        if archived(path):path=BytesIO(read_bytes(path))
        return pandas_original.read_csv(path,*args,**kwargs)


def install(module):
    if hasattr(module,'pd'):module.pd=PandasAdapter()
    if hasattr(module,'csv_immutable'):module.csv_immutable=csv_immutable
    if hasattr(module,'checked_hash'):module.checked_hash=checked_hash
