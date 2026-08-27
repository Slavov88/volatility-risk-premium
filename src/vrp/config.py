"""Central scientific conventions locked before empirical analysis.

The authoritative substantive specification is ``paper/method_protocol.md``
locked on 2026-08-26, with a technical sample-tail amendment dated 2026-08-27.
Internal volatility values are annualized decimals and internal variance values
are the square of decimal volatility. The empirical sign is always implied
minus realized.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ScientificConventions:
    """Units, horizons, inference, sample boundaries, and forecast constants."""

    protocol_version: str = "1.0.1"
    protocol_decision_date: str = "2026-08-26"
    protocol_amendment_date: str = "2026-08-27"

    # These dates govern forecast-origin eligibility, not availability of
    # post-origin outcome data needed to realize the final targets.
    sample_start: str = "1990-01-02"
    sample_end: str = "2025-12-31"
    spx_target_support_end_exclusive: str = "2026-02-03"

    trading_days_per_year: int = 252
    calendar_days_per_year: int = 365
    primary_calendar_days: int = 30
    primary_calendar_annualization_days: int = 365
    robustness_trading_days: int = 21

    primary_horizon: str = "30_calendar_days"
    robustness_horizon: str = "21_trading_days"
    primary_empirical_object: str = "implied_variance_minus_realized_variance"
    secondary_empirical_object: str = "implied_volatility_minus_realized_volatility"
    empirical_sign_convention: str = "implied_minus_realized"

    primary_hac_rule: str = "derive_L0_from_calendar_target_overlap"
    primary_hac_sensitivity_maxlags: tuple[int, int] = (42, 63)
    fixed_21_hac_maxlags: int = 20
    fixed_21_hac_sensitivity_maxlags: tuple[int, int, int] = (10, 21, 42)

    significance_level: float = 0.05
    confidence_level: float = 0.95
    test_direction: str = "two_sided"

    garch_model: str = "GARCH(1,1)"
    garch_mean: str = "constant"
    garch_primary_distribution: str = "normal"
    garch_robustness_distribution: str = "student_t"
    garch_primary_window: str = "expanding"
    garch_robustness_window_years: int = 5

    oos_initial_estimation_end_year: int = 2006
    oos_start_year: int = 2007
    formal_regime_chronology: str = "NBER_monthly_business_cycle"

    percent_scale: float = 100.0
    random_seed: int = 42

    def validate(self) -> None:
        """Raise if any locked convention drifts from the protocol."""

        if self.protocol_version != "1.0.1":
            raise ValueError("protocol_version must remain 1.0.1")
        if self.protocol_decision_date != "2026-08-26":
            raise ValueError("protocol_decision_date must remain 2026-08-26")
        if self.protocol_amendment_date != "2026-08-27":
            raise ValueError("protocol_amendment_date must remain 2026-08-27")

        if self.sample_start != "1990-01-02":
            raise ValueError("sample_start must remain 1990-01-02")
        if self.sample_end != "2025-12-31":
            raise ValueError("forecast-origin sample_end must remain 2025-12-31")
        if self.spx_target_support_end_exclusive != "2026-02-03":
            raise ValueError(
                "S&P target-support acquisition end must remain exclusive 2026-02-03"
            )

        start = date.fromisoformat(self.sample_start)
        end = date.fromisoformat(self.sample_end)
        support_end_exclusive = date.fromisoformat(self.spx_target_support_end_exclusive)
        if start >= end:
            raise ValueError("sample_start must precede sample_end")
        if support_end_exclusive <= end:
            raise ValueError("target-support end must lie after the forecast-origin sample")

        if self.trading_days_per_year != 252:
            raise ValueError("trading_days_per_year must remain 252")
        if self.calendar_days_per_year != 365:
            raise ValueError("calendar_days_per_year must remain 365")
        if self.primary_calendar_days != 30:
            raise ValueError("primary horizon must remain 30 calendar days")
        if self.primary_calendar_annualization_days != 365:
            raise ValueError("primary calendar annualization must remain 365")
        if self.robustness_trading_days != 21:
            raise ValueError("mandatory robustness horizon must remain 21 trading days")
        if self.fixed_21_hac_maxlags != self.robustness_trading_days - 1:
            raise ValueError("fixed-21 HAC maxlags must remain 20")

        if self.primary_horizon != "30_calendar_days":
            raise ValueError("primary_horizon must remain 30_calendar_days")
        if self.robustness_horizon != "21_trading_days":
            raise ValueError("robustness_horizon must remain 21_trading_days")
        if self.primary_empirical_object != "implied_variance_minus_realized_variance":
            raise ValueError("primary empirical object must remain variance-space VRP proxy")
        if self.secondary_empirical_object != "implied_volatility_minus_realized_volatility":
            raise ValueError("secondary empirical object must remain volatility gap")
        if self.empirical_sign_convention != "implied_minus_realized":
            raise ValueError("empirical sign convention must remain implied minus realized")

        if self.primary_hac_rule != "derive_L0_from_calendar_target_overlap":
            raise ValueError("primary HAC lag must be derived from calendar-target overlap")
        if self.primary_hac_sensitivity_maxlags != (42, 63):
            raise ValueError("primary HAC sensitivities must remain (42, 63)")
        if self.fixed_21_hac_sensitivity_maxlags != (10, 21, 42):
            raise ValueError("fixed-21 HAC sensitivities must remain (10, 21, 42)")

        if self.significance_level != 0.05:
            raise ValueError("significance_level must remain 0.05")
        if self.confidence_level != 0.95:
            raise ValueError("confidence_level must remain 0.95")
        if self.test_direction != "two_sided":
            raise ValueError("confirmatory tests must remain two-sided")

        if self.garch_model != "GARCH(1,1)":
            raise ValueError("primary model must remain GARCH(1,1)")
        if self.garch_mean != "constant":
            raise ValueError("GARCH mean specification must remain constant")
        if self.garch_primary_distribution != "normal":
            raise ValueError("primary GARCH distribution must remain normal")
        if self.garch_robustness_distribution != "student_t":
            raise ValueError("GARCH robustness distribution must remain student_t")
        if self.garch_primary_window != "expanding":
            raise ValueError("primary GARCH estimation window must remain expanding")
        if self.garch_robustness_window_years != 5:
            raise ValueError("rolling-window robustness must remain five years")
        if self.oos_initial_estimation_end_year != 2006 or self.oos_start_year != 2007:
            raise ValueError("OOS design must remain train-through-2006/start-2007")
        if self.formal_regime_chronology != "NBER_monthly_business_cycle":
            raise ValueError("formal regime chronology must remain NBER monthly")

        if self.percent_scale != 100.0:
            raise ValueError("percent_scale must remain 100")
        if self.random_seed != 42:
            raise ValueError("random_seed must remain 42")


CONVENTIONS = ScientificConventions()
CONVENTIONS.validate()
