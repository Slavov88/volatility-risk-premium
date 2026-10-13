from datetime import date
import numpy as np
import pytest
from vrp.asof_garch_calendar import corrected_record, forecast_schedule, scheduled_steps
from vrp.calendar import forward_30c_sessions


def record(dist="normal", persistence=.95, steps=21):
    omega=.00001; values=[.0002]
    for _ in range(steps-1):
        values.append(omega+persistence*values[-1])
    n=len(forward_30c_sessions(date(2012,10,1)))
    return {"origin":"2012-10-01","training_end":"2012-10-01","status":"CONVERGED",
            "parameters":{"omega":omega*10000,"alpha[1]":.1,"beta[1]":persistence-.1,**({"nu":5.} if dist=="t" else {})},
            "daily_decimal_variances":values,"session_count_30c":n,"forecast_sessions":[d.isoformat() for d in scheduled_steps("2012-10-01",steps)],
            "garch_30c":365/30*sum(values[:n]),"garch_21t":252/21*sum(values[:21])}


@pytest.mark.parametrize("dist",["normal","t"])
@pytest.mark.parametrize("persistence",[.8,.9999,1.,1.000000000000001])
def test_reuse_extend_annualization_and_exact21(dist,persistence):
    original=record(dist,persistence); corrected=corrected_record(original,dist)
    assert corrected["garch_21t"]==original["garch_21t"]
    assert corrected["session_count_30c"]==22
    assert corrected["correction_audit"]["extended_steps"]==1
    assert corrected["garch_30c"]==pytest.approx(sum(corrected["daily_decimal_variances"][:22])*365/30)
    assert len(original["daily_decimal_variances"])==21


def test_injected_future_closure_changes_actual_targets_not_forecasts(monkeypatch):
    import vrp.calendar as cal
    from vrp.targets import select_forward_30c
    origin=date(2018,11,15); before=forecast_schedule(origin)
    known=cal.exchange_sessions
    injected=date(2018,11,20)
    announcement=date(2018,11,19)
    assert origin<announcement<injected
    cached=record();cached["origin"]=origin.isoformat();cached["training_end"]=origin.isoformat()
    cached["session_count_30c"]=len(cal.forward_30c_sessions(origin))
    cached["garch_30c"]=365/30*sum(cached["daily_decimal_variances"][:cached["session_count_30c"]])
    prediction_before=corrected_record(cached,"normal")
    monkeypatch.setattr(cal,"exchange_sessions",lambda start,end:tuple(d for d in known(start,end) if d!=injected))
    assert forecast_schedule(origin)==before
    assert injected not in cal.forward_30c_sessions(origin)
    assert injected in before[0]
    prediction_after=corrected_record(cached,"normal")
    assert prediction_after["garch_30c"]==prediction_before["garch_30c"]
    assert prediction_after["garch_21t"]==prediction_before["garch_21t"]
    returns=[(d,.01) for d in known(origin,date(2018,12,15)) if d!=injected]
    # Actual target selector follows actual sessions, which is correct ex-post.
    selected=select_forward_30c(origin,returns)
    assert len(selected)==len(cal.forward_30c_sessions(origin))
    assert len(selected)==len(before[0])-2  # injected closure plus known Bush funeral


def test_missing_or_corrupt_recurrence_and_future_training_rejected():
    r=record("t");r["parameters"]["nu"]=2
    with pytest.raises(ValueError,match="second moment"):
        corrected_record(r,"t")
    r=record();r["daily_decimal_variances"][5]=10
    with pytest.raises(ValueError,match="recurrence"):
        corrected_record(r,"normal")
    r=record();r["training_end"]="2012-10-02"
    with pytest.raises(ValueError,match="training"):
        corrected_record(r,"normal")


def test_new_recursive_pipeline_cannot_call_actual_future_selector(monkeypatch):
    import vrp.recursive_garch as pipeline
    import vrp.calendar as calendar
    monkeypatch.setattr(calendar,"forward_30c_sessions",lambda *_: (_ for _ in ()).throw(AssertionError("future actual calendar used")))
    assert len(pipeline.forecast_schedule("2012-10-01")[0])==22
