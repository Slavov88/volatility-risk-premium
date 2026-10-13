"""Independently audit full calendar overlap and fresh deterministic GARCH fits."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from vrp.calendar import forward_30c_sessions
from vrp.dates import as_date
from vrp.provisional_analysis import inputs, persist, STATUS
from vrp.recursive_garch import fit_origin, training_slice


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parser-path",type=Path,required=True);parser.add_argument("--root",type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.parser_path.resolve()))
    targets,daily,_=inputs();returns=daily.dropna(subset=["log_return"])
    days=[as_date(d) for d in returns.Date];values=returns.log_return.to_numpy()
    origins=[as_date(d) for d in targets.origin];sets=[set(forward_30c_sessions(d)) for d in origins]
    l0=0;witness=None
    for i,s in enumerate(sets):
        for j in range(i+1,len(sets)):
            if origins[j]>=max(s):break
            if s&sets[j] and j-i>l0:l0=j-i;witness=[origins[i].isoformat(),origins[j].isoformat(),sorted(d.isoformat() for d in s&sets[j])]
    result={"status":STATUS,"independent_set_intersection_L0":l0,"overlap_witness":witness,
        "garch_fresh_refits":[],"source_preservation":"pinned freeze/targets verified by loader"}
    for path in sorted((args.root/"garch").glob("*/*/forecasts.json")):
        report=json.loads(path.read_bytes());config=json.loads((path.parent/"configuration.json").read_bytes())
        lookup={r['origin']:r for r in report['records']}
        # Date-only first/final origin and first origins of frozen crisis years.
        selected=[report['records'][0]['origin'],report['records'][-1]['origin']]
        selected += [next(r['origin'] for r in report['records'] if r['origin'].startswith(str(y))) for y in (2008,2020,2022)]
        for text in selected:
            old=lookup[text];_,_,train=training_slice(days,values,as_date(text),config['window'])
            fresh=fit_origin(train,config['distribution'],len(old['forecast_sessions']),True)
            if fresh['status']!='CONVERGED':raise ValueError('Fresh audit fit failed')
            fresh['garch_30c']=(365/30)*sum(fresh['daily_decimal_variances'][:old['session_count_30c']])
            fresh['garch_21t']=(252/21)*sum(fresh['daily_decimal_variances'][:21])
            # JSON object keys are strings in the persisted artifact, while
            # diagnostic lag keys originate as integers in Python.
            fresh=json.loads(json.dumps(fresh,allow_nan=False))
            for key,v in fresh.items():
                if v!=old[key]:raise ValueError('Fresh fit differs: '+text+' '+key)
            result['garch_fresh_refits'].append({'variant':report['variant'],'origin':text,
                'all_parameters_forecasts_warnings_residual_diagnostics_exactly_equal':True})
    result['analysis_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.root.glob('h*.json')}
    print('execution_audit',persist(args.root/'execution_audit.json',result),flush=True)


if __name__=='__main__':main()
