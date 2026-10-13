from datetime import date
import math

import pytest

from vrp.calendar import exchange_sessions,forward_30c_sessions,next_exchange_sessions
from vrp.spx_discrepancy_impact import correction_footprint


def test_single_close_change_has_opposite_adjacent_return_effects_without_mutation():
    days=exchange_sessions(date(2024,1,2),date(2024,3,1))
    closes=[100.*math.exp(i*.001) for i in range(len(days))]
    old=closes.copy()
    day=date(2024,2,1)
    index=days.index(day)
    replacement=closes[index]*math.exp(.002)
    report=correction_footprint(days,closes,{day:replacement},days)[0]
    assert report["signed_log_return_adjustments"] == pytest.approx([.002,-.002])
    assert closes==old
    affected={day,days[index+1]}
    expected30=[d.isoformat() for d in days if affected.intersection(forward_30c_sessions(d))]
    expected21=[d.isoformat() for d in days if affected.intersection(next_exchange_sessions(d,21))]
    assert report["affected_origins"] == {"30c":expected30,"21t":expected21}
    assert days[index+1].isoformat() not in report["affected_origins"]["30c"]
    assert not set(report)&{"rvar","vrp_x","p_value"}


def test_weekend_next_return_and_target_membership_are_calendar_correct():
    days=exchange_sessions(date(2024,1,2),date(2024,2,15))
    report=correction_footprint(days,[100.]*len(days),{date(2024,1,5):101.},days)[0]
    assert report["affected_return_end_dates"] == ["2024-01-05","2024-01-08"]
    assert report["signed_log_return_adjustments"][0]+report["signed_log_return_adjustments"][1]==0


def test_incomplete_adjacent_sessions_rejected():
    with pytest.raises(ValueError,match="Missing next"):
        correction_footprint(["2024-01-02","2024-01-03","2024-01-05"],[100.,101.,102.],{"2024-01-03":102.},[])


@pytest.mark.parametrize("value", [0.,-1.,float("nan"),float("inf")])
def test_invalid_replacement_rejected(value):
    with pytest.raises(ValueError,match="Replacement"):
        correction_footprint(["2024-01-02","2024-01-03","2024-01-04"],[100.,101.,102.],{"2024-01-03":value},[])
