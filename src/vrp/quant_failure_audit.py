"""Independent score checks, fixed uncertainty, and instrument/timing bridge."""
import json
import math
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
from vrp.quant_failure import (OUT, ROOT, load_inputs, partitions, bootstrap_counts,
    interval, projection, constraint_bridge, ledger_components)
from vrp.quant_extension import sha, checked_hash, persist, csv_immutable, implementation, block_indices
from vrp.quant_portfolio import rolling_volatility


def weighted_rank(y,p,weights):
    """Tie-aware ROC pair probability and stepwise PR area, independently coded."""
    y=np.asarray(y); p=np.asarray(p); weights=np.asarray(weights,float)
    order=np.argsort(-p,kind='stable'); yy=y[order]; ww=weights[order]; pp=p[order]
    ends=np.r_[np.flatnonzero(np.diff(pp)!=0),len(pp)-1]
    tp=np.cumsum(ww*yy)[ends]; fp=np.cumsum(ww*(1-yy))[ends]
    if not len(tp) or tp[-1]<=0: return np.array([np.nan,np.nan])
    tpr=np.r_[0,tp/tp[-1]]
    roc=float(np.trapezoid(tpr,np.r_[0,fp/fp[-1]])) if fp[-1]>0 else np.nan
    denom=tp+fp
    precision=np.divide(tp,denom,out=np.zeros_like(tp),where=denom>0)
    ap=float(np.sum(np.diff(tpr)*precision))
    return np.array([roc,ap])


def weighted_projection_draws(y,f,mask,counts):
    c=counts[:,mask]; actual=y[mask]; forecast=f[mask]; n=c.sum(axis=1)
    with np.errstate(divide='ignore',invalid='ignore'):
        mf=(c@forecast)/n; my=(c@actual)/n
        cov=(c@(forecast*actual))/n-mf*my
        var=(c@(forecast*forecast))/n-mf*mf
        b=np.where(var>1e-20,cov/var,np.nan); a=my-b*mf
    return interval(a),interval(b)


def score_uncertainty(h6,panel,masks,counts):
    ranks=[]; calibration=[]; y=h6.y.to_numpy()
    for g,mask in masks.items():
        if not mask.any(): continue
        c=counts[:,mask]
        for m in 'ABCD':
            p=h6[m].to_numpy()[mask]; actual=y[mask]; base=weighted_rank(actual,p,np.ones(len(p)))
            if 0<actual.sum()<len(actual):
                check=[roc_auc_score(actual,p),average_precision_score(actual,p)]
                if not np.allclose(base,check,atol=1e-12): raise ValueError('Independent ROC/AP mismatch')
            draws=np.array([weighted_rank(actual,p,w) for w in c])
            for j,metric in enumerate(['roc_auc','average_precision']):
                ranks.append({'group':g,'model':m,'metric':metric,'estimate':float(base[j]) if np.isfinite(base[j]) else None,**interval(draws[:,j])})
            with np.errstate(divide='ignore',invalid='ignore'):
                diff=(c@(p-actual))/c.sum(axis=1)
            calibration.append({'group':g,'model':m,'diagnostic':'mean_probability_minus_prevalence',
                'estimate':float((p-actual).mean()),**interval(diff)})
        for m in ['vix','garch','trailing','ewma','har','combined']:
            a,b=weighted_projection_draws(panel.y.to_numpy(),panel[m].to_numpy(),mask,counts)
            diagnostic,_,_=projection(panel.y.to_numpy()[mask],panel[m].to_numpy()[mask])
            for key,ci in [('intercept',a),('slope',b)]:
                calibration.append({'group':g,'model':m,'diagnostic':'variance_'+key,'estimate':diagnostic[key],**ci})
    return {'ranking':ranks,'calibration':calibration}


def split_bridge(panel,spy,logs):
    market=spy.set_index('Date'); cc=((market.Close+market.Dividends)/market.Close.shift(1)-1)
    # Actual observed forward sessions ONLY for realized diagnostic targets.
    spy_targets=[]
    for origin in panel.origin:
        end=(pd.Timestamp(origin)+pd.Timedelta(days=30)).strftime('%Y-%m-%d')
        sub=cc.loc[(cc.index>origin)&(cc.index<=end)]
        if not len(sub) or not np.isfinite(sub).all(): raise ValueError('SPY realized horizon support')
        spy_targets.append(float(np.sum(sub.to_numpy()**2)*365/30))
    spy_targets=np.array(spy_targets); bridges=[]; daily=[]
    for m in ['vix','garch','trailing','combined']:
        log=logs[m,0]; net=logs[m,5]; f=panel[m].to_numpy(); y=panel.y.to_numpy()
        w,_,cap,total=constraint_bridge(y,f); _,cal,u=projection(y,f)
        dates=log.Date.tolist(); opens=market.loc[dates,'Open'].to_numpy(); closes=market.loc[dates,'Close'].to_numpy(); div=market.loc[dates,'Dividends'].to_numpy()
        startprice=np.r_[opens[0],closes[:-1]]; endprice=closes.copy(); endprice[-1]=opens[-1]
        # Pure accounting proxy at saved weight; not a simulated investable strategy.
        pure=(endprice+div)/startprice-1; pure[0]=(endprice[0]/startprice[0]-1)
        effective=log.opening_weight_after_trade.to_numpy(); ideal=effective*pure
        actual=log['return'].to_numpy(); timing=actual-ideal
        vi=float(np.var(ideal,ddof=1)*252); vg=float(np.var(actual,ddof=1)*252); vn=float(np.var(net['return'],ddof=1)*252)
        instrument=float(np.mean((w*w*(spy_targets-y))[:-1]))
        spyproxy=float(np.mean((w*w*spy_targets)[:-1]))
        horizon=float(vi-spyproxy); trade=float(vg-vi); cost=float(vn-vg)
        components={'calibration':float(np.mean((w*w*cal)[:-1])),
                    'forecast_residual':float(np.mean((w*w*u)[:-1])),
                    'constraint':float(cap[:-1].mean()),
                    'instrument_return_convention':instrument,
                    'horizon_dynamic_exposure_mean_sample_bridge':horizon,
                    'implementation_trade_timing_dividend_bridge':trade,
                    'transaction_cost_variance_effect':cost}
        residual=vn-.01-sum(components.values())
        if abs(residual)>1e-13: raise ValueError('Disaggregated bridge failed')
        cov=float(np.cov(ideal,timing,ddof=1)[0,1]*252*2); timingvar=float(np.var(timing,ddof=1)*252)
        if abs(trade-cov-timingvar)>1e-13: raise ValueError('Trade timing covariance failed')
        bridges.append({'strategy':m,'variance_minus_target':float(vn-.01),**components,
                        'arithmetic_residual':float(residual),'timing_variance':timingvar,'timing_cross_covariance':cov})
        daily.extend({'origin':o,'Date':d,'strategy':m,'pure_weighted_cc_return':float(i),
                      'implementation_return_residual':float(t),'spy_forward_simple_variance':float(s)}
                     for o,d,i,t,s in zip(panel.origin,dates,ideal,timing,spy_targets))
    return {'bridge':bridges,'daily_bridge':daily}


def portfolio_uncertainty(panel,logs,masks):
    groups=[]; comparisons=[]; n=len(panel); y=panel.y.to_numpy()
    for block in [21,63,126]:
        counts=bootstrap_counts(n,block)
        for m in ['buyhold','trailing','vix','garch','combined']:
            log=logs[m,5]; r=log['return'].to_numpy(); rv=rolling_volatility(r)
            w=log.opening_weight_after_trade.to_numpy()
            for g,mask in masks.items():
                if not mask.any(): continue
                c=counts[:,mask]; nn=c.sum(axis=1)
                with np.errstate(divide='ignore',invalid='ignore'):
                    mean=(c@r[mask])/nn; second=(c@(r[mask]**2))/nn
                    vol=np.sqrt(np.maximum((second-mean**2)*nn/(nn-1),0)*252)
                    mw=(c@w[mask])/nn
                for metric,estimate,draws in [('annual_vol',float(np.std(r[mask],ddof=1)*np.sqrt(252)),vol),
                                               ('mean_weight',float(w[mask].mean()),mw)]:
                    groups.append({'block':block,'group':g,'strategy':m,'metric':metric,'estimate':estimate,**interval(draws)})
                valid=mask&np.isfinite(rv); vcounts=counts[:,valid]; den=vcounts.sum(axis=1)
                with np.errstate(divide='ignore',invalid='ignore'):
                    tracking=np.sqrt((vcounts@((rv[valid]-.1)**2))/den)
                groups.append({'block':block,'group':g,'strategy':m,'metric':'conditional_observed_rolling_tracking_rmse',
                    'estimate':float(np.sqrt(np.mean((rv[valid]-.1)**2))) if valid.any() else None,**interval(tracking)})
                if m!='buyhold':
                    f=panel[m].to_numpy(); _,error,cap,total=constraint_bridge(y,f)
                    earned=mask.copy(); earned[-1]=False; ec=counts[:,earned]; en=ec.sum(axis=1)
                    for metric,x in [('cap_fraction',(f<=.01).astype(float)),('cap_constraint_variance',cap),
                                     ('weighted_forecast_error',error)]:
                        with np.errstate(divide='ignore',invalid='ignore'): draws=(ec@x[earned])/en
                        groups.append({'block':block,'group':g,'strategy':m,'metric':metric,
                                      'estimate':float(x[earned].mean()) if earned.any() else None,**interval(draws)})
        # Full paired return resamples recompute rolling windows, exactly as original H8.
        rng=np.random.default_rng(1729); a=logs['combined',5]['return'].to_numpy(); b=logs['trailing',5]['return'].to_numpy()
        years=(pd.Timestamp(logs['combined',5].Date.iloc[-1])-pd.Timestamp(logs['combined',5].Date.iloc[0])).days/365.25
        def stats(r):
            return np.array([np.sqrt(np.mean((rolling_volatility(r)[20:]-.1)**2)),np.std(r,ddof=1)*np.sqrt(252),np.expm1(np.log1p(r).sum()/years)])
        draws=np.array([stats(a[idx])-stats(b[idx]) for idx in (block_indices(n,rng,block) for _ in range(1000))])
        estimate=stats(a)-stats(b)
        for j,key in enumerate(['rolling_tracking_rmse','annual_vol','cagr']):
            comparisons.append({'block':block,'metric':key,'estimate':float(estimate[j]),**interval(draws[:,j])})
    return {'groups':groups,'paired_combined_minus_trailing':comparisons}


def execute_audit():
    code=implementation(['src/vrp/quant_failure_audit.py','src/vrp/quant_failure.py','scripts/run_quant_failure_audit.py'])
    result=json.loads((OUT/'results.json').read_bytes())
    for name,digest in result['input_sha256'].items(): checked_hash(ROOT/name,digest)
    h6,panel,meta,spy,_,logs=load_inputs(); masks=partitions(panel)
    print('Independent score and rank crosschecks',flush=True)
    max_error=0.
    for m in 'ABCD':
        p=h6[m].to_numpy(); y=h6.y.to_numpy(); independent=math.fsum(float((a-b)**2) for a,b in zip(y,p))/len(y)
        max_error=max(max_error,abs(independent-meta['h6']['models'][m]['brier']))
        if max_error>1e-12: raise ValueError('Original H6 score changed')
    for m in ['vix','garch','trailing','ewma','har','combined']:
        f=panel[m].to_numpy(); y=panel.y.to_numpy()
        q=math.fsum(float(a/b-math.log(a/b)-1) for a,b in zip(y,f))/len(y)
        rmse=math.sqrt(math.fsum(float((a-b)**2) for a,b in zip(y,f))/len(y))
        if abs(q-meta['h7']['models'][m]['qlike'])>1e-12 or abs(rmse-meta['h7']['models'][m]['rmse'])>1e-12: raise ValueError('Original H7 score changed')
    a=score_uncertainty(h6,panel,masks,bootstrap_counts(len(panel),63))
    print('Disaggregated instrument/horizon/implementation bridge',flush=True)
    b=split_bridge(panel,spy,logs)
    print('Portfolio uncertainty and block sensitivities',flush=True)
    c=portfolio_uncertainty(panel,logs,masks)
    for name,digest in result['input_sha256'].items(): checked_hash(ROOT/name,digest)
    audit={'implementation':code,'primary_results_sha256':sha(OUT/'results.json'),
           'independent_brier_max_error':max_error,'original_models_unchanged':True,
           'score_uncertainty':a,'split_bridge':b,'portfolio_uncertainty':c,
           'uncertainty_scope':'Block-resampled historical distributions; conditional observed rolling-window subgroup intervals preserve original window losses; full paired rolling intervals recompute windows.'}
    hashes={}
    for prefix,sections in [('score',a),('split',b),('portfolio',c)]:
        for section,records in sections.items(): hashes[f'{prefix}_{section}.csv']=csv_immutable(OUT/f'{prefix}_{section}.csv',pd.DataFrame(records))
    audit['table_sha256']=hashes
    persist(OUT/'independent_audit.json',audit)
    persist(ROOT/'data/manifests/quant_failure_independent_audit_v1.json',audit)
    print('Complete audit SHA '+sha(OUT/'independent_audit.json'),flush=True)
    return audit
