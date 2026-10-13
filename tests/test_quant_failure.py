"""Independent identities and adversarial diagnostic boundaries."""
import numpy as np
import pandas as pd
import pytest
from vrp.quant_failure import (brier_decomposition, projection, constraint_bridge,
    partitions, ledger_components, bootstrap_counts, mean_intervals)
from vrp.quant_portfolio import simulate_spy
from vrp.quant_failure_audit import weighted_rank, weighted_projection_draws
from sklearn.metrics import roc_auc_score, average_precision_score


def test_brier_exact_within_bin_and_imbalance():
    y=np.r_[np.ones(7),np.zeros(93)]
    p=np.linspace(.001,.999,100)
    d=brier_decomposition(y,p)
    assert d['event_contribution']+d['nonevent_contribution']==pytest.approx(np.mean((y-p)**2))
    assert d['reliability']-d['resolution']+d['uncertainty']+d['within_bin_residual']==pytest.approx(d['brier'])
    assert abs(d['within_bin_residual'])>1e-6
    constant=brier_decomposition(y,np.repeat(y.mean(),len(y)))
    assert constant['brier']==pytest.approx(.07*.93)
    assert constant['resolution']==0
    assert len(constant['bins'])==10


def test_projection_retains_all_cross_terms():
    rng=np.random.default_rng(35); f=np.exp(rng.normal(-3,1,101)); y=.01+.7*f+rng.normal(0,.01,len(f))
    d,cal,u=projection(y,f)
    assert np.allclose(y-f,cal+u)
    assert d['mse']==pytest.approx(d['calibration_mse']+d['residual_mse']+d['cross_term'])
    assert d['mse']==pytest.approx(d['bias_squared']+d['centered_error_variance'])


def test_cap_shortfall_is_forecast_target_not_realized_bound():
    f=np.array([.0025,.01,.04]); y=np.array([.16,.01,.01])
    w,error,cap,total=constraint_bridge(y,f)
    assert np.array_equal(w,[1,1,.5])
    assert np.allclose(cap,np.minimum(f,.01)-.01)
    assert np.allclose(error+cap,total)
    assert total[0]>0  # A cap does not prevent subsequent realized shock variance.
    with pytest.raises(ValueError): constraint_bridge([.1],[0])


def test_partition_boundaries_and_future_outcome_changes():
    frame=pd.DataFrame({'origin':['2020-02-18','2020-02-19','2020-03-24'],
        'vix_close':[14.99,15,25],'vix_change5':[-.2,0,.2], 'y':[.02,.03,.04],
        'vix':[.01,.02,.03],'trailing':[.01,.02,.03]})
    before=partitions(frame); frame['y']*=100; after=partitions(frame)
    for g in before:
        if not g.startswith('outcome_'): assert np.array_equal(before[g],after[g])
    assert before['vix_low'].tolist()==[True,False,False]
    assert before['vix_mid'].tolist()==[False,True,False]
    assert before['vix_high'].tolist()==[False,False,True]
    assert before['shock_up'].tolist()==[False,False,True]
    assert before['shock_down'].tolist()==[True,False,False]


def test_ledger_dividend_overnight_fees_and_terminal():
    spy=pd.DataFrame({'Date':['2020-01-02','2020-01-03','2020-01-06'],
                      'Open':[100.,103.,101.],'Close':[102.,100.,999.], 'Dividends':[0.,1.,0.]})
    signals=pd.DataFrame({'origin':['2019-12-31','2020-01-02','2020-01-03']})
    log=simulate_spy(spy,signals,np.array([.5,1.,.2]),5)
    parts,err=ledger_components(log,spy)
    assert err<1e-13
    assert parts[1,1]>0
    assert parts[-1,2]==0
    assert log.cost.iloc[-1]==0
    bad=log.copy(); bad.loc[1,'cash']+=.1
    with pytest.raises(ValueError): ledger_components(bad,spy)


def test_resampling_keeps_group_gaps_and_determinism():
    a=bootstrap_counts(100,21); b=bootstrap_counts(100,21)
    assert np.array_equal(a,b); assert np.all(a.sum(axis=1)==100)
    mask=np.arange(100)%4==0
    x=np.arange(100,dtype=float)[:,None]
    ci=mean_intervals(x,{'g':mask},a)['g'][0]
    independent=(a[:,mask]@x[mask]).ravel()/a[:,mask].sum(axis=1)
    assert np.allclose(ci['ci95'],np.quantile(independent,[.025,.975]))


def test_weighted_rank_ties_zero_weights_and_independent_scores():
    y=np.array([1,0,1,0,1,0]); p=np.array([.2,.2,.1,.1,.4,.9]); weights=np.array([3,2,0,1,2,1])
    actual=weighted_rank(y,p,weights)
    assert np.allclose(actual,[roc_auc_score(y,p,sample_weight=weights),average_precision_score(y,p,sample_weight=weights)])
    assert weighted_rank(np.ones(4),np.arange(4),np.ones(4))[1]==1
    assert np.isnan(weighted_rank(np.zeros(4),np.arange(4),np.ones(4))).all()


def test_weighted_projection_bootstrap_matches_expanded_rows():
    f=np.array([.01,.02,.05,.1]); y=np.array([.03,.01,.06,.2]); c=np.tile([1,2,3,1],(1000,1))
    a,b=weighted_projection_draws(y,f,np.ones(4,bool),c)
    idx=np.repeat(np.arange(4),c[0]); d,_,_=projection(y[idx],f[idx])
    assert a['ci95']==pytest.approx([d['intercept']]*2)
    assert b['ci95']==pytest.approx([d['slope']]*2)
