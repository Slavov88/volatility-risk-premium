"""Registered cash-yield sensitivity on unchanged H8 signals and policies."""
from __future__ import annotations
from datetime import date,datetime,time,timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal,localcontext
import json
import math
import numpy as np
import pandas as pd
from vrp.quant_extension import ROOT, OUT as ORIGINAL, sha, checked_hash, persist, csv_immutable, implementation, block_indices, PERIODS
from vrp.quant_portfolio import rebalance, portfolio_metrics, rolling_volatility
from vrp.quant_failure import load_inputs

OUT=ROOT/'outputs/h8_cash_yield/v1'
MODELS=['buyhold','trailing','vix','garch','combined']
COSTS=[0,1,5,10,25]
SCENARIOS=['zero','dgs1mo_full','dgs1mo_half','dtb4wk_full']
NY=ZoneInfo('America/New_York')
STATUS='EXPLORATORY CASH-YIELD SENSITIVITY — PENDING INDEPENDENT COAUTHOR REVIEW'


def prior_evidence():
    paths=[]
    for folder in ['outputs/quant_extension/v2','outputs/empirical_calendar_repair/v1',
                   'outputs/quant_failure_diagnostics/v1','data/processed/interim','data/manifests']:
        paths += [p for p in (ROOT/folder).rglob('*') if p.is_file()
                  and not p.name.startswith('h8_cash_')]
    for name in ['h8_portfolio_economic_value.md','h6_tail_risk_results.md','h7_variance_forecasting_results.md',
                 'h6_failure_analysis.md','h7_failure_analysis.md','h8_failure_analysis.md',
                 'quant_failure_mechanisms.md','quant_failure_progress.md']:
        paths.append(ROOT/'docs'/name)
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))}


def investment_rate(percent,series):
    """Quotes are percent; bill discount requires price-denominator conversion."""
    p=np.asarray(percent,float)/100
    if not np.isfinite(p).all():raise ValueError('Nonfinite quote')
    if series=='DGS1MO':return p
    if series=='DTB4WK':
        price=1-p*28/360
        if (price<=0).any():raise ValueError('Invalid discount price')
        return p/360/price*365
    raise ValueError('Unregistered source')


def rate_schedule(frame,execution_dates,series):
    needed=['period_start_date',series,'realtime_start_date']
    if frame.columns.tolist()!=needed:raise ValueError('Rate input schema')
    valid=frame.dropna(subset=[series]).copy()
    if valid.period_start_date.duplicated().any() or not valid.period_start_date.is_monotonic_increasing:
        raise ValueError('Duplicate or unordered observations')
    if (valid.realtime_start_date<valid.period_start_date).any():raise ValueError('Impossible release chronology')
    records=[]
    for i,end in enumerate(execution_dates):
        if i==0:
            records.append({'Date':end,'start_open':end,'elapsed_days':0,'observation_date':None,
                            'initial_release_date':None,'available_from_ny':None,'quote_percent':0.,
                            'annual_investment_rate':0.,'cash_factor':0.,'age_days':0});continue
        start=execution_dates[i-1]
        if end<=start:raise ValueError('Non-increasing execution dates')
        # Archive vintage date has no verified intraday timestamp. Usable next day.
        eligible=valid.loc[(valid.realtime_start_date<start)&(valid.period_start_date<start)]
        if eligible.empty:raise ValueError('No historically available initial-release quote')
        quote=eligible.iloc[-1]; days=(date.fromisoformat(end)-date.fromisoformat(start)).days
        age=(date.fromisoformat(start)-date.fromisoformat(quote.period_start_date)).days
        if age>15:raise ValueError('Stale quote beyond registered15-day guard')
        release=date.fromisoformat(quote.realtime_start_date)
        available=datetime.combine(release+timedelta(days=1),time.min,NY)
        opening=datetime.combine(date.fromisoformat(start),time(9,30),NY)
        if available>=opening:raise ValueError('Unavailable rate used at interval start')
        rate=float(investment_rate(quote[series],series))
        factor=rate*days/365
        if factor<=-1:raise ValueError('Nonpositive cash account factor')
        records.append({'Date':end,'start_open':start,'elapsed_days':days,
                        'observation_date':quote.period_start_date,'initial_release_date':quote.realtime_start_date,
                        'available_from_ny':available.isoformat(),'quote_percent':float(quote[series]),
                        'annual_investment_rate':rate,'cash_factor':factor,'age_days':age})
    return pd.DataFrame(records)


def cash_replay(spy,original,schedule,multiplier,cost_bps):
    if schedule.Date.tolist()!=original.Date.tolist():raise ValueError('Rate/ledger alignment')
    market=spy.set_index('Date'); shares=0.; cash=1.; previous=1.; rows=[]
    for i,row in enumerate(original.itertuples(index=False)):
        price=market.loc[row.Date]; opening=float(price.Open); closing=float(price.Close)
        oldshares=shares; startcash=cash; factor=float(schedule.cash_factor.iloc[i])*multiplier
        income=startcash*factor; cash+=income
        dividend=oldshares*float(price.Dividends);cash+=dividend
        nav_open=shares*opening+cash
        if row.final_open_mark:
            cost=0.;traded=0.;nav_close=nav_open
        else:
            shares,cash,cost,traded=rebalance(shares,cash,opening,float(row.target_weight),cost_bps/10000)
            nav_close=shares*closing+cash
        actualweight=shares*opening/(shares*opening+cash)
        if not 0<=actualweight<=1+1e-12 or cash<-1e-12:raise ValueError('Unreported borrowing')
        record={'Date':row.Date,'signal_origin':row.signal_origin,'final_open_mark':bool(row.final_open_mark),
                'target_weight':float(row.target_weight),'opening_weight_after_trade':actualweight,
                'old_shares':oldshares,'shares':shares,'cash':cash,'dividend_cash':dividend,
                'nav_open_before_cost':nav_open,'trade_notional':traded,'turnover_nav':traded/nav_open,
                'cost':cost,'nav':nav_close,'return':nav_close/previous-1,
                'cash_balance_interval_start':startcash,'cash_interest':income,
                'cash_factor':factor,'elapsed_days':int(schedule.elapsed_days.iloc[i]),
                'rate_observation_date':schedule.observation_date.iloc[i],
                'rate_initial_release_date':schedule.initial_release_date.iloc[i]}
        rows.append(record);previous=nav_close
    return pd.DataFrame(rows)


def independently_audit(log,spy,schedule,series,multiplier,cost_bps):
    """Second arithmetic implementation, Decimal interest and explicit state checks."""
    market=spy.set_index('Date'); previous=1.;old_cash=1.;prior_shares=0.;priorclose=None;parts=[];errors=[]
    for i,row in enumerate(log.itertuples(index=False)):
        p=market.loc[row.Date]; opening=float(p.Open); closing=float(p.Close)
        with localcontext() as ctx:
            ctx.prec=40
            quote=Decimal(str(schedule.quote_percent.iloc[i]))/Decimal(100)
            annual=(quote if series=='DGS1MO' else (quote/Decimal(360))/(1-quote*Decimal(28)/Decimal(360))*Decimal(365))
            expected_interest=float(Decimal(str(old_cash))*annual*Decimal(str(multiplier))*Decimal(int(row.elapsed_days))/Decimal(365))
        dividend=prior_shares*float(p.Dividends)
        if row.final_open_mark:
            newq=prior_shares; newcash=old_cash+expected_interest+dividend; paid=traded=0.
        else:
            nav_before=prior_shares*opening+old_cash+expected_interest+dividend
            weight=row.target_weight; rate=cost_bps/10000
            oldvalue=prior_shares*opening
            # Algebraic post-cost NAV solve, independent of original rebalance helper.
            buying=weight*nav_before>=oldvalue
            postnav=((nav_before+rate*oldvalue)/(1+rate*weight) if buying
                     else (nav_before-rate*oldvalue)/(1-rate*weight))
            newq=weight*postnav/opening; newcash=(1-weight)*postnav
            traded=abs(newq-prior_shares)*opening;paid=rate*traded
        marked=opening if row.final_open_mark else closing
        nav=newq*marked+newcash
        overnight=0. if priorclose is None else prior_shares*(opening-priorclose)
        intraday=0. if row.final_open_mark else newq*(closing-opening)
        components=np.array([overnight,dividend,intraday,expected_interest,-paid])/previous
        errors.extend([abs(row.cash_interest-expected_interest),abs(row.dividend_cash-dividend),
                       abs(row.cash_balance_interval_start-old_cash),
                       abs(row.nav_open_before_cost-(prior_shares*opening+old_cash+expected_interest+dividend)),
                       abs(row.old_shares-prior_shares),abs(row.shares-newq),abs(row.cash-newcash),
                       abs(row.trade_notional-traded),abs(row.cost-paid),abs(row.nav-nav),
                       abs(float(log['return'].iloc[i])-components.sum())])
        if not row.final_open_mark and abs(row.opening_weight_after_trade-row.target_weight)>1e-12:raise ValueError('Exposure changed')
        parts.append(components);previous=float(row.nav);old_cash=float(row.cash);prior_shares=float(row.shares);priorclose=closing
    if max(errors)>2e-11:raise ValueError('Independent cash/share/return audit failed: '+str(max(errors)))
    return np.array(parts),{'max_absolute_accounting_error':max(errors),'rows':len(log)}


def attribution(cashlog,zerolog,cashparts,zeroparts):
    rc=cashlog['return'].to_numpy();rz=zerolog['return'].to_numpy();delta=rc-rz
    direct=cashparts[:,3];equity=(cashparts[:,:3]-zeroparts[:,:3]).sum(axis=1)
    fees=cashparts[:,4]-zeroparts[:,4]
    if not np.allclose(delta,direct+equity+fees,rtol=1e-10,atol=1e-13):raise ValueError('Delta return accounting')
    numerator=np.log1p(delta/(1+rz))
    factor=np.divide(numerator,delta,out=1/(1+rz),where=delta!=0)
    logparts=np.c_[direct,equity,fees]*factor[:,None]
    total=float(np.log1p(rc).sum()-np.log1p(rz).sum())
    residual=total-float(logparts.sum())
    if abs(residual)>1e-11:raise ValueError('Log-growth attribution failed')
    return {'incremental_log_growth':total,'direct_interest_log_contribution':float(logparts[:,0].sum()),
            'changed_equity_dividend_log_contribution':float(logparts[:,1].sum()),
            'changed_fee_log_contribution':float(logparts[:,2].sum()),'log_attribution_residual':residual},logparts


def fast_rolling(r):
    r=np.asarray(r,float); sums=np.r_[0,np.cumsum(r)]; squares=np.r_[0,np.cumsum(r*r)]
    variance=((squares[21:]-squares[:-21])-(sums[21:]-sums[:-21])**2/21)/20
    return np.sqrt(np.maximum(variance,0)*252)


def stream_statistics(r,rf,years):
    r=np.asarray(r,float); sd=r.std(ddof=1); excess=r-rf
    nav=np.exp(np.cumsum(np.log1p(r)));peaks=np.maximum.accumulate(np.r_[1.,nav])
    return np.array([np.expm1(np.log1p(r).sum()/years),sd*np.sqrt(252),
        np.sqrt(np.mean((fast_rolling(r)-.1)**2)),r.mean()/sd*np.sqrt(252),
        excess.mean()/excess.std(ddof=1)*np.sqrt(252),float(np.min(np.r_[1.,nav]/peaks-1))])


STAT_NAMES=['cagr','annual_vol','rolling21_target_rmse','sharpe_zero_reference','sharpe_excess_common_dgs1mo','max_drawdown']


def interval(v):return np.quantile(np.asarray(v),[.025,.975]).tolist()


def summarize(log,zero,common_rf,scenario_rf,logparts):
    metrics=portfolio_metrics(log);r=log['return'].to_numpy();prev=np.r_[1.,log.nav.to_numpy()[:-1]]
    years=(date.fromisoformat(log.Date.iloc[-1])-date.fromisoformat(log.Date.iloc[0])).days/365.25
    days=log.elapsed_days.to_numpy();fractions=np.r_[0.,1-log.opening_weight_after_trade.to_numpy()[:-1]]
    ex=r-common_rf; exown=r-scenario_rf
    income=log.cash_interest.to_numpy();norm=income/prev
    return {**metrics,'mean_cash_fraction_session':float(1-log.opening_weight_after_trade.mean()),
            'mean_cash_fraction_calendar_weighted':float(np.sum(fractions*days)/np.sum(days)),
            'cash_income_initial_nav':float(income.sum()),'cash_income_initial_nav_per_year':float(income.sum()/years),
            'normalized_cash_income_sum':float(norm.sum()),'annual_normalized_cash_income':float(norm.sum()/years),
            'cash_income_cagr_increment':metrics['cagr']-portfolio_metrics(zero)['cagr'],
            'sharpe_excess_common_dgs1mo':float(ex.mean()/ex.std(ddof=1)*np.sqrt(252)),
            'sharpe_excess_scenario_cash':float(exown.mean()/exown.std(ddof=1)*np.sqrt(252))}


def bootstrap(logs,common_rf):
    """Paired streams, frozen rate path, all fixed contrasts and ranking frequencies."""
    n=len(common_rf);years=(date.fromisoformat(logs['zero','combined',5].Date.iloc[-1])-date.fromisoformat(logs['zero','combined',5].Date.iloc[0])).days/365.25
    estimates={key:stream_statistics(log['return'].to_numpy(),common_rf,years) for key,log in logs.items()}
    contrasts=[];ranks=[]
    for block in [21,63,126]:
        rng=np.random.default_rng(1729);draws={key:[] for key in logs}
        for iteration in range(1000):
            idx=block_indices(n,rng,block);rf=common_rf[idx]
            for key,log in logs.items():draws[key].append(stream_statistics(log['return'].to_numpy()[idx],rf,years))
        draws={key:np.array(v) for key,v in draws.items()}
        for scenario in SCENARIOS[1:]:
            for model in MODELS:
                for cost in COSTS:
                    key=(scenario,model,cost);ref=('zero',model,cost)
                    for j,metric in enumerate(STAT_NAMES):
                        contrasts.append({'block':block,'comparison':'cash_minus_zero','scenario':scenario,
                            'candidate':model,'baseline':model,'cost_bps':cost,'metric':metric,
                            'estimate':float(estimates[key][j]-estimates[ref][j]),'ci95':interval(draws[key][:,j]-draws[ref][:,j])})
        for scenario in SCENARIOS:
            for a_i,a in enumerate(MODELS):
                for b in MODELS[a_i+1:]:
                    key=(scenario,a,5);ref=(scenario,b,5)
                    for j,metric in enumerate(STAT_NAMES):
                        contrasts.append({'block':block,'comparison':'strategy_pair','scenario':scenario,
                            'candidate':a,'baseline':b,'cost_bps':5,'metric':metric,
                            'estimate':float(estimates[key][j]-estimates[ref][j]),'ci95':interval(draws[key][:,j]-draws[ref][:,j])})
            for j,metric in enumerate(STAT_NAMES[:5]):
                matrix=np.column_stack([draws[scenario,m,5][:,j] for m in MODELS])
                lower=metric=='rolling21_target_rmse'
                if metric=='annual_vol':matrix=abs(matrix-.1);lower=True
                order=np.argsort(matrix if lower else -matrix,axis=1,kind='stable')
                for model_index,model in enumerate(MODELS):
                    ranks.append({'block':block,'scenario':scenario,'model':model,'metric':metric,
                                  'bootstrap_best_frequency':float(np.mean(order[:,0]==model_index)),
                                  'bootstrap_mean_rank':float(np.mean(np.argmax(order==model_index,axis=1)+1))})
        print('Completed paired uncertainty block',block,flush=True)
    return contrasts,ranks


def execute():
    code=implementation(['src/vrp/cash_yield.py','scripts/run_h8_cash_yield.py','paper/h8_cash_yield_plan.md'])
    before=prior_evidence();_,signals,meta,spy,source,originals=load_inputs()
    pointer=ROOT/'data/manifests/h8_cash_rate_source_v1.json'
    sources=json.loads(pointer.read_bytes()); schedules={}
    for record in sources['downloads']:checked_hash(ROOT/record['path'],record['sha256'])
    dates=originals['combined',5].Date.tolist()
    for model in MODELS:
        expected=np.ones(len(signals)) if model=='buyhold' else np.clip(.1/np.sqrt(signals[model].to_numpy()),0,1)
        for cost in COSTS:
            if not np.array_equal(originals[model,cost].target_weight.to_numpy(),expected):raise ValueError('Original target exposure mismatch')
    for identifier in ['DGS1MO','DTB4WK']:
        info=sources['series'][identifier];checked_hash(ROOT/info['initial_path'],info['initial_sha256'])
        frame=pd.read_csv(ROOT/info['initial_path'],float_precision='round_trip')
        schedules[identifier]=rate_schedule(frame,dates,identifier)
    common_rf=schedules['DGS1MO'].cash_factor.to_numpy()
    logs={};parts={};rows=[];audits={};loghashes={};attributions=[];periods=[];zero_exact=[]
    for scenario in SCENARIOS:
        identifier='DTB4WK' if scenario=='dtb4wk_full' else 'DGS1MO'
        multiplier={'zero':0.,'dgs1mo_full':1.,'dgs1mo_half':.5,'dtb4wk_full':1.}[scenario]
        schedule=schedules[identifier]
        for model in MODELS:
            for cost in COSTS:
                zero=originals[model,cost]
                log=cash_replay(spy,zero,schedule,multiplier,cost)
                if scenario=='zero':
                    if not log[zero.columns].equals(zero):raise ValueError('Zero-interest original ledger differs')
                    raw=log[zero.columns].to_csv(index=False,float_format='%.17g',lineterminator='\n').encode()
                    import hashlib
                    if hashlib.sha256(raw).hexdigest()!=meta['h8']['log_sha256'][f'h8_{model}_{cost}bps.csv']:raise ValueError('Zero-interest CSV bytes differ')
                    zero_exact.append(f'{model}_{cost}')
                component,audit=independently_audit(log,spy,schedule,identifier,multiplier,cost)
                key=(scenario,model,cost);logs[key]=log;parts[key]=component;audits['_'.join(map(str,key))]=audit
                attribution_row,lp=attribution(log,zero,component,parts['zero',model,cost])
                attribution_row.update({'scenario':scenario,'strategy':model,'cost_bps':cost});attributions.append(attribution_row)
                summary=summarize(log,zero,common_rf,schedule.cash_factor.to_numpy()*multiplier,lp)
                original_metrics=meta['h8']['models'][str(cost)][model]
                if scenario=='zero' and any(summary[k]!=v for k,v in original_metrics.items()):raise ValueError('Zero-interest metrics differ')
                summary.update({'scenario':scenario,'strategy':model,'cost_bps':cost});rows.append(summary)
                loghashes[f'{scenario}_{model}_{cost}bps.csv']=csv_immutable(OUT/f'{scenario}_{model}_{cost}bps.csv',log)
                if cost==5:
                    csv_immutable(OUT/f'{scenario}_{model}_daily_attribution.csv',pd.DataFrame({'Date':log.Date,
                                  'direct_interest_log':lp[:,0],'changed_equity_dividend_log':lp[:,1],'changed_fee_log':lp[:,2]}))
                    for period,(lo,hi) in PERIODS.items():
                        mask=log.signal_origin.between(lo,hi).to_numpy();sub=log[mask].copy()
                        sub['nav']=np.cumprod(1+sub['return'].to_numpy());metric=portfolio_metrics(sub)
                        periods.append({'scenario':scenario,'strategy':model,'period':period,**metric,
                                        'cash_income_initial_nav':float(log.cash_interest[mask].sum())})
        print('Completed ledger scenario',scenario,flush=True)
    # Gross/net cost effects remain distinct from total fee dollars.
    for row in rows:
        gross=logs[row['scenario'],row['strategy'],0]; net=logs[row['scenario'],row['strategy'],row['cost_bps']]
        row['gross_minus_net_cagr']=portfolio_metrics(gross)['cagr']-row['cagr']
        row['gross_minus_net_log_growth']=float(np.log1p(gross['return']).sum()-np.log1p(net['return']).sum())
    contrasts,ranks=bootstrap(logs,common_rf)
    for name,digest in before.items():checked_hash(ROOT/name,digest)
    result={'status':STATUS,'implementation':code,'registration_commit':'669af87','clarification_commit':'f952067',
        'rate_source_manifest_sha256':sha(pointer),'rates':sources,'spy_sha256':source['sha256'],
        'common_origins':len(signals),'models_refitted':0,'n_original_zero_ledgers_exact':len(zero_exact),
        'input_sha256':before,'summary':rows,'periods_5bps':periods,'attributions':attributions,
        'accounting_audit':audits,'uncertainty':contrasts,'ranking_uncertainty':ranks,'ledger_sha256':loghashes,
        'accrual':'Prior-opening cash times initial-release-known locked annual rate times actual calendar days /365; credited next open before dividends/trade.',
        'sharpe_reference':'Original zero reference preserved; common DGS1MO excess and separate scenario-rate excess also shown.',
        'bootstrap':{'blocks':[21,63,126],'draws':1000,'seed':1729,'paired_all_return_rate_streams':True},
        'limitations':'Treasury yield proxy cash account, not actual securities total return or guaranteed broker payment; exploratory historical uncertainty only.'}
    hashes={}
    for name,records in [('summary',rows),('periods',periods),('attribution',attributions),('uncertainty',contrasts),('ranking_uncertainty',ranks)]:
        frame=pd.DataFrame(records)
        for col in frame:
            if frame[col].map(lambda v:isinstance(v,list)).any():frame[col]=frame[col].map(lambda v:json.dumps(v) if isinstance(v,list) else v)
        hashes[name+'.csv']=csv_immutable(OUT/(name+'.csv'),frame)
    for identifier,schedule in schedules.items():hashes[identifier+'_schedule.csv']=csv_immutable(OUT/(identifier+'_schedule.csv'),schedule)
    result['table_sha256']=hashes
    persist(OUT/'results.json',result);persist(ROOT/'data/manifests/h8_cash_results_v1.json',result)
    print('Complete cash-yield results SHA '+sha(OUT/'results.json'),flush=True)
    return result
