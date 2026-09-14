import math
from datetime import date, timedelta

import pytest

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
    origin = date(2024, 1, 2)
    assert primary_horizon_end(origin) == date(2024, 2, 1)
    assert primary_horizon_end(date(2025, 12, 31)) == date(2026, 1, 30)


def test_rvar_30c_exact_construction() -> None:
    origin = date(2024, 1, 2)
    pairs = [(origin + timedelta(days=index), 0.01) for index in range(1, 40)]
    rvar = realized_variance_30c(origin, pairs, last_available=origin + timedelta(days=40))
    selected = [ret for day, ret in pairs if origin < day <= origin + timedelta(days=30)]
    assert len(selected) == 30
    expected = (365 / 30) * sum(ret * ret for ret in selected)
    assert rvar is not None
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(rvar, (365 / 30) * 30 * 0.0001, rel_tol=0, abs_tol=1e-12)


def test_rvar_30c_excludes_origin_date_and_day_31() -> None:
    origin = date(2024, 1, 2)
    pairs = [
        (date(2024, 1, 2), 0.50),
        (date(2024, 1, 3), 0.01),
        (date(2024, 2, 1), 0.02),
        (date(2024, 2, 2), 0.40),
    ]
    rvar = realized_variance_30c(origin, pairs, last_available=date(2024, 2, 2))
    expected = (365 / 30) * (0.01**2 + 0.02**2)
    assert rvar is not None
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)


def test_rvar_30c_incomplete_calendar_is_missing() -> None:
    origin = date(2024, 1, 2)
    pairs = [(date(2024, 1, 3), 0.01)]
    assert realized_variance_30c(origin, pairs, last_available=date(2024, 1, 10)) is None
    assert select_forward_30c(origin, pairs, last_available=date(2024, 1, 10)) is None


def test_rvar_30c_never_shortens_end_of_sample() -> None:
    origin = date(2025, 12, 31)
    pairs = [(date(2026, 1, 2), 0.01), (date(2026, 1, 15), 0.01)]
    assert realized_variance_30c(origin, pairs, last_available=date(2026, 1, 15)) is None
    complete = [(date(2026, 1, 2), 0.01), (date(2026, 1, 30), 0.02)]
    rvar = realized_variance_30c(origin, complete, last_available=date(2026, 1, 30))
    assert rvar is not None
    assert math.isclose(rvar, (365 / 30) * (0.01**2 + 0.02**2), rel_tol=0, abs_tol=1e-12)


def test_rvar_30c_session_count_may_vary() -> None:
    origin = date(2024, 1, 5)  # Friday
    weekday_pairs = []
    cursor = origin + timedelta(days=1)
    while cursor <= origin + timedelta(days=30):
        if cursor.weekday() < 5:
            weekday_pairs.append((cursor, 0.01))
        cursor += timedelta(days=1)
    rvar = realized_variance_30c(
        origin, weekday_pairs, last_available=origin + timedelta(days=30)
    )
    assert rvar is not None
    assert len(weekday_pairs) < 30
    expected = (365 / 30) * len(weekday_pairs) * 0.0001
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)


def test_rvar_21t_uses_next_21_trading_returns_only() -> None:
    origin = date(2024, 1, 2)
    pairs = [(origin + timedelta(days=index), float(index) / 100.0) for index in range(1, 30)]
    rvar = realized_variance_21t(origin, pairs)
    window = [ret for _, ret in pairs[:21]]
    expected = (252 / 21) * sum(ret * ret for ret in window)
    assert rvar is not None
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)
    assert select_forward_21t(origin, pairs) == window


def test_rvar_21t_incomplete_window_is_missing() -> None:
    origin = date(2024, 1, 2)
    pairs = [(origin + timedelta(days=index), 0.01) for index in range(1, 21)]
    assert realized_variance_21t(origin, pairs) is None


def test_rvar_21t_excludes_origin_session() -> None:
    origin = date(2024, 1, 2)
    pairs = [(origin, 0.9)] + [
        (origin + timedelta(days=index), 0.01) for index in range(1, 22)
    ]
    rvar = realized_variance_21t(origin, pairs)
    expected = (252 / 21) * 21 * (0.01**2)
    assert rvar is not None
    assert math.isclose(rvar, expected, rel_tol=0, abs_tol=1e-12)


def test_realized_volatility_is_sqrt() -> None:
    assert math.isclose(realized_volatility(0.04), 0.2, rel_tol=0, abs_tol=1e-12)


def test_forecast_origin_cutoff() -> None:
    assert_forecast_origin_allowed(date(2025, 12, 31))
    assert_forecast_origin_allowed(date(1990, 1, 2))
    with pytest.raises(ValueError, match="2025-12-31"):
        assert_forecast_origin_allowed(date(2026, 1, 2))
    with pytest.raises(ValueError, match="1990-01-02"):
        assert_forecast_origin_allowed(date(1989, 12, 31))
