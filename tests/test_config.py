from dataclasses import FrozenInstanceError

import pytest

from vrp.config import CONVENTIONS, ScientificConventions


def test_default_conventions_are_explicit_and_valid() -> None:
    assert CONVENTIONS.trading_days_per_year == 252
    assert CONVENTIONS.primary_calendar_days == 30
    assert CONVENTIONS.primary_calendar_annualization_days == 365
    assert CONVENTIONS.robustness_trading_days == 21
    assert CONVENTIONS.robustness_trading_day_sensitivities == (20, 22)
    assert CONVENTIONS.fixed_21_hac_maxlags == 20
    assert CONVENTIONS.percent_scale == 100.0
    assert CONVENTIONS.empirical_sign_convention == (
        "implied_variance_minus_realized_variance"
    )
    assert CONVENTIONS.horizon_decision_status == "locked-2026-08-10"


def test_conventions_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        CONVENTIONS.robustness_trading_days = 20  # type: ignore[misc]


def test_invalid_horizon_is_rejected() -> None:
    conventions = ScientificConventions(robustness_trading_days=0)
    with pytest.raises(ValueError, match="robustness_trading_days"):
        conventions.validate()
