from datetime import date
import json
import numpy as np
import pytest

from vrp.calendar import exchange_sessions
from vrp.evaluation import estimation_window
from vrp.recursive_garch import Checkpoints, fit_origin, training_slice


@pytest.mark.parametrize("window",["expanding","rolling_5y"])
def test_fast_training_slice_equals_locked_window_and_no_lookahead(window):
    dates=list(exchange_sessions(date(1999,1,4),date(2007,2,28)))
    values=np.arange(len(dates))/100000.;origin=date(2007,1,3)
    start,end,train=training_slice(dates,values,origin,window)
    oracle=estimation_window(origin,list(zip(dates,values)),window=window)
    assert [dates[start],dates[end-1]]==[oracle[0][0],oracle[-1][0]]
    assert train.tolist()==[v for _,v in oracle]
    changed=values.copy();changed[end:]=99
    assert np.array_equal(train,training_slice(dates,changed,origin,window)[2])


def test_real_garch_forecast_and_independent_variance_recurrence():
    rng=np.random.default_rng(42);values=rng.normal(scale=.01,size=700)
    record=fit_origin(values,"normal",22)
    assert record["status"]=="CONVERGED"
    assert len(record["daily_decimal_variances"])==22
    assert record["recurrence_max_abs_error_percent_squared"]<1e-8
    assert all(0<v<.001 for v in record["daily_decimal_variances"])


def test_checkpoints_resume_and_reject_tampered_inputs_and_payload(tmp_path):
    store=Checkpoints(tmp_path/"fits.sqlite",{"model":"locked"})
    expected={"origin":"2024-01-02","training_sha256":"abc"}
    store.write(expected["origin"],{**expected,"status":"CONVERGED"})
    assert store.read(expected["origin"],expected)["status"]=="CONVERGED"
    with pytest.raises(ValueError,match="input identity"):
        store.read(expected["origin"],{**expected,"training_sha256":"bad"})
    store.db.execute("UPDATE fits SET payload='{}'");store.db.commit()
    with pytest.raises(ValueError,match="payload hash"):
        store.read(expected["origin"],expected)
    store.close()
    with pytest.raises(ValueError,match="configuration"):
        Checkpoints(tmp_path/"fits.sqlite",{"model":"changed"})
