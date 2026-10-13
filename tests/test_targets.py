import math
from datetime import date

from vrp.calendar import forward_30c_sessions, next_exchange_sessions
from vrp.targets import (
    assert_forecast_origin_allowed,
    primary_horizon_end,
    realized_variance_21t,
    realized_variance_30c,
    realized_volatility,
    select_forward_21t,
    select_forward_30c,
)


def test_30_calendar_day_horizon_end() -> None:
    assert primary_horizon_end(date(2024, 1, 2)) == date(2024, 2, 1)
    assert primary_horizon_end(date(2025, 12, 31)) == date(2026, 1, 30)


def test_rvar_30c_requires_every_expected_exchange_session() -> None:
    origin = date(2024, 1, 2)
    sessions = forward_30c_sessions(origin)
    pairs = [(day, 0.01) for day in sessions]
    rvar = realized_variance_30c(origin, pairs)
    assert rvar is not None
    expected = (365 / 30) * len(sessions) * 0.0001
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)

    missing_middle = pairs[:4] + pairs[5:]
    assert realized_variance_30c(origin, missing_middle) is None
    assert select_forward_30c(origin, missing_middle) is None


def test_rvar_30c_does_not_accept_endpoint_only_data() -> None:
    origin = date(2025, 12, 31)
    sessions = forward_30c_sessions(origin)
    endpoint_only = [(sessions[0], 0.01), (sessions[-1], 0.02)]
    assert realized_variance_30c(origin, endpoint_only) is None


def test_rvar_21t_requires_exact_next_21_sessions() -> None:
    origin = date(2024, 1, 2)
    sessions = next_exchange_sessions(origin, 22)
    pairs = [(day, (index + 1) / 1000.0) for index, day in enumerate(sessions)]
    selected = select_forward_21t(origin, pairs)
    assert selected == [value for _, value in pairs[:21]]

    missing_fifth = pairs[:4] + pairs[5:]
    assert select_forward_21t(origin, missing_fifth) is None
    assert realized_variance_21t(origin, missing_fifth) is None


def test_realized_volatility_validates_input() -> None:
    assert math.isclose(realized_volatility(0.04), 0.2)
    for bad in [-0.1, float("nan"), float("inf")]:
        try:
            realized_volatility(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid variance should be rejected")


def test_forecast_origin_cutoff() -> None:
    assert_forecast_origin_allowed(date(2025, 12, 31))
    assert_forecast_origin_allowed(date(1990, 1, 2))
    try:
        assert_forecast_origin_allowed(date(2026, 1, 2))
    except ValueError:
        pass
    else:
        raise AssertionError("post-cutoff origin accepted")
