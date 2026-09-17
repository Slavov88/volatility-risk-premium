import math
from datetime import date, timedelta

import pytest

from vrp.evaluation import (
    common_evaluation_mask,
    estimation_window,
    naive_variance_21t,
    naive_variance_30c,
    out_of_sample_split,
)


def test_oos_split_trains_through_2006_and_evaluates_from_2007() -> None:
    sessions = [
        date(1990, 1, 2),
        date(2006, 12, 28),
        date(2006, 12, 29),
        date(2007, 1, 2),
        date(2007, 1, 3),
        date(2007, 2, 1),
        date(2007, 2, 2),
    ]
    split = out_of_sample_split(sessions)
    assert split.initial_estimation_dates == (
        date(1990, 1, 2),
        date(2006, 12, 28),
        date(2006, 12, 29),
    )
    assert split.initial_estimation_end == date(2006, 12, 29)
    assert split.evaluation_origins[:2] == (date(2007, 1, 2), date(2007, 1, 3))
    assert split.evaluation_start == date(2007, 1, 2)


def test_oos_split_requires_complete_target_and_never_uses_2026_as_origin() -> None:
    sessions = [
        date(2006, 12, 29),
        date(2025, 12, 30),
        date(2025, 12, 31),
        date(2026, 1, 29),
        date(2026, 1, 30),
        date(2026, 2, 2),
    ]
    split = out_of_sample_split(sessions)
    assert date(2025, 12, 30) in split.evaluation_origins
    assert date(2025, 12, 31) in split.evaluation_origins
    assert all(day.year <= 2025 for day in split.evaluation_origins)

    incomplete = out_of_sample_split(sessions[:-2])
    assert date(2025, 12, 31) not in incomplete.evaluation_origins


def test_expanding_and_rolling_windows_are_information_safe() -> None:
    origin = date(2012, 1, 3)
    values = [
        (date(1990, 1, 2), 0.01),
        (date(2007, 1, 3), 0.02),  # left endpoint: excluded from rolling
        (date(2007, 1, 4), 0.03),
        (origin, 0.04),
        (date(2012, 1, 4), 9.0),  # future: excluded from both
    ]
    expanding = estimation_window(origin, values, window="expanding")
    rolling = estimation_window(origin, values, window="rolling_5y")
    assert [day for day, _ in expanding] == [
        date(1990, 1, 2),
        date(2007, 1, 3),
        date(2007, 1, 4),
        origin,
    ]
    assert [day for day, _ in rolling] == [date(2007, 1, 4), origin]


def test_changing_future_return_cannot_change_windows_or_naive_forecast() -> None:
    origin = date(2012, 1, 31)
    history = [
        (origin - timedelta(days=31), 0.01),
        (origin - timedelta(days=20), 0.02),
        (origin, 0.03),
    ]
    first = history + [(origin + timedelta(days=1), 1.0)]
    second = history + [(origin + timedelta(days=1), -5.0)]
    assert estimation_window(origin, first) == estimation_window(origin, second)
    assert naive_variance_30c(origin, first) == naive_variance_30c(origin, second)


def test_naive_30c_exact_window_and_annualization() -> None:
    origin = date(2024, 2, 1)
    values = [
        (origin - timedelta(days=31), 0.50),
        (origin - timedelta(days=30), 0.40),  # excluded boundary
        (origin - timedelta(days=29), 0.01),
        (origin, 0.02),
        (origin + timedelta(days=1), 0.30),
    ]
    forecast = naive_variance_30c(origin, values)
    assert forecast is not None
    expected = (365 / 30) * (0.01**2 + 0.02**2)
    assert math.isclose(forecast, expected, rel_tol=0, abs_tol=1e-12)


def test_naive_30c_requires_complete_trailing_calendar_support() -> None:
    origin = date(2024, 2, 1)
    values = [(origin - timedelta(days=29), 0.01), (origin, 0.02)]
    assert naive_variance_30c(origin, values) is None


def test_naive_21t_uses_last_21_returns_through_origin() -> None:
    origin = date(2024, 2, 1)
    values = [
        (origin - timedelta(days=30 - index), (index + 1) / 100.0)
        for index in range(30)
    ]
    values.append((origin + timedelta(days=1), 5.0))
    forecast = naive_variance_21t(origin, values)
    selected = [value for _, value in values[:30]][-21:]
    expected = (252 / 21) * sum(value * value for value in selected)
    assert forecast is not None
    assert math.isclose(forecast, expected, rel_tol=0, abs_tol=1e-12)


def test_common_mask_is_one_intersection_for_all_three_models() -> None:
    origins = [date(2007, 1, 2), date(2007, 1, 3), date(2007, 1, 4)]
    target = {origins[0]: 0.01, origins[1]: 0.02, origins[2]: 0.03}
    forecasts = {
        "vix": {origins[0]: 0.01, origins[1]: 0.02, origins[2]: 0.03},
        "garch": {origins[0]: 0.01, origins[1]: None, origins[2]: 0.03},
        "naive": {origins[0]: 0.01, origins[1]: 0.02, origins[2]: float("nan")},
    }
    assert common_evaluation_mask(origins, target, forecasts) == (origins[0],)


def test_common_mask_requires_prespecified_models_and_valid_variances() -> None:
    origin = date(2007, 1, 2)
    target = {origin: 0.01}
    with pytest.raises(ValueError, match="exactly vix, garch, and naive"):
        common_evaluation_mask([origin], target, {"vix": {origin: 0.01}})

    forecasts = {
        "vix": {origin: 0.01},
        "garch": {origin: -0.01},
        "naive": {origin: 0.01},
    }
    with pytest.raises(ValueError, match="non-negative"):
        common_evaluation_mask([origin], target, forecasts)


def test_unknown_estimation_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="expanding"):
        estimation_window(
            date(2007, 1, 2),
            [(date(2006, 12, 29), 0.01)],
            window="selected_after_results",  # type: ignore[arg-type]
        )
