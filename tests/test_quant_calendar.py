from datetime import date
import numpy as np
import pytest
from vrp.quant_calendar import scheduled_forward_sessions, reaggregate_garch
from vrp.calendar import forward_30c_sessions, xnys_calendar


def test_sandy_not_known_to_preclosure_forecast():
    scheduled = scheduled_forward_sessions("2012-10-01")
    actual = forward_30c_sessions(date(2012,10,1))
    assert date(2012,10,29) in scheduled and date(2012,10,30) in scheduled
    assert date(2012,10,29) not in actual and date(2012,10,30) not in actual
    assert len(scheduled) == len(actual)+2


def test_future_adhoc_calendar_perturbation_does_not_change_forecast(monkeypatch):
    from vrp import quant_calendar
    before = scheduled_forward_sessions("2025-12-01")
    class Fake:
        regular_holidays = xnys_calendar().regular_holidays
        adhoc_holidays = [date(2025,12,3),date(2025,12,4),date(2025,12,5)]
    monkeypatch.setattr(quant_calendar, "xnys_calendar", lambda: Fake())
    assert scheduled_forward_sessions("2025-12-01") == before


def test_reaggregated_garch_uses_only_daily_forecast_and_schedule():
    r = {"origin": "2012-10-01", "training_end": "2012-10-01", "daily_decimal_variances": [.0001]*22,
         "parameters": {"omega": .1, "alpha[1]": .1, "beta[1]": .8}}
    assert reaggregate_garch(r) == pytest.approx(len(scheduled_forward_sessions(r["origin"]))*365/30*.0001)
    r["garch_30c"] = 1e9
    assert reaggregate_garch(r) < 1
    r["daily_decimal_variances"] = [.0001]
    with pytest.raises(ValueError, match="horizon"):
        reaggregate_garch(r)


def test_analytic_extension_and_corrupted_recurrence():
    r = {"origin":"2012-10-01","training_end":"2012-10-01", "daily_decimal_variances":[.0001]*21,
         "parameters":{"omega":.1,"alpha[1]":.1,"beta[1]":.8}}
    assert reaggregate_garch(r) == pytest.approx(.0001*len(scheduled_forward_sessions(r["origin"]))*365/30)
    r["daily_decimal_variances"][10] = .1
    with pytest.raises(ValueError, match="recurrence"):
        reaggregate_garch(r)


def test_scheduled_regular_holiday_removed_but_funeral_not():
    dates = scheduled_forward_sessions("2018-11-15")
    assert date(2018,11,22) not in dates
    assert date(2018,12,5) in dates
