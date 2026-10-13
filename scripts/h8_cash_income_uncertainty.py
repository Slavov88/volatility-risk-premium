"""Fixed cash-income/log-allocation uncertainty on paired historical streams."""
from datetime import date
import json
import numpy as np
import pandas as pd
from vrp.cash_yield import ROOT,OUT,MODELS,SCENARIOS
from vrp.quant_extension import persist,implementation,csv_immutable,sha,block_indices,checked_hash


def execute():
    code=implementation(['scripts/h8_cash_income_uncertainty.py'])
    result=json.loads((OUT/'results.json').read_bytes());rows=[];annual=[]
    example=pd.read_csv(OUT/'zero_combined_5bps.csv',float_precision='round_trip')
    n=len(example);years=(date.fromisoformat(example.Date.iloc[-1])-date.fromisoformat(example.Date.iloc[0])).days/365.25
    arrays={}
    for scenario in SCENARIOS:
        for model in MODELS:
            file=f'{scenario}_{model}_5bps.csv';checked_hash(OUT/file,result['ledger_sha256'][file])
            log=pd.read_csv(OUT/file,float_precision='round_trip')
            prior=np.r_[1.,log.nav.to_numpy()[:-1]];normalized=log.cash_interest.to_numpy()/prior
            parts=pd.read_csv(OUT/f'{scenario}_{model}_daily_attribution.csv',float_precision='round_trip')
            arrays[scenario,model]=np.c_[normalized,parts[['direct_interest_log','changed_equity_dividend_log','changed_fee_log']].to_numpy()]
            for year in range(2012,2027):
                mask=log.Date.str.startswith(str(year)).to_numpy()
                annual.append({'scenario':scenario,'strategy':model,'cash_credit_year':year,'n_marks':int(mask.sum()),
                    'cash_income_initial_nav':float(log.cash_interest[mask].sum()),
                    'cash_income_normalized_sum':float(normalized[mask].sum()),
                    'terminal_stub':year==2026})
    for block in [21,63,126]:
        rng=np.random.default_rng(1729)
        counts=np.array([np.bincount(block_indices(n,rng,block),minlength=n) for _ in range(1000)],float)
        for (scenario,model),values in arrays.items():
            draws=counts@values/years;estimates=values.sum(axis=0)/years
            for j,key in enumerate(['annual_normalized_cash_income','annual_direct_interest_log_contribution',
                                     'annual_changed_equity_dividend_log_contribution','annual_changed_fee_log_contribution']):
                rows.append({'block':block,'scenario':scenario,'strategy':model,'metric':key,'estimate':float(estimates[j]),
                             'ci95':np.quantile(draws[:,j],[.025,.975]).tolist()})
    result={'implementation':code,'primary_results_sha256':sha(OUT/'results.json'),'uncertainty':rows,'annual_cash_credit':annual,
            'scope':'Paired block resampling of normalized actual income and log allocation streams; fixed original elapsed years. Conditional historical uncertainty, not proof of future cash yields.'}
    for name,values in [('cash_income_uncertainty',rows),('annual_cash_credit',annual)]:
        frame=pd.DataFrame(values)
        if 'ci95' in frame:frame['ci95']=frame.ci95.map(json.dumps)
        csv_immutable(OUT/(name+'.csv'),frame)
    persist(OUT/'income_uncertainty.json',result);persist(ROOT/'data/manifests/h8_cash_income_uncertainty_v2.json',result)
    print('Cash-income/component uncertainty completed',flush=True);return result


if __name__=='__main__':execute()
