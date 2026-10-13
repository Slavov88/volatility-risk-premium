import math
from datetime import date

from vrp.calendar import forward_30c_sessions, next_exchange_sessions
from vrp.range_estimators import (
    garman_klass_daily,
    parkinson_daily,
    realized_range_variance_21t,
    realized_range_variance_30c,
)


def test_parkinson_known_fixture() -> None:
    value = parkinson_daily(110.0, 100.0)
    expected = (math.log(1.1) ** 2) / (4.0 * math.log(2.0))
    assert math.isclose(value, expected, rel_tol=0, abs_tol=1e-15)


def test_garman_klass_known_fixture() -> None:
    value = garman_klass_daily(100.0, 110.0, 90.0, 105.0)
    expected = 0.5 * (math.log(110.0 / 90.0) ** 2) - (
        2.0 * math.log(2.0) - 1.0
    ) * (math.log(1.05) ** 2)
    assert math.isclose(value, expected, rel_tol=0, abs_tol=1e-15)


def test_range_variance_30c_requires_complete_session_set() -> None:
    origin = date(2024, 1, 2)
    sessions = forward_30c_sessions(origin)
    daily = [(day, 0.002) for day in sessions]
    result = realized_range_variance_30c(origin, daily)
    assert result is not None
    assert math.isclose(result, (365 / 30) * len(sessions) * 0.002)
    assert realized_range_variance_30c(origin, daily[:-1]) is None


def test_range_variance_21t_requires_exact_sessions() -> None:
    origin = date(2024, 1, 2)
    sessions = next_exchange_sessions(origin, 21)
    daily = [(day, 0.003) for day in sessions]
    result = realized_range_variance_21t(origin, daily)
    assert result is not None
    assert math.isclose(result, (252 / 21) * 21 * 0.003)
    assert realized_range_variance_21t(origin, daily[:-1]) is None
