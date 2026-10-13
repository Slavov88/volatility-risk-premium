"""Frozen exploratory diagnostics; no model fitting or strategy changes."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
from vrp.quant_extension import (ROOT, OUT as INPUT, sha, checked_hash, persist,
    csv_immutable, implementation, block_indices, budget_alerts, alert_metrics)
from vrp.quant_portfolio import acquire_spy, rolling_volatility, portfolio_metrics

OUT = ROOT / 'outputs/quant_failure_diagnostics/v1'
STATUS = 'EXPLORATORY DIAGNOSTICS — PENDING INDEPENDENT COAUTHOR REVIEW'
MODELS = ['vix', 'garch', 'trailing', 'ewma', 'har', 'combined']


def frozen_inputs():
    """Hash all prior evidence and data, including Task1, without modifying it."""
    paths = []
    for folder in ['outputs/quant_extension/v2', 'outputs/empirical_calendar_repair/v1',
                   'outputs/empirical_h1_h5/v1', 'data/manifests', 'data/processed/interim']:
        paths += [p for p in (ROOT/folder).rglob('*') if p.is_file()
                  and not p.name.startswith('quant_failure_')]
    for name in ['quant_extension_protocol.md', 'quant_extension_calendar_amendment.md']:
        paths.append(ROOT/'paper'/name)
    for name in ['quant_extension_summary.md', 'h6_tail_risk_results.md',
                 'h7_variance_forecasting_results.md', 'h8_portfolio_economic_value.md',
                 'h3_h4_calendar_correction.md', 'h3_h4_corrected_results.md',
                 'empirical_calendar_impact.md', 'empirical_results_summary_calendar_v1.md']:
        paths.append(ROOT/'docs'/name)
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths))}


def load_inputs():
    meta = {h: json.loads((INPUT/f'{h}.json').read_bytes()) for h in ['h6', 'h7', 'h8']}
    for h, expected in [('h6','2a8107e9ace5dcfd565bbdba59bf7f298906584d3050565806f129072b4715c9'),
                        ('h7','cec3e911eaef7f4d27d8395ba8316f807a910b82601a79bcfe29a8f636001d68'),
                        ('h8','b09b8f3ffdd8af230854709e39771efb0e73f8c9b5afb9c5b33607e04183f001')]:
        checked_hash(INPUT/f'{h}.json', expected)
    for h in ['h6','h7']:
        checked_hash(INPUT/f'{h}_forecasts.csv', meta[h]['forecasts_sha256'])
    for name, digest in meta['h8']['log_sha256'].items():
        checked_hash(INPUT/name, digest)
    h6 = pd.read_csv(INPUT/'h6_forecasts.csv', float_precision='round_trip')
    h7 = pd.read_csv(INPUT/'h7_forecasts.csv', float_precision='round_trip')
    if len(h6) != 3520 or h6.origin.tolist() != h7.origin.tolist():
        raise ValueError('Common origin mismatch')
    target = ROOT/'data/processed/interim/40113d6646b0e7b8/targets/bd7a172882ded86f/six_forward_targets.csv'
    checked_hash(target, 'cdd63f219d61584c8f3fa15e8f80c23ef351a6e902cb93027eed9b5e79dba3a5')
    daily = pd.read_csv(target, float_precision='round_trip')
    # Shift on complete observed historical sessions BEFORE narrowing evaluation.
    daily['vix_change5'] = daily.vix_close / daily.vix_close.shift(5) - 1
    panel = h7.merge(daily[['origin','vix_close','vix_change5','ivar','rvar_cc_fwd_30c']],
                     on='origin', validate='one_to_one')
    if not np.array_equal(panel.y, panel.rvar_cc_fwd_30c) or not np.array_equal(panel.vix, panel.ivar):
        raise ValueError('Target/IVAR mismatch')
    if not np.array_equal(h6.y, (panel.y > 1.5*panel.vix).astype(int)):
        raise ValueError('Event mismatch')
    for h in ['h6','h7']:
        fits = meta[h]['fits']
        if len(fits) != 168 or any(f['latest_maturity'][:10] > f['as_of'] for f in fits):
            raise ValueError('Refit maturity mismatch')
        known = {f['as_of'] for f in fits}
        if not set(h6.as_of_fit if h=='h6' else h7.as_of_fit).issubset(known):
            raise ValueError('Unknown fit')
    if not (ROOT/'data/manifests/quant_extension_spy.json').exists():
        raise ValueError('Missing frozen SPY source; acquisition is not authorized by this plan')
    spy, source = acquire_spy()  # Existing pointer required; never acquire new data here.
    logs = {(m,c): pd.read_csv(INPUT/f'h8_{m}_{c}bps.csv', float_precision='round_trip')
            for m in ['buyhold','trailing','vix','garch','combined'] for c in [0,1,5,10,25]}
    return h6, panel, meta, spy, source, logs


def partitions(panel):
    d = panel.origin.to_numpy(str); v = panel.vix_close.to_numpy(float)
    z = panel.vix_change5.to_numpy(float); n = len(d)
    masks = {'full': np.ones(n, bool)}
    for year in range(2012,2026):
        masks[f'year_{year}'] = np.char.startswith(d,str(year))
    for name,lo,hi in [('2012_2016','2012-01-01','2016-12-31'),
                        ('2017_2021','2017-01-01','2021-12-31'),
                        ('2022_2025','2022-01-01','2025-12-31'),
                        ('2020_pre','2020-01-01','2020-02-18'),
                        ('2020_onset','2020-02-19','2020-03-23'),
                        ('2020_normalize','2020-03-24','2020-06-30'),
                        ('2020_late','2020-07-01','2020-12-31')]:
        masks[name] = (d>=lo)&(d<=hi)
    masks.update({'vix_low':v<15, 'vix_mid':(v>=15)&(v<25), 'vix_high':v>=25,
                  'shock_down':z<=-.2, 'shock_stable':(z>-.2)&(z<.2), 'shock_up':z>=.2})
    ratio = panel.y.to_numpy()/panel.vix.to_numpy()
    masks.update({'outcome_ratio_le1':ratio<=1,'outcome_ratio_1_1.5':(ratio>1)&(ratio<=1.5),
                  'outcome_ratio_1.5_3':(ratio>1.5)&(ratio<=3), 'outcome_ratio_gt3':ratio>3})
    change = panel.y.to_numpy()/panel.trailing.to_numpy()
    masks.update({'outcome_variance_down':change<=.5,
                  'outcome_variance_stable':(change>.5)&(change<2), 'outcome_variance_up':change>=2})
    return masks


def brier_decomposition(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float); n=len(y)
    if not n: return None
    prevalence=float(y.mean()); rel=res=0.; bins=[]; binned=np.empty(n)
    ids=np.minimum((p*10).astype(int),9)
    for j in range(10):
        mask=ids==j; k=int(mask.sum())
        if k:
            meanp=float(p[mask].mean()); rate=float(y[mask].mean()); binned[mask]=meanp
            rel+=k/n*(meanp-rate)**2; res+=k/n*(rate-prevalence)**2
        else: meanp=rate=None
        bins.append({'lower':j/10,'n':k,'predicted':meanp,'observed':rate})
    unc=prevalence*(1-prevalence); score=float(np.mean((p-y)**2))
    within=float(np.mean((p-y)**2-(binned-y)**2))
    event=float(np.mean(y*(1-p)**2)); nonevent=float(np.mean((1-y)*p**2))
    if abs(score-(rel-res+unc+within))>1e-12 or abs(score-event-nonevent)>1e-12:
        raise ValueError('Brier identity failed')
    return {'brier':score,'event_contribution':event,'nonevent_contribution':nonevent,
            'reliability':rel,'resolution':res,'uncertainty':unc,'within_bin_residual':within,'bins':bins}


def projection(y,f):
    """Descriptive OOS least-squares diagnostic; never an executable forecast."""
    y=np.asarray(y,float); f=np.asarray(f,float)
    X=np.c_[np.ones(len(f)),f]; coeff=np.linalg.lstsq(X,y,rcond=None)[0]
    cal=X@coeff-f; u=y-X@coeff; e=y-f
    pieces={'calibration_mse':float(np.mean(cal**2)), 'residual_mse':float(np.mean(u**2)),
            'cross_term':float(2*np.mean(cal*u))}
    mse=float(np.mean(e**2)); bias=float(e.mean()); centered=float(np.var(e))
    slope=float(np.cov(f,y,ddof=0)[0,1]/np.var(f)) if np.var(f)>0 else 0.
    intercept=float(y.mean()-slope*f.mean())
    if np.var(f)>1e-20 and not np.allclose(coeff,[intercept,slope],rtol=1e-9,atol=1e-10):
        raise ValueError('Independent calibration moment crosscheck failed')
    if abs(mse-sum(pieces.values()))>1e-12 or abs(mse-bias**2-centered)>1e-12:
        raise ValueError('MSE identity failed')
    return {'intercept':float(coeff[0]),'slope':float(coeff[1]),'mse':mse,
            'bias_actual_minus_forecast':bias,'bias_squared':bias**2,
            'centered_error_variance':centered,**pieces}, cal, u


def constraint_bridge(y,f):
    y=np.asarray(y,float); f=np.asarray(f,float)
    if np.any(f<=0): raise ValueError('Nonpositive forecast')
    w=np.minimum(.1/np.sqrt(f),1.)
    forecast=w*w*(y-f); constraint=w*w*f-.01; total=w*w*y-.01
    if not np.allclose(total,forecast+constraint,rtol=1e-12,atol=1e-15):
        raise ValueError('Variance proxy identity failed')
    return w,forecast,constraint,total


def ledger_components(log,spy):
    """Independent value/return accounting from saved shares and raw prices."""
    market=spy.set_index('Date'); n=len(log); previous=np.r_[1.,log.nav.to_numpy()[:-1]]
    dates=log.Date.tolist(); opens=market.loc[dates,'Open'].to_numpy()
    closes=market.loc[dates,'Close'].to_numpy(); dividends=market.loc[dates,'Dividends'].to_numpy()
    # First return begins with cash at opening, so no overnight price exposure.
    prior_close=np.r_[opens[0],closes[:-1]]
    old=log.old_shares.to_numpy(); new=log.shares.to_numpy()
    final=log.final_open_mark.to_numpy(bool)
    parts=np.c_[old*(opens-prior_close),old*dividends,
                np.where(final,0.,new*(closes-opens)),-log.cost.to_numpy()]/previous[:,None]
    error=np.max(np.abs(parts.sum(axis=1)-log['return'].to_numpy()))
    if error>2e-12: raise ValueError('Return accounting failed')
    expected_nav=new*np.where(final,opens,closes)+log.cash.to_numpy()
    old_cash=np.r_[1.,log.cash.to_numpy()[:-1]]
    expected_cash=old_cash+old*dividends-(new-old)*opens-log.cost.to_numpy()
    err=max(float(error),float(np.max(abs(expected_nav-log.nav))),
            float(np.max(abs(expected_cash-log.cash))),float(np.max(abs(old*dividends-log.dividend_cash))))
    if err>2e-11: raise ValueError('Share/cash recurrence failed')
    # Cost rate implied by nonzero trades checked by caller for each scenario.
    return parts,err


def bootstrap_counts(n,block):
    rng=np.random.default_rng(1729)
    return np.asarray([np.bincount(block_indices(n,rng,block),minlength=n) for _ in range(1000)],float)


def interval(values):
    x=np.asarray(values,float); x=x[np.isfinite(x)]
    return {'ci95':np.quantile(x,[.025,.975]).tolist() if len(x) else None,'valid_draws':len(x)}


def mean_intervals(matrix,masks,counts):
    """Full-chronology resampling followed by subgroup selection."""
    matrix=np.asarray(matrix,float); ans={}
    for group,mask in masks.items():
        denominator=counts[:,mask].sum(axis=1)
        with np.errstate(divide='ignore',invalid='ignore'):
            estimates=(counts[:,mask]@matrix[mask])/denominator[:,None]
        ans[group]=[interval(estimates[:,j]) for j in range(matrix.shape[1])]
    return ans


def h6_analysis(h6,panel,masks,counts):
    y=h6.y.to_numpy(float); columns={}; rows=[]; bins=[]; alerts=[]; contrasts=[]
    for m in 'ABCD':
        p=h6[m].to_numpy(); live=p>=h6[f'{m}_alert_threshold'].to_numpy()
        columns.update({f'{m}_brier':(p-y)**2,f'{m}_probability':p,
                        f'{m}_event_loss':y*(1-p)**2,f'{m}_nonevent_loss':(1-y)*p*p,
                        f'{m}_live_alert':live.astype(float),f'{m}_live_tp':live*y,
                        f'{m}_live_fn':(~live)*y})
    columns['prevalence']=y
    for c,b in [('C','A'),('C','B'),('D','A'),('D','B')]:
        columns[f'{c}_minus_{b}']=columns[f'{c}_brier']-columns[f'{b}_brier']
    names=list(columns); matrix=np.column_stack(list(columns.values()))
    cis=mean_intervals(matrix,masks,counts)
    for g,mask in masks.items():
        k=int(mask.sum()); suby=y[mask]
        if not k:
            rows.append({'group':g,'model':None,'n':0}); continue
        for m in 'ABCD':
            p=h6[m].to_numpy()[mask]; dec=brier_decomposition(suby,p)
            row={'group':g,'model':m,'n':k,'events':int(suby.sum()),'prevalence':float(suby.mean()),
                 'mean_probability':float(p.mean()),'log_loss':float(np.mean(-suby*np.log(np.clip(p,1e-6,1-1e-6))-(1-suby)*np.log(np.clip(1-p,1e-6,1)))),
                 'roc_auc':float(roc_auc_score(suby,p)) if 0<suby.sum()<k else None,
                 'average_precision':float(average_precision_score(suby,p)) if suby.sum() else None,
                 **{key:val for key,val in dec.items() if key!='bins'}}
            for stat in ['brier','probability','event_loss','nonevent_loss','live_alert','live_tp','live_fn']:
                ci=cis[g][names.index(f'{m}_{stat}')]; row[stat+'_ci_low']=ci['ci95'][0] if ci['ci95'] else None; row[stat+'_ci_high']=ci['ci95'][1] if ci['ci95'] else None
            pc=cis[g][names.index('prevalence')]['ci95']; row['prevalence_ci_low'],row['prevalence_ci_high']=pc
            rows.append(row)
            bins.extend({'group':g,'model':m,**b} for b in dec['bins'])
            for policy,alert in [('retrospective_group_budget',budget_alerts(p)),
                                 ('saved_train_quantile',p>=h6[f'{m}_alert_threshold'].to_numpy()[mask])]:
                stats=alert_metrics(suby,alert); global_alert=(h6[m].to_numpy()>=h6[f'{m}_alert_threshold'].to_numpy()) if policy=='saved_train_quantile' else None
                draws=[]
                if global_alert is not None:
                    denom=counts[:,mask]@y[mask]
                    with np.errstate(divide='ignore',invalid='ignore'):
                        draws=(counts[:,mask]@(y[mask]*global_alert[mask]))/denom
                else:
                    # Replicates preserve chronology before subgroup re-ranking.
                    for c in counts:
                        idx=np.repeat(np.flatnonzero(mask),c[mask].astype(int))
                        if len(idx) and y[idx].sum():
                            draws.append(alert_metrics(y[idx],budget_alerts(h6[m].to_numpy()[idx]))['recall'])
                ci=interval(draws)
                alerts.append({'group':g,'model':m,'policy':policy,**stats,
                               'recall_ci_low':ci['ci95'][0] if ci['ci95'] else None,
                               'recall_ci_high':ci['ci95'][1] if ci['ci95'] else None,'valid_draws':ci['valid_draws']})
        for c,b in [('C','A'),('C','B'),('D','A'),('D','B')]:
            ci=cis[g][names.index(f'{c}_minus_{b}')]
            contrasts.append({'group':g,'candidate':c,'baseline':b,'n':k,
                'brier_difference':float(columns[f'{c}_minus_{b}'][mask].mean()),
                'ci_low':ci['ci95'][0],'ci_high':ci['ci95'][1]})
    # False negatives at the original whole-sample allocation, never a new threshold.
    severity=[]
    for m in 'ABCD':
        for policy,alert in [('original_full_budget',budget_alerts(h6[m].to_numpy())),
                             ('saved_train_quantile',h6[m].to_numpy()>=h6[f'{m}_alert_threshold'].to_numpy())]:
            for g,mask in masks.items():
                event=mask&(y==1); fn=event&(~alert)
                severity.append({'group':g,'model':m,'policy':policy,'events':int(event.sum()),'fn':int(fn.sum()),
                    'fn_mean_ratio':float((panel.y/panel.vix)[fn].mean()) if fn.any() else None,
                    'fn_mean_realized_vol':float(np.sqrt(panel.y[fn]).mean()) if fn.any() else None,
                    'event_ivol_mean':float(np.sqrt(panel.vix[event]).mean()) if event.any() else None})
    return {'scores':rows,'bins':bins,'alerts':alerts,'contrasts':contrasts,'false_negatives':severity}


def h7_analysis(panel,masks,counts):
    y=panel.y.to_numpy(); columns={}; rows=[]; contrasts=[]; concentration=[]; leaveout=[]
    for m in MODELS:
        f=panel[m].to_numpy(); error=f-y; q=y/f-np.log(y/f)-1
        columns.update({f'{m}_qlike':q,f'{m}_mse':error**2,f'{m}_mae':abs(error),
                        f'{m}_bias':error,f'{m}_forecast':f,f'{m}_under':(y>1.5*f).astype(float)})
    columns['target']=y
    for m in ['vix','garch','trailing']:
        for stat in ['qlike','mse','mae']:
            columns[f'combined_minus_{m}_{stat}']=columns[f'combined_{stat}']-columns[f'{m}_{stat}']
    names=list(columns); cis=mean_intervals(np.column_stack(list(columns.values())),masks,counts)
    for g,mask in masks.items():
        if not mask.any(): rows.append({'group':g,'model':None,'n':0}); continue
        for m in MODELS:
            f=panel[m].to_numpy()[mask]; actual=y[mask]; proj,_,_=projection(actual,f)
            row={'group':g,'model':m,'n':int(mask.sum()),'mean_target':float(actual.mean()),**proj}
            for stat in ['qlike','mse','mae','bias','forecast','under']:
                col=f'{m}_{stat}'; row[stat]=float(columns[col][mask].mean()); ci=cis[g][names.index(col)]['ci95']
                row[stat+'_ci_low'],row[stat+'_ci_high']=ci
            row['rmse']=math.sqrt(row['mse']); row['rmse_ci_low']=math.sqrt(max(row['mse_ci_low'],0)); row['rmse_ci_high']=math.sqrt(max(row['mse_ci_high'],0))
            rows.append(row)
        for m in ['vix','garch','trailing']:
            for stat in ['qlike','mse','mae']:
                key=f'combined_minus_{m}_{stat}'; ci=cis[g][names.index(key)]['ci95']
                contrasts.append({'group':g,'baseline':m,'loss':stat,'n':int(mask.sum()),
                                  'difference':float(columns[key][mask].mean()),'ci_low':ci[0],'ci_high':ci[1]})
    for m in MODELS:
        for stat in ['qlike','mse','mae']:
            x=columns[f'{m}_{stat}']; order=np.argsort(-x,kind='stable')
            for fraction in [.01,.05]:
                idx=order[:math.ceil(len(x)*fraction)]
                concentration.append({'model':m,'loss':stat,'fraction':fraction,'n':len(idx),
                                      'share_of_total_loss':float(x[idx].sum()/x.sum()),
                                      'origins':panel.origin.iloc[idx].tolist()})
    for year in range(2012,2026):
        mask=~masks[f'year_{year}']
        for m in ['vix','garch','trailing']:
            for stat in ['qlike','mse','mae']:
                leaveout.append({'omitted_year':year,'baseline':m,'loss':stat,
                    'difference':float(columns[f'combined_minus_{m}_{stat}'][mask].mean())})
    correlations=panel[['vix','garch','trailing']].corr().to_dict()
    standardized=(panel[['vix','garch','trailing']]-panel[['vix','garch','trailing']].mean())/panel[['vix','garch','trailing']].std(ddof=0)
    return {'scores':rows,'contrasts':contrasts,'concentration':concentration,'leave_year_out':leaveout,
            'predictor_correlations':correlations,'standardized_condition_number':float(np.linalg.cond(standardized))}


def coefficient_analysis(meta,panel):
    h6rows=[]; h7rows=[]; contributions=[]
    for fit in meta['h6']['fits']:
        for m in 'BCD':
            record=fit[m]
            for j,feature in enumerate(record['features']):
                beta=record['coefficients'][0][j] if record['coefficients'] else None
                h6rows.append({'as_of':fit['as_of'],'model':m,'feature':feature,'standardized_coefficient':beta,
                              'raw_coefficient':beta/record['scaler_scale'][j] if beta is not None else None,
                              'intercept_standardized':record['intercept'][0] if record['intercept'] else None,
                              'importance':record['feature_importance'][j] if record['feature_importance'] else None,
                              'training_mean':record['scaler_mean'][j],'training_scale':record['scaler_scale'][j],
                              'training_n':fit['training_n'],'training_events':fit['training_events']})
    fits={fit['as_of']:fit for fit in meta['h7']['fits']}
    for fit in fits.values():
        for m in ['combined','har']:
            record=fit[m]
            for j,feature in enumerate(record['features']):
                h7rows.append({'as_of':fit['as_of'],'model':m,'feature':feature,
                              'coefficient':record['raw_coefficients'][j],'intercept':record['raw_intercept'],
                              'standardized_coefficient':record['standardized_coefficients'][j],
                              'training_mean':record['scaler_mean'][j],'training_scale':record['scaler_scale'][j],
                              'smearing':record['smearing'],'training_n':fit['training_n']})
    errors=[]
    for _,row in panel.iterrows():
        fit=fits[row.as_of_fit]['combined']; betas=fit['raw_coefficients']; intercept=fit['raw_intercept']
        values=np.array([row.vix,row.garch,row.trailing]); contrib=values*betas
        rebuilt=max(intercept+sum(contrib),1e-8); errors.append(abs(rebuilt-row.combined))
        contributions.append({'origin':row.origin,'as_of_fit':row.as_of_fit,'intercept':intercept,
                              **{m:float(v) for m,v in zip(['vix','garch','trailing'],contrib)},
                              **{m+'_share':float(v/row.combined) for m,v in zip(['vix','garch','trailing'],contrib)},
                              'intercept_share':float(intercept/row.combined),'forecast':row.combined})
    if max(errors)>1e-12: raise ValueError('Raw combination replay mismatch')
    return {'h6':h6rows,'h7':h7rows,'contributions':contributions,'replay_max_error':max(errors)}


def h8_analysis(panel,spy,logs,masks,counts):
    rows=[]; accounting=[]; regimes=[]; bridges=[]; audits={}; daily_parts=[]
    n=len(panel); buyhold=logs['buyhold',0]['return'].to_numpy()
    for m in ['buyhold','trailing','vix','garch','combined']:
        gross=logs[m,0]; rg=gross['return'].to_numpy(); vg=float(np.var(rg,ddof=1)*252)
        if gross.signal_origin.tolist()!=panel.origin.tolist(): raise ValueError('Ledger signal mismatch')
        if m!='buyhold':
            f=panel[m].to_numpy(); w,err,cap,total=constraint_bridge(panel.y.to_numpy(),f)
            if not np.allclose(gross.target_weight,w,rtol=0,atol=1e-15): raise ValueError('Policy changed')
            proj,cal,u=projection(panel.y.to_numpy(),f)
            # Only 3519 earned signals; final origin deliberately unused.
            proxy=np.mean(total[:-1])+.01
            bridge=vg-proxy
            base={'calibration':float(np.mean((w*w*cal)[:-1])),
                  'forecast_residual':float(np.mean((w*w*u)[:-1])),
                  'constraint':float(cap[:-1].mean()),'implementation_horizon_bridge':float(bridge),
                  'proxy_variance':float(proxy),'calibration_intercept':proj['intercept'],'calibration_slope':proj['slope']}
        for cost in [0,1,5,10,25]:
            log=logs[m,cost]; r=log['return'].to_numpy(); parts,error=ledger_components(log,spy)
            if not np.allclose(log.cost,log.trade_notional*cost/10000,rtol=1e-10,atol=1e-14): raise ValueError('Cost recurrence')
            if not log.final_open_mark.iloc[-1] or log.final_open_mark.iloc[:-1].any() or log.cost.iloc[-1]!=0: raise ValueError('Endpoint mismatch')
            # Full symmetric covariance ledger: diagonal and cross terms sum to sample variance.
            cov=np.cov(parts.T,ddof=1)*252; realized=np.var(r,ddof=1)*252
            if abs(cov.sum()-realized)>1e-13: raise ValueError('P&L covariance identity')
            audits[f'{m}_{cost}']={'ledger_max_error':error,'variance_accounting_error':float(abs(cov.sum()-realized))}
            for i,a in enumerate(['overnight','dividend','intraday','negative_cost']):
                for j,b in enumerate(['overnight','dividend','intraday','negative_cost']):
                    accounting.append({'strategy':m,'cost_bps':cost,'component_a':a,'component_b':b,'annual_covariance':float(cov[i,j])})
            metric=portfolio_metrics(log); drag=float(np.log1p(rg).sum()-np.log1p(r).sum())
            row={'strategy':m,'cost_bps':cost,**metric,'mean_cash_fraction':float(1-log.opening_weight_after_trade.mean()),
                 'gross_minus_net_total_log_return':drag,
                 'gross_minus_net_cagr':portfolio_metrics(gross)['cagr']-metric['cagr'],
                 'foregone_vs_buyhold_total_log_return':float(np.log1p(buyhold).sum()-np.log1p(r).sum())}
            if m!='buyhold':
                row.update({'cap_fraction_earned':float(np.mean(w[:-1]==1)),
                            'mean_forecast':float(f[:-1].mean()),'mean_target':float(panel.y.iloc[:-1].mean()),
                            'mean_forecast_vol':float(np.sqrt(f[:-1]).mean()),
                            'cap_forecast_variance_shortfall':float(-cap[:-1].mean())})
                cost_effect=float(realized-vg); residual=realized-.01-sum([base['calibration'],base['forecast_residual'],base['constraint'],base['implementation_horizon_bridge'],cost_effect])
                if abs(residual)>1e-13: raise ValueError('End to end bridge identity')
                bridges.append({'strategy':m,'cost_bps':cost,'realized_variance_minus_target':float(realized-.01),
                                **base,'transaction_cost_variance_effect':cost_effect,'arithmetic_residual':float(residual)})
            rows.append(row)
            if cost==5:
                daily_parts.extend({'Date':d,'strategy':m,**{key:float(value) for key,value in zip(['overnight','dividend','intraday','negative_cost'],p)}} for d,p in zip(log.Date,parts))
                centered=(r-r.mean())**2*252/(n-1)
                rolling=rolling_volatility(r)
                for g,mask in masks.items():
                    if not mask.any(): regimes.append({'group':g,'strategy':m,'n':0}); continue
                    valid=mask&np.isfinite(rolling); subr=r[mask]
                    localnav=np.cumprod(1+subr); peak=np.maximum.accumulate(np.r_[1.,localnav])
                    info={'group':g,'strategy':m,'n':int(mask.sum()),
                          'variance_contribution':float(centered[mask].sum()),
                          'mean_weight':float(log.opening_weight_after_trade[mask].mean()),
                          'cash_fraction':float(1-log.opening_weight_after_trade[mask].mean()),
                          'annual_vol':float(np.std(subr,ddof=1)*np.sqrt(252)) if len(subr)>1 else None,
                          'rolling_target_rmse':float(np.sqrt(np.mean((rolling[valid]-.1)**2))) if valid.any() else None,
                          'rolling_under_target_fraction':float(np.mean(rolling[valid]<.1)) if valid.any() else None,
                          'total_log_return':float(np.log1p(subr).sum()),
                          'turnover_sum':float(log.turnover_nav[mask].sum()),'cost_initial_nav':float(log.cost[mask].sum()),
                          'drawdown_subgroup_path':float(np.min(np.r_[1.,localnav]/peak-1))}
                    # Labels use signal origin; fragmented subgroup drawdowns are descriptive, not investable paths.
                    if m!='buyhold':
                        earned=mask.copy(); earned[-1]=False
                        info.update({'cap_fraction':float(np.mean(w[earned]==1)) if earned.any() else None,
                                     'forecast_error_proxy':float(err[earned].mean()) if earned.any() else None,
                                     'constraint_proxy':float(cap[earned].mean()) if earned.any() else None,
                                     'mean_forecast':float(f[earned].mean()) if earned.any() else None,
                                     'mean_forward_realized_variance':float(panel.y[earned].mean()) if earned.any() else None})
                    regimes.append(info)
    return {'summary':rows,'regimes':regimes,'variance_components':accounting,'bridge':bridges,
            'accounting_audit':audits,'daily_components':daily_parts}


def sensitivity(h6,panel,masks,h8,counts_by_block):
    rows=[]
    y=h6.y.to_numpy(); cy=panel.y.to_numpy(); cf=panel.combined.to_numpy()
    columns={'prevalence':y,'C_minus_A_brier':(h6.C.to_numpy()-y)**2-(h6.A.to_numpy()-y)**2}
    for m in ['vix','garch','trailing']:
        f=panel[m].to_numpy(); columns[f'combined_minus_{m}_qlike']=(cy/cf-np.log(cy/cf)-1)-(cy/f-np.log(cy/f)-1)
    for block,counts in counts_by_block.items():
        ci=mean_intervals(np.column_stack(list(columns.values())),masks,counts)
        for g,mask in masks.items():
            for j,key in enumerate(columns):
                rows.append({'block':block,'group':g,'statistic':key,'estimate':float(columns[key][mask].mean()) if mask.any() else None,**ci[g][j]})
    return rows


def execute():
    code=implementation(['src/vrp/quant_failure.py','scripts/run_quant_failure.py','paper/quant_failure_diagnostic_plan.md'])
    before=frozen_inputs(); h6,panel,meta,spy,source,logs=load_inputs()
    before[source['path']]=sha(ROOT/source['path'])
    masks=partitions(panel)
    print('Verified inputs; generating fixed bootstrap draws',flush=True)
    counts_by_block={b:bootstrap_counts(len(panel),b) for b in [21,63,126]}
    print('H6 decomposition',flush=True); a=h6_analysis(h6,panel,masks,counts_by_block[63])
    print('H7 decomposition',flush=True); b=h7_analysis(panel,masks,counts_by_block[63])
    print('Coefficient audit and H8 exact accounting',flush=True)
    coeff=coefficient_analysis(meta,panel); c=h8_analysis(panel,spy,logs,masks,counts_by_block[63])
    print('Sensitivity diagnostics',flush=True); sens=sensitivity(h6,panel,masks,c,counts_by_block)
    for name,digest in before.items(): checked_hash(ROOT/name,digest)
    results={'status':STATUS,'plan_registration_commit':'7ad9187','implementation':code,
             'n':len(panel),'n_monthly_fits':168,'input_sha256':before,'spy_source':source,
             'bootstrap':{'seed':1729,'draws':1000,'blocks':[21,63,126],'selection':'full chronological resample then subgroup'},
             'h6':a,'h7':b,'coefficients':coeff,'h8':c,'sensitivity':sens,
             'limitations':'Historical descriptive decomposition; overlapping targets; no causal identification or prospective observations.'}
    hashes={}
    for h,sections in [('h6',a),('h7',b),('coefficients',coeff),('h8',c)]:
        for section,records in sections.items():
            if isinstance(records,list) and (not records or isinstance(records[0],dict)):
                frame=pd.DataFrame(records)
                # Keep nested values serialized, preserving all detailed origins/CI data.
                for col in frame:
                    if frame[col].map(lambda x:isinstance(x,(dict,list))).any():
                        frame[col]=frame[col].map(lambda x:json.dumps(x,sort_keys=True) if isinstance(x,(dict,list)) else x)
                hashes[f'{h}_{section}.csv']=csv_immutable(OUT/f'{h}_{section}.csv',frame)
    hashes['sensitivities.csv']=csv_immutable(OUT/'sensitivities.csv',pd.DataFrame(sens))
    results['table_sha256']=hashes
    persist(OUT/'results.json',results)
    persist(ROOT/'data/manifests/quant_failure_results_v1.json',results)
    print('Complete; results SHA '+sha(OUT/'results.json'),flush=True)
    return results
