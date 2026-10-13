"""Adversarial availability, units, day count and self-financing regressions."""
import numpy as np
import pandas as pd
import pytest
from vrp.cash_yield import (investment_rate,rate_schedule,cash_replay,independently_audit,
                           attribution,fast_rolling,exact_reference_values)
from vrp.quant_portfolio import simulate_spy,rolling_volatility


def quotes():
    return pd.DataFrame({'period_start_date':['2020-02-25','2020-02-26','2020-02-27'],
        'DGS1MO':[5.,6.,99.],'realtime_start_date':['2020-02-26','2020-02-27','2020-03-02']})


def test_release_is_not_observation_and_future_revision_cannot_affect_prior_interval():
    dates=['2020-02-28','2020-03-02','2020-03-03'];q=quotes()
    s=rate_schedule(q,dates,'DGS1MO')
    assert s.observation_date.iloc[1]=='2020-02-26'
    assert s.quote_percent.iloc[1]==6
    assert s.elapsed_days.tolist()==[0,3,1] # Leap day and weekend included.
    assert s.cash_factor.iloc[1]==pytest.approx(.06*3/365)
    q.loc[2,'DGS1MO']=123.; changed=rate_schedule(q,dates,'DGS1MO')
    assert s.cash_factor.iloc[1]==changed.cash_factor.iloc[1]
    # A release on start date is still unknown under the end-of-vintage policy.
    assert s.observation_date.iloc[2]=='2020-02-26'


def test_percent_discount_conversion_negative_quotes_and_fail_closed():
    assert investment_rate(5.,'DGS1MO')==pytest.approx(.05)
    expected=.05/360/(1-.05*28/360)*365
    assert investment_rate(5.,'DTB4WK')==pytest.approx(expected)
    assert investment_rate(-.01,'DGS1MO')<0
    with pytest.raises(ValueError):investment_rate(np.nan,'DGS1MO')
    with pytest.raises(ValueError):investment_rate(2000,'DTB4WK')
    with pytest.raises(ValueError):rate_schedule(quotes(),['2019-01-01','2019-01-02'],'DGS1MO')
    with pytest.raises(ValueError):rate_schedule(quotes(),['2021-01-01','2021-01-04'],'DGS1MO')


def test_dst_uses_calendar_day_count_not_elapsed_clock_hours():
    q=pd.DataFrame({'period_start_date':['2020-03-04'],'DGS1MO':[5.], 'realtime_start_date':['2020-03-05']})
    s=rate_schedule(q,['2020-03-06','2020-03-09'],'DGS1MO')
    assert s.elapsed_days.iloc[1]==3
    assert s.cash_factor.iloc[1]==pytest.approx(.05*3/365)


def example():
    spy=pd.DataFrame({'Date':['2020-02-28','2020-03-02','2020-03-03'],
        'Open':[100.,103.,102.],'Close':[101.,102.,999.],'Dividends':[0.,1.,0.]})
    signals=pd.DataFrame({'origin':['2020-02-27','2020-02-28','2020-03-02']})
    original=simulate_spy(spy,signals,np.array([.5,.6,.9]),5)
    schedule=rate_schedule(quotes(),original.Date.tolist(),'DGS1MO')
    return spy,original,schedule


def test_zero_replay_exact_interest_on_actual_cash_and_dividend_timing():
    spy,original,schedule=example()
    zero=cash_replay(spy,original,schedule,0.,5)
    assert zero[original.columns].equals(original)
    log=cash_replay(spy,original,schedule,1.,5)
    assert log.cash_interest.iloc[0]==0
    assert log.cash_interest.iloc[1]==pytest.approx(zero.cash.iloc[0]*.06*3/365)
    assert log.cash_interest.iloc[1]!=pytest.approx((zero.cash.iloc[0]+log.dividend_cash.iloc[1])*.06*3/365,abs=1e-12)
    assert log.final_open_mark.iloc[-1]
    assert log.cost.iloc[-1]==0
    assert log.target_weight.equals(original.target_weight)
    parts,audit=independently_audit(log,spy,schedule,'DGS1MO',1.,5)
    assert audit['max_absolute_accounting_error']<1e-12
    assert parts[-1,2]==0
    assert parts[-1,3]>0
    _,baseline=independently_audit(zero,spy,schedule,'DGS1MO',0.,5)
    zp,_=independently_audit(zero,spy,schedule,'DGS1MO',0.,5)
    att,_=attribution(log,zero,parts,zp)
    assert att['incremental_log_growth']==pytest.approx(att['direct_interest_log_contribution']+att['changed_equity_dividend_log_contribution']+att['changed_fee_log_contribution'])
    bad=log.copy();bad.loc[1,'cash_interest']+=.01
    with pytest.raises(ValueError):independently_audit(bad,spy,schedule,'DGS1MO',1.,5)


def test_rolling_risk_independent_formula_and_deterministic_replay():
    rng=np.random.default_rng(1729);r=rng.normal(0,.01,500)
    assert np.allclose(fast_rolling(r),rolling_volatility(r)[20:],atol=1e-12,rtol=1e-10)
    spy,original,schedule=example()
    assert cash_replay(spy,original,schedule,.5,10).equals(cash_replay(spy,original,schedule,.5,10))


def test_csv_integer_inference_does_not_mask_numerical_reference_changes():
    a=pd.DataFrame({'cash':[0,0],'weight':[1,1]});b=a.astype(float)
    assert exact_reference_values(b,a)
    b.loc[1,'cash']=1e-17
    assert not exact_reference_values(b,a)
