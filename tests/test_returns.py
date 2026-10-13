import math
from datetime import date

import pytest

from vrp.returns import log_returns


def test_known_log_return_values() -> None:
    dates = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    closes = [100.0, 100.0 * math.exp(0.01), 100.0 * math.exp(0.02)]
    pairs = log_returns(dates, closes)
    assert pairs[0] == (date(2024, 1, 3), pytest.approx(0.01, abs=1e-12))
    assert pairs[1][0] == date(2024, 1, 4)
    assert math.isclose(pairs[1][1], 0.01, rel_tol=0, abs_tol=1e-12)


def test_weekend_gap_is_valid_when_sessions_are_consecutive() -> None:
    pairs = log_returns(
        [date(2024, 1, 5), date(2024, 1, 8)],
        [100.0, 101.0],
    )
    assert pairs[0][0] == date(2024, 1, 8)


def test_exchange_holiday_gap_is_valid() -> None:
    pairs = log_returns(
        [date(2024, 7, 3), date(2024, 7, 5)],
        [100.0, 101.0],
    )
    assert pairs[0][0] == date(2024, 7, 5)


def test_missing_exchange_session_is_rejected() -> None:
    with pytest.raises(ValueError, match="not consecutive exchange sessions"):
        log_returns(
            [date(2024, 1, 2), date(2024, 1, 4)],
            [100.0, 101.0],
        )


@pytest.mark.parametrize(
    "dates",
    [
        [date(2024, 1, 3), date(2024, 1, 2)],
        [date(2024, 1, 2), date(2024, 1, 2)],
    ],
)
def test_unsorted_or_duplicate_dates_are_rejected(dates) -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        log_returns(dates, [100.0, 101.0])


def test_log_returns_reject_nonfinite_or_nonpositive_closes() -> None:
    for bad in [0.0, float("nan"), float("inf")]:
        with pytest.raises(ValueError, match="finite, strictly positive"):
            log_returns(
                [date(2024, 1, 2), date(2024, 1, 3)],
                [100.0, bad],
            )


def test_log_returns_require_aligned_inputs() -> None:
    with pytest.raises(ValueError, match="same length"):
        log_returns([date(2024, 1, 2)], [100.0, 101.0])
