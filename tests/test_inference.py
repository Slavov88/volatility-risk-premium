import math
from datetime import date, timedelta

import pytest

from vrp.config import CONVENTIONS
from vrp.inference import newey_west_mean, overlap_l0


def test_hac_mean_constant_series() -> None:
    stats = newey_west_mean([1.0, 1.0, 1.0, 1.0], maxlags=1)
    assert stats["mean"] == 1.0
    assert stats["standard_error"] == 0.0
    assert math.isinf(stats["t_statistic"])
    assert stats["n_obs"] == 4.0
    assert stats["maxlags"] == 1.0


def test_hac_mean_known_autocorrelated_fixture() -> None:
    stats = newey_west_mean([1.0, 1.0, 2.0, 2.0], maxlags=1)
    assert math.isclose(stats["mean"], 1.5, rel_tol=0, abs_tol=0.0)
    # gamma0 = 0.25, gamma1 = 0.0625, Bartlett weight = 1/2
    # HAC = 0.25 + 2*(1/2)*0.0625 = 0.3125; se = sqrt(0.3125 / 4)
    expected_se = math.sqrt(0.078125)
    assert math.isclose(stats["standard_error"], expected_se, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(stats["t_statistic"], 1.5 / expected_se, rel_tol=0, abs_tol=1e-12)


def test_hac_mean_iid_three_observations_maxlags_zero() -> None:
    stats = newey_west_mean([1.0, 2.0, 3.0], maxlags=0)
    assert math.isclose(stats["mean"], 2.0, rel_tol=0, abs_tol=0.0)
    # residuals -1,0,1; gamma0 = 2/3; se = sqrt((2/3)/3) = sqrt(2/9)
    expected_se = math.sqrt(2.0 / 9.0)
    assert math.isclose(stats["standard_error"], expected_se, rel_tol=0, abs_tol=1e-15)


def test_hac_rejects_empty_and_negative_lags() -> None:
    with pytest.raises(ValueError, match="observations"):
        newey_west_mean([], maxlags=0)
    with pytest.raises(ValueError, match="maxlags"):
        newey_west_mean([1.0], maxlags=-1)


def test_overlap_l0_daily_origins() -> None:
    origins = [date(2024, 1, 1) + timedelta(days=index) for index in range(40)]
    assert overlap_l0(origins, origins) == 29
    assert CONVENTIONS.primary_calendar_days == 30


def test_overlap_l0_nonoverlapping_origins() -> None:
    origins = [date(2024, 1, 1), date(2024, 2, 1)]
    trading = [date(2024, 1, 1) + timedelta(days=index) for index in range(70)]
    assert overlap_l0(origins, trading) == 0


def test_fixed_21_hac_lag_is_protocol_constant() -> None:
    assert CONVENTIONS.fixed_21_hac_maxlags == 20
