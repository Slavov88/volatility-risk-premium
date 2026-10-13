"""Fixed protocol post-2014 evaluation sensitivity; reuse unchanged forecasts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from vrp.dates import as_date
from vrp.forecast_analysis import qlike
from vrp.inference import overlap_l0, holm_adjust_two
from vrp.provisional_analysis import inputs, checked_mean, checked_regression, persist, STATUS, identity
from vrp.recursive_garch import VARIANTS
from vrp.calendar import trailing_30c_sessions, trailing_exchange_sessions
from vrp.evaluation import naive_variance_30c, naive_variance_21t


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parser-path',type=Path,required=True)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--code-commit',required=True);args=p.parse_args()
    sys.path.insert(0,str(args.parser_path.resolve()))
    ident=identity(args.code_commit,['scripts/post2014_forecast_sensitivity.py','src/vrp/provisional_analysis.py',
        'src/vrp/inference.py','src/vrp/forecast_analysis.py','src/vrp/evaluation.py'])
    targets,daily,_=inputs();sample=targets.loc[targets.origin>='2014-10-06'].copy()
    returns={as_date(d):float(v) for d,v in zip(daily.Date,daily.log_return) if np.isfinite(v)}
    whole=json.loads((args.root/'h3_h4.json').read_bytes());results=[]
    for variant in VARIANTS:
        path=next((args.root/'garch'/variant).glob('*/forecasts.json'))
        if hashlib.sha256(path.read_bytes()).hexdigest()!=whole['garch_sources'][variant]['forecasts_sha256']:
            raise ValueError('Verified forecast artifact mismatch')
        records={r['origin']:r for r in json.loads(path.read_bytes())['records']}
        for horizon in ('30c','21t'):
            baseline=next(r for r in whole['analyses'] if r['variant']==variant)['horizons'][horizon]
            common=[d for d in baseline['common_origins'] if d>='2014-10-06']
            if common!=sample.origin.tolist():raise ValueError('Fixed subset mask mismatch')
            actual=sample[f'rvar_cc_fwd_{horizon}'].to_numpy();pred={'vix':sample.ivar.to_numpy(),
                'garch':np.array([records[d][f'garch_{horizon}'] for d in common])}
            naive=[]
            for text in common:
                origin=as_date(text);sessions=trailing_30c_sessions(origin) if horizon=='30c' else trailing_exchange_sessions(origin,21)
                fn=naive_variance_30c if horizon=='30c' else naive_variance_21t
                naive.append(fn(origin,[(d,returns[d]) for d in sessions]))
            pred['naive']=np.array(naive);loss={name:(actual-v)**2 for name,v in pred.items()}
            l0=overlap_l0(common);lags=[l0,42,63] if horizon=='30c' else [20,10,21,42]
            for lag in dict.fromkeys(lags):
                contrasts={name:checked_mean(loss[a]-loss[b],lag) for name,a,b in
                    [('vix_vs_garch','vix','garch'),('vix_vs_naive','vix','naive'),('garch_vs_naive','garch','naive')]}
                adjusted=holm_adjust_two([contrasts['vix_vs_naive']['p_value'],contrasts['garch_vs_naive']['p_value']])
                for name,value in zip(['vix_vs_naive','garch_vs_naive'],adjusted):contrasts[name]['holm_p_value']=value
                results.append({'variant':variant,'horizon':horizon,'lag':lag,'n':len(common),
                    'h3':contrasts,'h4':checked_regression(actual,np.column_stack([pred['vix'],pred['garch']]),lag),
                    'qlike_vix_vs_garch':checked_mean(qlike(actual,pred['vix'])-qlike(actual,pred['garch']),lag),
                    'metrics':{name:{'rmse':float(np.sqrt(v.mean())),'mae':float(np.mean(abs(actual-pred[name])))} for name,v in loss.items()}})
    output={'status':STATUS,'cutoff':'2014-10-06','post2003_oos':'identical to full OOS starting 2007',
        'forecast_refits':0,'same_frozen_forecasts':True,'implementation':ident,
        'h3_h4_source_sha256':hashlib.sha256((args.root/'h3_h4.json').read_bytes()).hexdigest(),'analyses':results}
    print('post2014 sensitivity',persist(args.root/'h3_h4_post2014.json',output),flush=True)


if __name__=='__main__':main()
