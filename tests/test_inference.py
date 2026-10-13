import math
from datetime import date

import numpy as np
import pytest
import statsmodels.api as sm

from vrp.calendar import exchange_sessions
from vrp.config import CONVENTIONS
from vrp.inference import fit_hac_ols, newey_west_mean, overlap_l0


def test_hac_mean_matches_statsmodels_fixture() -> None:
    values = np.array([1.0, 1.0, 2.0, 2.0, 3.0, 2.5])
    ours = newey_west_mean(values, maxlags=2)
    direct = sm.OLS(values, np.ones((len(values), 1))).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": 2, "use_correction": True},
        use_t=False,
    )
    assert math.isclose(ours["mean"], direct.params[0], abs_tol=1e-15)
    assert math.isclose(
        ours["standard_error"], direct.bse[0], rel_tol=1e-12
    )
    assert math.isclose(
        ours["t_statistic"], direct.tvalues[0], rel_tol=1e-12
    )


def test_hac_zero_mean_zero_variance_is_not_infinite() -> None:
    stats = newey_west_mean([0.0, 0.0, 0.0, 0.0], maxlags=1)
    assert stats["standard_error"] == 0.0
    assert stats["t_statistic"] == 0.0
    assert stats["p_value"] == 1.0


def test_hac_rejects_nonfinite_empty_and_negative_lags() -> None:
    with pytest.raises(ValueError, match="observations"):
        newey_west_mean([], maxlags=0)
    with pytest.raises(ValueError, match="maxlags"):
        newey_west_mean([1.0, 2.0], maxlags=-1)
    for bad in [float("nan"), float("inf")]:
        with pytest.raises(ValueError, match="finite"):
            newey_west_mean([1.0, bad], maxlags=0)


def test_regression_hac_utility_validates_and_fits() -> None:
    result = fit_hac_ols(
        [1.0, 2.0, 2.8, 4.2, 4.9],
        [[0.0], [1.0], [2.0], [3.0], [4.0]],
        maxlags=1,
    )
    assert len(result.params) == 2
    assert result.cov_type == "HAC"
    with pytest.raises(ValueError, match="finite"):
        fit_hac_ols(
            [1.0, 2.0, float("nan")],
            [[0.0], [1.0], [2.0]],
            maxlags=1,
        )


def test_overlap_l0_uses_expected_exchange_sessions() -> None:
    origins = exchange_sessions(date(2024, 1, 2), date(2024, 2, 15))
    l0 = overlap_l0(origins, origins)
    assert l0 > 0
    assert CONVENTIONS.primary_calendar_days == 30


def test_overlap_l0_sorts_origins_and_rejects_duplicates() -> None:
    origins = [date(2024, 2, 2), date(2024, 1, 2)]
    assert overlap_l0(origins, origins) == 0
    with pytest.raises(ValueError, match="unique"):
        overlap_l0(
            [date(2024, 1, 2), date(2024, 1, 2)],
            None,
        )


def test_fixed_21_hac_lag_is_protocol_constant() -> None:
    assert CONVENTIONS.fixed_21_hac_maxlags == 20


def test_hac_rejects_excessive_lags_and_rank_deficient_designs() -> None:
    with pytest.raises(ValueError, match="smaller than"):
        newey_west_mean([0.1, 0.2], maxlags=2)
    with pytest.raises(ValueError, match="smaller than"):
        fit_hac_ols([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], maxlags=3)
    with pytest.raises(ValueError, match="rank-deficient"):
        fit_hac_ols(
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [[1.0, 2.0], [2.0, 4.0], [3.0, 6.0], [4.0, 8.0], [5.0, 10.0]],
            maxlags=1,
        )
