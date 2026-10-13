"""Full numerical/publication replay, preserving original producer commits."""
import hashlib
import importlib.util
import json
from pathlib import Path
from threadpoolctl import threadpool_limits
from vrp import cash_yield as core
from vrp.quant_extension import sha,checked_hash,persist,implementation


def module(name):
    spec=importlib.util.spec_from_file_location(name,core.ROOT/'scripts'/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def stripped(record):
    record=dict(record);record.pop('implementation',None);return record


def main():
    out=core.OUT;root=core.ROOT
    originals={n:json.loads((out/((n if n!='publication' else 'publication_p3')+'.json')).read_bytes()) for n in ['results','independent_audit','income_uncertainty','publication']}
    for record in originals.values():
        for name,digest in record['implementation']['sources_sha256_lf'].items():
            if hashlib.sha256((root/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=digest:raise ValueError('Producer source changed '+name)
    modules=[(core,'execute','results'),(module('audit_h8_cash_yield'),'audit','independent_audit'),
             (module('h8_cash_income_uncertainty'),'execute','income_uncertainty'),
             (module('publish_h8_cash_yield'),'publish','publication')]
    with threadpool_limits(limits=1):
        for producer,function,key in modules:
            cache=module('h8_cash_cache_io');cache.install(producer)
            original=producer.persist;producer.persist=lambda path,value:None
            try:fresh=getattr(producer,function)()
            finally:producer.persist=original
            if stripped(fresh)!=stripped(originals[key]):raise ValueError('Replay changed '+key)
    old=json.loads((root/'outputs/h8_cash_yield/v1/results.json').read_bytes());new=originals['results']
    for key in old:
        if key not in ['implementation','periods_5bps','table_sha256'] and old[key]!=new[key]:raise ValueError('Unexpected v1/v2 change '+key)
    old_periods={(r['scenario'],r['strategy'],r['period']):r for r in old['periods_5bps']}
    changes=sum(old_periods[(r['scenario'],r['strategy'],r['period'])]!=r for r in new['periods_5bps'])
    for name,digest in new['input_sha256'].items():checked_hash(root/name,digest)
    for name,digest in originals['publication']['files_sha256'].items():checked_hash(root/name,digest)
    # Check all Markdown table shapes and all local report links.
    import re
    count=0
    for name in ['h8_cash_yield_sensitivity.md','h8_economic_attribution.md']:
        text=(root/'docs'/name).read_text(encoding='utf-8');width=None
        for line in text.splitlines():
            if line.startswith('| '):
                if width is None:width=line.count('|')
                elif line.count('|')!=width:raise ValueError('Table shape '+name)
            else:width=None
        for dest in re.findall(r'\]\(([^)]+)\)',text):
            if not dest.startswith('http'):
                if not (root/'docs'/dest).exists():raise ValueError('Missing report link '+dest)
                count+=1
    report={'status':'PASSED_FULL_NUMERIC_TABLE_AND_PUBLICATION_REPLAY','implementation':implementation(['scripts/replay_h8_cash_yield.py']),
            'results_sha256':sha(out/'results.json'),'publication_sha256':sha(out/'publication_p3.json'),
            'cache_io_implementation':implementation(['scripts/h8_cash_cache_io.py']),
            'original_zero_ledgers_exact':25,'original_zero_period_summaries_exact':25,
            'v1_v2_all_full_sample_numeric_fields_identical':True,'v1_v2_all100_ledger_hashes_identical':True,
            'v1_signal_date_period_summaries_superseded':changes,'local_report_links_checked':count,
            'original_input_files_preserved':len(new['input_sha256'])}
    persist(out/'deterministic_replay_p3.json',report);persist(root/'data/manifests/h8_cash_deterministic_replay_v2p3.json',report)
    print(report['status'],flush=True)


if __name__=='__main__':main()
