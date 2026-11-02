"""Check the manuscript's European prices, six fixed quotes and variance strip.

Run with the repository src directory on PYTHONPATH. The integration uses
log-strike quadrature with finite limits checked against the known diffusion
variance. These model checks do not use Track B return data.
"""
import json
import math
import platform

import scipy
from scipy.integrate import quad
from scipy.special import ndtr

from black_scholes import black_scholes_price
from vrp.option_validation import REFERENCE_CASES, market_quote_validation_rows


def normal_payoff(case):
    """Discount and integrate the terminal payoff over the Gaussian shock."""
    tau = case.time_to_maturity
    signed = 1 if case.option_type == 'call' else -1
    log_mean = math.log(case.spot) + (case.rate - case.dividend_yield
                                      - case.volatility**2 / 2) * tau
    spread = case.volatility * math.sqrt(tau)
    critical = (math.log(case.strike) - log_mean) / spread
    bounds = (critical, 12) if signed == 1 else (-12, critical)

    def payoff(z):
        spot = math.exp(log_mean + spread * z)
        return signed * (spot - case.strike) * math.exp(-z*z/2) / math.sqrt(2*math.pi)

    return math.exp(-case.rate * tau) * quad(payoff, *bounds, epsabs=1e-13)[0]


def strip_rate(volatility, tau):
    """Integrate discounted put/call prices divided by squared strike."""
    spot, rate, dividend_yield = 100, 0.05, 0.02
    forward = spot * math.exp((rate - dividend_yield) * tau)
    spread = volatility * math.sqrt(tau)

    def integrand(x):
        strike = forward * math.exp(x)
        d1 = -x / spread + spread / 2
        d2 = d1 - spread
        sign = -1 if x < 0 else 1
        price = math.exp(-rate*tau) * sign * (
            forward * ndtr(sign*d1) - strike * ndtr(sign*d2))
        return price / strike  # dK = K dx

    extent = 12 * spread + spread**2
    strip = quad(integrand, -extent, 0)[0] + quad(integrand, 0, extent)[0]
    return 2 * math.exp(rate*tau) * strip / tau


def main():
    errors = []
    for case in REFERENCE_CASES:
        computed = black_scholes_price(case.spot, case.strike, case.time_to_maturity,
                                        case.rate, case.volatility, case.option_type,
                                        dividend_yield=case.dividend_yield)
        errors.append(abs(computed - normal_payoff(case)))
    strip_errors = [abs(strip_rate(vol, tau) - vol**2)
                    for vol in (0.12, 0.30, 0.60) for tau in (30/365, 1)]
    quotes = market_quote_validation_rows()
    result = {
        "python": platform.python_version(),
        "scipy": scipy.__version__,
        "payoff_quadrature_cases": len(errors),
        "maximum_absolute_price_error": max(errors),
        "strip_quadrature_cases": len(strip_errors),
        "maximum_absolute_annualized_variance_error": max(strip_errors),
        "fixed_quotes_in_spread": sum(row["inside_bid_ask"] for row in quotes),
        "fixed_quotes": len(quotes),
        "maximum_quoted_iv_absolute_error": max(row["iv_abs_error"] for row in quotes),
    }
    assert max(errors) < 1e-10 and max(strip_errors) < 1e-10
    assert result["fixed_quotes_in_spread"] == result["fixed_quotes"] == 6
    assert result["maximum_quoted_iv_absolute_error"] < 1e-6
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
