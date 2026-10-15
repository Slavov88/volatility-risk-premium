import math
from datetime import date

import pytest

from vrp.calendar import exchange_sessions, forward_30c_sessions, is_exchange_session, next_exchange_sessions
from vrp.evaluation import (
    common_evaluation_mask,
    estimation_window,
    out_of_sample_split,
)
from vrp.inference import holm_adjust_two, nonoverlapping_origins_30c, overlap_l0
from vrp.returns import log_returns


def test_xnys_calendar_covers_verified_1986_training_history() -> None:
    sessions = exchange_sessions(date(1986, 1, 2), date(1986, 1, 8))
    assert sessions[0] == date(1986, 1, 2)
    assert date(1986, 1, 3) in sessions
    assert is_exchange_session(date(1986, 1, 3))


def test_future_data_mutation_cannot_change_estimation_window_at_origin() -> None:
    origin = date(2024, 1, 5)
    sessions = exchange_sessions(date(2024, 1, 2), date(2024, 1, 10))
    baseline = [(day, index / 1000.0) for index, day in enumerate(sessions)]
    altered = [
        (day, value if day <= origin else value + 9.0)
        for day, value in baseline
    ]
    assert estimation_window(origin, baseline) == estimation_window(origin, altered)


def test_common_mask_is_exact_intersection_and_rejects_bad_origin() -> None:
    origins = exchange_sessions(date(2024, 1, 2), date(2024, 1, 5))
    target = {day: 0.04 for day in origins}
    forecasts = {
        "vix": {day: 0.04 for day in origins},
        "garch": {day: 0.04 for day in origins},
        "naive": {day: 0.04 for day in origins},
    }
    forecasts["garch"][origins[1]] = None
    assert common_evaluation_mask(origins, target, forecasts) == (
        origins[0],
        origins[2],
        origins[3],
    )


def test_oos_split_rejects_non_exchange_dates() -> None:
    with pytest.raises(ValueError, match="XNYS"):
        out_of_sample_split([date(2007, 1, 6)])  # Saturday


def test_special_exchange_closures_are_not_sessions() -> None:
    september_2001 = set(exchange_sessions(date(2001, 9, 10), date(2001, 9, 17)))
    for closed in [
        date(2001, 9, 11),
        date(2001, 9, 12),
        date(2001, 9, 13),
        date(2001, 9, 14),
    ]:
        assert closed not in september_2001

    sandy = set(exchange_sessions(date(2012, 10, 26), date(2012, 10, 31)))
    assert date(2012, 10, 29) not in sandy
    assert date(2012, 10, 30) not in sandy

    bush_funeral = set(exchange_sessions(date(2018, 12, 4), date(2018, 12, 6)))
    assert date(2018, 12, 5) not in bush_funeral


def test_locked_2025_tail_calendar_is_exact() -> None:
    origin = date(2025, 12, 31)
    assert forward_30c_sessions(origin)[-1] == date(2026, 1, 30)
    assert next_exchange_sessions(origin, 21)[-1] == date(2026, 2, 2)


def test_nonoverlapping_selector_uses_calendar_endpoint_only() -> None:
    origins = exchange_sessions(date(2024, 1, 2), date(2024, 4, 30))
    selected = nonoverlapping_origins_30c(origins)
    assert selected[0] == origins[0]
    for left, right in zip(selected, selected[1:]):
        assert right > left.replace()  # distinct dates
        assert right > left.fromordinal(left.toordinal() + 30)


def test_overlap_l0_rejects_post_cutoff_origins() -> None:
    with pytest.raises(ValueError, match="after locked cutoff"):
        overlap_l0([date(2026, 1, 2)])


def test_holm_adjust_two_matches_manual_fixture() -> None:
    adjusted = holm_adjust_two([0.04, 0.01])
    assert adjusted == pytest.approx((0.04, 0.02))
    with pytest.raises(ValueError, match="exactly two"):
        holm_adjust_two([0.1])
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        holm_adjust_two([0.1, math.nan])


def test_log_returns_has_no_calendar_bypass() -> None:
    with pytest.raises(ValueError, match="not consecutive"):
        log_returns(
            [date(2024, 1, 2), date(2024, 1, 4)],
            [100.0, 101.0],
        )
