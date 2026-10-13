import math
from datetime import date

from vrp.calendar import (
    exchange_sessions,
    forward_30c_sessions,
    trailing_30c_sessions,
    trailing_exchange_sessions,
)
from vrp.evaluation import (
    naive_variance_21t,
    naive_variance_30c,
    out_of_sample_split,
)


def test_oos_split_requires_all_forward_exchange_sessions() -> None:
    origin = date(2007, 1, 3)
    future = forward_30c_sessions(origin)
    sessions = [
        date(1990, 1, 2),
        date(2006, 12, 29),
        origin,
        *future,
    ]
    split = out_of_sample_split(sessions)
    assert origin in split.evaluation_origins

    broken = [day for day in sessions if day != future[5]]
    assert origin not in out_of_sample_split(broken).evaluation_origins


def test_naive_30c_requires_every_expected_trailing_session() -> None:
    origin = date(2024, 2, 1)
    sessions = trailing_30c_sessions(origin)
    values = [(day, 0.01) for day in sessions]
    forecast = naive_variance_30c(origin, values)
    assert forecast is not None
    assert math.isclose(
        forecast,
        (365 / 30) * len(sessions) * 0.0001,
        abs_tol=1e-12,
    )
    assert naive_variance_30c(origin, values[:-1]) is None


def test_naive_21t_requires_exact_trailing_sessions() -> None:
    origin = date(2024, 2, 1)
    sessions = trailing_exchange_sessions(origin, 21)
    values = [(day, 0.01) for day in sessions]
    assert naive_variance_21t(origin, values) is not None
    broken = values[:7] + values[8:]
    assert naive_variance_21t(origin, broken) is None


def test_calendar_fixture_contains_real_weekend_and_holiday_gaps() -> None:
    sessions = exchange_sessions(date(2024, 7, 1), date(2024, 7, 8))
    assert date(2024, 7, 4) not in sessions
    assert date(2024, 7, 5) in sessions
    assert date(2024, 7, 8) in sessions
