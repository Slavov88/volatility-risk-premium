import math
from datetime import date, timedelta

import pytest

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
    assert math.isclose(value, 0.0032763713930836426, rel_tol=0, abs_tol=1e-18)
    assert parkinson_daily(100.0, 100.0) == 0.0


def test_garman_klass_known_fixture() -> None:
    value = garman_klass_daily(100.0, 110.0, 90.0, 105.0)
    expected = 0.5 * (math.log(110.0 / 90.0) ** 2) - (2.0 * math.log(2.0) - 1.0) * (
        math.log(1.05) ** 2
    )
    assert math.isclose(value, expected, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(value, 0.01921479796164129, rel_tol=0, abs_tol=1e-18)
    assert garman_klass_daily(100.0, 100.0, 100.0, 100.0) == 0.0


def test_range_estimators_reject_nonpositive_prices() -> None:
    with pytest.raises(ValueError, match="Parkinson"):
        parkinson_daily(100.0, 0.0)
    with pytest.raises(ValueError, match="Garman-Klass"):
        garman_klass_daily(100.0, 101.0, 0.0, 100.0)


def test_range_variance_uses_same_30c_window() -> None:
    origin = date(2024, 1, 2)
    daily = [(origin + timedelta(days=index), 0.002) for index in range(1, 40)]
    rvar = realized_range_variance_30c(
        origin, daily, last_available=origin + timedelta(days=40)
    )
    expected = (365 / 30) * 30 * 0.002
    assert rvar is not None
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)


def test_range_variance_21t_takes_next_21() -> None:
    origin = date(2024, 1, 2)
    daily = [(origin + timedelta(days=index), 0.003) for index in range(1, 30)]
    rvar = realized_range_variance_21t(origin, daily)
    expected = (252 / 21) * 21 * 0.003
    assert rvar is not None
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)
