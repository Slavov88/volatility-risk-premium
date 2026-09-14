import math
from datetime import date, timedelta

import pytest

from vrp.returns import log_returns


def test_known_log_return_values() -> None:
    dates = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    closes = [100.0, 100.0 * math.exp(0.01), 100.0 * math.exp(0.02)]
    pairs = log_returns(dates, closes)
    assert pairs[0] == (date(2024, 1, 3), pytest.approx(0.01, rel=0, abs=1e-12))
    assert pairs[1][0] == date(2024, 1, 4)
    assert math.isclose(pairs[1][1], 0.01, rel_tol=0, abs_tol=1e-12)


def test_log_return_of_110_over_100() -> None:
    dates = [date(2024, 1, 2), date(2024, 1, 3)]
    pairs = log_returns(dates, [100.0, 110.0])
    assert pairs == [(date(2024, 1, 3), pytest.approx(math.log(1.1), rel=0, abs=1e-15))]


def test_log_returns_reject_nonpositive_closes() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        log_returns([date(2024, 1, 2), date(2024, 1, 3)], [100.0, 0.0])


def test_log_returns_require_aligned_inputs() -> None:
    with pytest.raises(ValueError, match="same length"):
        log_returns([date(2024, 1, 2)], [100.0, 101.0])
