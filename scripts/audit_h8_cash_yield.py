"""Independent vintage selection, accounting allocation and original controls."""
from datetime import date,timedelta
from decimal import Decimal,localcontext
import csv
import json
import math
import numpy as np
import pandas as pd
from vrp.cash_yield import ROOT,OUT,MODELS,COSTS,SCENARIOS
from vrp.quant_extension import checked_hash,sha,persist,implementation,csv_immutable


def audit():
    code=implementation(['scripts/audit_h8_cash_yield.py'])
    result=json.loads((OUT/'results.json').read_bytes());source=result['rates']
    checked_hash(ROOT/'data/manifests/h8_cash_rate_source_v1.json',result['rate_source_manifest_sha256'])
    for record in source['downloads']:checked_hash(ROOT/record['path'],record['sha256'])
    rate_checks={};missing=[];snapshots=[]
    for series in ['DGS1MO','DTB4WK']:
        path=ROOT/source['series'][series]['initial_path']
        raw=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
        valid=[r for r in raw if r[series] not in ['', '.']]
        schedule=pd.read_csv(OUT/(series+'_schedule.csv'),float_precision='round_trip')
        errors=[]
        for i,row in enumerate(schedule.itertuples(index=False)):
            if i==0:continue
            eligible=[r for r in valid if r['period_start_date']<row.start_open and r['realtime_start_date']<row.start_open]
            choice=max(eligible,key=lambda r:r['period_start_date'])
            days=(date.fromisoformat(row.Date)-date.fromisoformat(row.start_open)).days
            if choice['period_start_date']!=row.observation_date or choice['realtime_start_date']!=row.initial_release_date:
                raise ValueError('Independent vintage eligibility selection mismatch')
            with localcontext() as ctx:
                ctx.prec=40;p=Decimal(choice[series])/100
                annual=p if series=='DGS1MO' else p/360/(1-p*28/360)*365
                factor=float(annual*days/365)
            errors.append(abs(factor-row.cash_factor))
            if days!=row.elapsed_days:raise ValueError('Independent calendar count mismatch')
        if max(errors)>1e-14:raise ValueError('Independent rate/units/day-count conversion mismatch')
        rate_checks[series]={'intervals':len(schedule)-1,'max_factor_error':max(errors),
            'max_quote_age_days':int(schedule.age_days.max()),'elapsed_days_total':int(schedule.elapsed_days.sum()),
            'multi_day_intervals':int(schedule.elapsed_days.gt(1).sum()),
            'max_elapsed_days':int(schedule.elapsed_days.max())}
        current=pd.read_csv(ROOT/source['series'][series]['current_path'],float_precision='round_trip')
        known={r['period_start_date']:r for r in valid}
        for row in current.dropna(subset=[series]).itertuples(index=False):
            if row.observation_date not in known:
                initial=next((r for r in raw if r['period_start_date']==row.observation_date),None)
                missing.append({'series':series,'observation_date':row.observation_date,
                                'current_percent':float(getattr(row,series)),
                                'initial_release_value':None,
                                'initial_realtime_start_date':initial['realtime_start_date'] if initial else None,
                                'treatment':'Not backfilled; last eligible initial-release quote remains locked.'})
        for vintage in ['2012-01-03','2018-04-05','2020-03-23','2022-11-04','2025-12-31']:
            path=ROOT/source['directory']/f'{series}_vintage_{vintage}.csv'
            snap=pd.read_csv(path,float_precision='round_trip');column=series+'_'+vintage.replace('-','')
            eligible=[r for r in valid if r['realtime_start_date']<=vintage and r['period_start_date']<=vintage]
            choice=max(eligible,key=lambda r:r['period_start_date'])
            check=snap.loc[snap.observation_date.eq(choice['period_start_date'])]
            if len(check)!=1 or not math.isfinite(float(check[column].iloc[0])):raise ValueError('Vintage snapshot does not contain selected quote')
            error=float(check[column].iloc[0])-float(choice[series])
            snapshots.append({'series':series,'vintage_date':vintage,'chosen_observation':choice['period_start_date'],
                              'initial_percent':float(choice[series]),'snapshot_percent':float(check[column].iloc[0]),
                              'difference':error,'snapshot_sha256':sha(path)})
            if abs(error)>1e-12:raise ValueError('Independent selected quote vintage value mismatch')
    # Numeric summaries verified independently from saved return streams.
    errors=[];controls=[];nominal=[];rankings=[]
    spy_meta=json.loads((ROOT/'data/manifests/quant_extension_spy.json').read_bytes())
    checked_hash(ROOT/spy_meta['path'],result['spy_sha256'])
    market=pd.read_csv(ROOT/spy_meta['path'],float_precision='round_trip').set_index('Date')
    def nominal_components(log):
        prices=market.loc[log.Date];opening=prices.Open.to_numpy();closing=prices.Close.to_numpy()
        priorclose=np.r_[opening[0],closing[:-1]];final=log.final_open_mark.to_numpy(bool)
        overnight=log.old_shares.to_numpy()*(opening-priorclose)
        intraday=np.where(final,0.,log.shares.to_numpy()*(closing-opening))
        return np.array([math.fsum(map(float,overnight+intraday)),math.fsum(map(float,log.dividend_cash)),
                         math.fsum(map(float,log.cash_interest)),-math.fsum(map(float,log.cost))])
    for scenario in SCENARIOS:
        for model in MODELS:
            for cost in COSTS:
                name=f'{scenario}_{model}_{cost}bps.csv';checked_hash(OUT/name,result['ledger_sha256'][name])
                log=pd.read_csv(OUT/name,float_precision='round_trip');r=log['return'].to_numpy();n=len(r)
                mean=math.fsum(map(float,r))/n;vol=math.sqrt(252*math.fsum(float((v-mean)**2) for v in r)/(n-1))
                years=(date.fromisoformat(log.Date.iloc[-1])-date.fromisoformat(log.Date.iloc[0])).days/365.25
                cagr=math.expm1(math.fsum(math.log1p(v) for v in r)/years)
                nav=1.;peak=1.;dd=0.
                for v in r:nav*=1+v;peak=max(peak,nav);dd=min(dd,nav/peak-1)
                metrics=next(a for a in result['summary'] if a['scenario']==scenario and a['strategy']==model and a['cost_bps']==cost)
                zero=pd.read_csv(OUT/f'zero_{model}_{cost}bps.csv',float_precision='round_trip')
                parts=nominal_components(log);zp=nominal_components(zero);delta=parts-zp
                terminal_delta=float(log.nav.iloc[-1]-zero.nav.iloc[-1]);residual=terminal_delta-float(delta.sum())
                errors.extend([abs(float(parts.sum())-(log.nav.iloc[-1]-1)),abs(residual)])
                nominal.append({'scenario':scenario,'strategy':model,'cost_bps':cost,
                    'terminal_nav_change':terminal_delta,'changed_equity_pnl_initial_nav':float(delta[0]),
                    'changed_dividends_initial_nav':float(delta[1]),'cash_interest_initial_nav':float(delta[2]),
                    'changed_negative_fees_initial_nav':float(delta[3]),'residual':residual})
                errors.extend([abs(vol-metrics['annual_vol']),abs(cagr-metrics['cagr']),abs(dd-metrics['max_drawdown']),
                               abs(math.fsum(map(float,log.cash_interest))-metrics['cash_income_initial_nav'])])
                if model=='buyhold':
                    zero=pd.read_csv(OUT/f'zero_{model}_{cost}bps.csv',float_precision='round_trip')
                    if not np.array_equal(log['return'],zero['return']) or log.cash_interest.ne(0).any():raise ValueError('Buyhold zero-cash control changed')
                    controls.append(scenario+'_'+str(cost))
                att=next(a for a in result['attributions'] if a['scenario']==scenario and a['strategy']==model and a['cost_bps']==cost)
                errors.append(abs(att['incremental_log_growth']-math.fsum(att[k] for k in ['direct_interest_log_contribution','changed_equity_dividend_log_contribution','changed_fee_log_contribution'])))
                errors.append(abs(metrics['cash_income_cagr_increment']-math.fsum(att[k] for k in ['direct_interest_cagr_allocation','changed_equity_dividend_cagr_allocation','changed_fee_cagr_allocation'])))
    if max(errors)>1e-11:raise ValueError('Independent economic summary/attribution check')
    for scenario in SCENARIOS:
        for cost in COSTS:
            rows=[r for r in result['summary'] if r['scenario']==scenario and r['cost_bps']==cost]
            for metric in ['cagr','sharpe_zero_reference','sharpe_excess_common_dgs1mo','sharpe_excess_scenario_cash','rolling21_target_rmse','annual_vol','max_drawdown']:
                lower=metric in ['rolling21_target_rmse','annual_vol']
                key=lambda r:abs(r[metric]-.1) if metric=='annual_vol' else r[metric]
                order=sorted(rows,key=key,reverse=not lower)
                rankings.append({'scenario':scenario,'cost_bps':cost,'metric':metric,
                                 'ranking_best_to_worst':[r['strategy'] for r in order],
                                 'criterion':'closest10% target' if metric=='annual_vol' else 'lower' if lower else 'higher'})
    for name,digest in result['input_sha256'].items():checked_hash(ROOT/name,digest)
    report={'status':'PASSED_INDEPENDENT_VINTAGE_AND_ECONOMIC_AUDIT','implementation':code,
            'results_sha256':sha(OUT/'results.json'),'rate_checks':rate_checks,
            'current_finite_but_initially_missing':missing,'snapshot_checks':snapshots,
            'max_independent_summary_error':max(errors),'buyhold_unchanged_controls':len(controls),
            'rankings':rankings,'nominal_terminal_attribution':nominal,
            'all_original_inputs_preserved':len(result['input_sha256'])}
    for name,records in [('source_missing',missing),('vintage_checks',snapshots),('rankings',rankings),('nominal_attribution',nominal)]:
        frame=pd.DataFrame(records)
        for c in frame:
            if frame[c].map(lambda x:isinstance(x,list)).any():frame[c]=frame[c].map(lambda x:json.dumps(x) if isinstance(x,list) else x)
        csv_immutable(OUT/(name+'.csv'),frame)
    persist(OUT/'independent_audit.json',report);persist(ROOT/'data/manifests/h8_cash_independent_audit_v2.json',report)
    print(report['status'],flush=True);return report


if __name__=='__main__':audit()
