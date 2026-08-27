from dataclasses import FrozenInstanceError

import pytest

from vrp.config import CONVENTIONS, ScientificConventions


def test_default_conventions_match_locked_protocol() -> None:
    assert CONVENTIONS.protocol_version == "1.0.1"
    assert CONVENTIONS.protocol_decision_date == "2026-08-26"
    assert CONVENTIONS.protocol_amendment_date == "2026-08-27"
    assert CONVENTIONS.sample_start == "1990-01-02"
    assert CONVENTIONS.sample_end == "2025-12-31"
    assert CONVENTIONS.spx_target_support_end_exclusive == "2026-02-03"

    assert CONVENTIONS.primary_horizon == "30_calendar_days"
    assert CONVENTIONS.primary_calendar_days == 30
    assert CONVENTIONS.primary_calendar_annualization_days == 365
    assert CONVENTIONS.robustness_horizon == "21_trading_days"
    assert CONVENTIONS.robustness_trading_days == 21
    assert CONVENTIONS.trading_days_per_year == 252

    assert CONVENTIONS.primary_empirical_object == (
        "implied_variance_minus_realized_variance"
    )
    assert CONVENTIONS.secondary_empirical_object == (
        "implied_volatility_minus_realized_volatility"
    )
    assert CONVENTIONS.empirical_sign_convention == "implied_minus_realized"

    assert CONVENTIONS.primary_hac_rule == "derive_L0_from_calendar_target_overlap"
    assert CONVENTIONS.primary_hac_sensitivity_maxlags == (42, 63)
    assert CONVENTIONS.fixed_21_hac_maxlags == 20
    assert CONVENTIONS.fixed_21_hac_sensitivity_maxlags == (10, 21, 42)

    assert CONVENTIONS.significance_level == 0.05
    assert CONVENTIONS.confidence_level == 0.95
    assert CONVENTIONS.test_direction == "two_sided"

    assert CONVENTIONS.garch_model == "GARCH(1,1)"
    assert CONVENTIONS.garch_mean == "constant"
    assert CONVENTIONS.garch_primary_distribution == "normal"
    assert CONVENTIONS.garch_robustness_distribution == "student_t"
    assert CONVENTIONS.garch_primary_window == "expanding"
    assert CONVENTIONS.garch_robustness_window_years == 5
    assert CONVENTIONS.oos_initial_estimation_end_year == 2006
    assert CONVENTIONS.oos_start_year == 2007
    assert CONVENTIONS.formal_regime_chronology == "NBER_monthly_business_cycle"


def test_conventions_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        CONVENTIONS.primary_calendar_days = 21  # type: ignore[misc]


def test_21_day_primary_horizon_is_rejected() -> None:
    conventions = ScientificConventions(primary_calendar_days=21)
    with pytest.raises(ValueError, match="30 calendar days"):
        conventions.validate()


def test_wrong_primary_empirical_object_is_rejected() -> None:
    conventions = ScientificConventions(
        primary_empirical_object="implied_volatility_minus_realized_volatility"
    )
    with pytest.raises(ValueError, match="variance-space"):
        conventions.validate()


def test_invalid_oos_design_is_rejected() -> None:
    conventions = ScientificConventions(oos_start_year=2008)
    with pytest.raises(ValueError, match="train-through-2006/start-2007"):
        conventions.validate()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"protocol_version": "1.0"}, "protocol_version"),
        ({"sample_start": "1990-01-03"}, "sample_start"),
        ({"sample_end": "2025-12-30"}, "sample_end"),
        ({"spx_target_support_end_exclusive": "2026-01-01"}, "target-support"),
        ({"significance_level": 0.10}, "significance_level"),
        ({"confidence_level": 0.90}, "confidence_level"),
        ({"garch_mean": "zero"}, "mean specification"),
        ({"garch_primary_distribution": "student_t"}, "primary GARCH distribution"),
        ({"garch_robustness_distribution": "normal"}, "robustness distribution"),
    ],
)
def test_locked_defaults_cannot_drift(kwargs: dict[str, object], message: str) -> None:
    conventions = ScientificConventions(**kwargs)
    with pytest.raises(ValueError, match=message):
        conventions.validate()
