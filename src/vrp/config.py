"""Central scientific conventions locked before empirical analysis.

Internal volatility values are annualized decimals. For example, 0.20 means
20 percent annualized volatility. Internal variance is the square of decimal
volatility, and the empirical sign is always implied minus realized variance.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScientificConventions:
    """Units and horizons shared by code and paper."""

    trading_days_per_year: int = 252
    primary_calendar_days: int = 30
    primary_calendar_annualization_days: int = 365
    robustness_trading_days: int = 21
    robustness_trading_day_sensitivities: tuple[int, int] = (20, 22)
    fixed_21_hac_maxlags: int = 20
    percent_scale: float = 100.0
    risk_free_series: str = "USTREASURY_BC_3MONTH"
    empirical_sign_convention: str = "implied_variance_minus_realized_variance"
    horizon_decision_status: str = "locked-2026-08-10"

    def validate(self) -> None:
        """Raise if a convention is internally inconsistent."""

        if self.trading_days_per_year <= 0:
            raise ValueError("trading_days_per_year must be positive")
        if not 1 <= self.robustness_trading_days < self.trading_days_per_year:
            raise ValueError("robustness_trading_days must be within one year")
        if self.primary_calendar_days <= 0:
            raise ValueError("primary_calendar_days must be positive")
        if self.primary_calendar_annualization_days != 365:
            raise ValueError("primary calendar annualization must remain 365 days")
        if self.robustness_trading_day_sensitivities != (20, 22):
            raise ValueError("robustness sensitivities must remain (20, 22)")
        if self.fixed_21_hac_maxlags != self.robustness_trading_days - 1:
            raise ValueError("fixed-21 HAC maxlags must remain 20")
        if self.percent_scale != 100.0:
            raise ValueError("percent_scale must remain 100 for percent display")
        if self.empirical_sign_convention != "implied_variance_minus_realized_variance":
            raise ValueError("empirical sign convention must remain implied minus realized")


CONVENTIONS = ScientificConventions()
CONVENTIONS.validate()
