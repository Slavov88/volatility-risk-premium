"""Replay committed numerical content without overwriting producer identities."""
import json
import hashlib
import math
import subprocess
import importlib.util
import numpy as np
from vrp import quant_failure as primary, quant_failure_audit as independent
from vrp.quant_extension import sha, checked_hash, persist, implementation


def without_identity(value):
    value=dict(value); value.pop('implementation',None); return value


def main():
    root=primary.ROOT; out=primary.OUT
    saved=json.loads((out/'results.json').read_bytes()); audit=json.loads((out/'independent_audit.json').read_bytes())
    publication=json.loads((out/'publication.json').read_bytes())
    for record in [saved,audit,publication]:
        for name,digest in record['implementation']['sources_sha256_lf'].items():
            raw=(root/name).read_bytes().replace(b'\r\n',b'\n')
            if hashlib.sha256(raw).hexdigest()!=digest: raise ValueError('Producer source changed '+name)
    original=primary.persist; captured={}
    def capture(path,value): captured[str(path)]=value
    primary.persist=capture
    try: fresh=primary.execute()
    finally: primary.persist=original
    if without_identity(fresh)!=without_identity(saved): raise ValueError('Primary numeric replay changed')
    original=independent.persist; independent.persist=capture
    try: fresh_audit=independent.execute_audit()
    finally: independent.persist=original
    if without_identity(fresh_audit)!=without_identity(audit): raise ValueError('Audit numeric replay changed')
    spec=importlib.util.spec_from_file_location('quant_failure_publication',root/'scripts/publish_quant_failure.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    original=module.persist; module.persist=capture
    try: fresh_publication=module.publish()
    finally: module.persist=original
    if without_identity(fresh_publication)!=without_identity(publication): raise ValueError('Publication replay changed')
    _,panel,meta,_,_,logs=primary.load_inputs(); n=len(panel); independent_errors={}
    for (model,cost),log in logs.items():
        r=log['return'].to_numpy(); mean=math.fsum(map(float,r))/n
        variance=252*math.fsum(float((v-mean)**2) for v in r)/(n-1)
        expected=meta['h8']['models'][str(cost)][model]
        vol=math.sqrt(variance)
        years=(primary.pd.Timestamp(log.Date.iloc[-1])-primary.pd.Timestamp(log.Date.iloc[0])).days/365.25
        cagr=math.expm1(math.fsum(math.log1p(v) for v in r)/years)
        nav=1.; peak=1.; dd=0.
        for value in r:
            nav*=1+value; peak=max(peak,nav); dd=min(dd,nav/peak-1)
        errors=[abs(vol-expected['annual_vol']),abs(cagr-expected['cagr']),abs(dd-expected['max_drawdown'])]
        if max(errors)>1e-12: raise ValueError('Independent original portfolio metric mismatch')
        independent_errors[f'{model}_{cost}']=max(errors)
    masks=primary.partitions(panel); group_errors={}
    for model in ['buyhold','vix','garch','trailing','combined']:
        full=next(r for r in saved['h8']['summary'] if r['strategy']==model and r['cost_bps']==5)
        for family in [['vix_low','vix_mid','vix_high'],['shock_down','shock_stable','shock_up']]:
            contribution=math.fsum(next(r for r in saved['h8']['regimes'] if r['strategy']==model and r['group']==g)['variance_contribution'] for g in family)
            error=abs(contribution-full['annual_vol']**2)
            if error>1e-13: raise ValueError('Regime variance contribution identity')
            group_errors[model+'_'+family[0]]=error
    for name,digest in saved['input_sha256'].items(): checked_hash(root/name,digest)
    for name,digest in publication['files_sha256'].items(): checked_hash(root/name,digest)
    manifest={'status':'PASSED_DETERMINISTIC_NUMERIC_AND_PUBLICATION_REPLAY',
              'results_sha256':sha(out/'results.json'),'audit_sha256':sha(out/'independent_audit.json'),
              'publication_sha256':sha(out/'publication.json'), 'original_input_files_preserved':len(saved['input_sha256']),
              'independent_original_portfolio_metric_errors':independent_errors,
              'regime_variance_contribution_errors':group_errors,
              'implementation':implementation(['scripts/replay_quant_failure.py'])}
    persist(out/'deterministic_replay.json',manifest)
    persist(root/'data/manifests/quant_failure_deterministic_replay_v1.json',manifest)
    print(manifest['status'],flush=True)


if __name__=='__main__': main()
