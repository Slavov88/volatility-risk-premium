from datetime import date
import numpy as np
import pytest
from vrp.empirical_calendar_repair import (holiday_audit,independent_regular_holidays,checked_first_variance,fixed_nonoverlap,analysis)
from vrp.recursive_garch import fit_origin


def test_regular_rule_history_and_first_forecast_window():
    result=holiday_audit()
    assert result["scheduled_holiday_dates_checked"]==185
    holidays=independent_regular_holidays()
    assert date(2021,6,18) not in holidays
    assert date(2022,6,20) in holidays
    assert date(2021,12,31) not in holidays  # Saturday NewYear is not observed Friday.
    assert date(2023,1,2) in holidays


@pytest.mark.parametrize("distribution",["normal","t"])
def test_first_variance_reconstructed_from_training_not_future(distribution):
    train=np.random.default_rng(42).normal(scale=.01,size=800)
    fit=fit_origin(train,distribution,21)
    assert fit["status"]=="CONVERGED"
    error=checked_first_variance(train,fit["parameters"],fit["daily_decimal_variances"][0])
    assert error<1e-12
    with pytest.raises(ValueError,match="first-step"):
        checked_first_variance(train,fit["parameters"],fit["daily_decimal_variances"][0]*1.1)


def test_nonoverlap_uses_complete_window_not_origin_order_only():
    origins=["2020-01-02","2020-01-03","2020-01-31","2020-02-03"]
    ends=["2020-02-01","2020-02-02","2020-03-01","2020-03-04"]
    assert fixed_nonoverlap(origins,ends).tolist()==[0,3]


def test_inference_common_mask_and_no_model_replacement():
    from vrp.calendar import exchange_sessions
    dates=[d.isoformat() for d in exchange_sessions(date(2018,1,2),date(2018,6,30))[:90]]
    y=np.linspace(.01,.1,90)+.001*np.sin(np.arange(90))
    predictions={"vix":np.linspace(.015,.11,90),"garch":np.linspace(.012,.09,90)+.002*np.cos(np.arange(90)),"naive":np.linspace(.02,.08,90)}
    first=analysis(dates,y,predictions,"30c")
    assert first==analysis(dates,y,predictions,"30c")
    bad={m:v.copy() for m,v in predictions.items()};bad["garch"][0]=np.nan
    with pytest.raises(ValueError,match="mask"):
        analysis(dates,y,bad,"30c")
