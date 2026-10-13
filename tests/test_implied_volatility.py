"""Track A implied-volatility inversion: recovery, bounds, and diagnostics.

These tests invert a single European Black--Scholes price. The recovered
volatility is never interchangeable with the Cboe VIX or with
``IVAR = (VIX / 100)^2``.
"""

from __future__ import annotations

import math
from itertools import product

import pytest

from black_scholes import (
    IV_SEARCH_CAP,
    IV_SEARCH_FLOOR,
    ImpliedVolatilityError,
    black_scholes_price,
    implied_volatility,
)

ABS_TOL = 1e-10
REPRICE_TOL = 1e-10

ATM = dict(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    rate=0.05,
)

RECOVERY_GRID = tuple(
    product(
        (90.0, 100.0, 110.0),
        (90.0, 100.0, 110.0),
        (0.25, 1.0),
        (0.0, 0.05),
        (0.15, 0.20, 0.40, 1.20),
        ("call", "put"),
        (0.0, 0.02),
    )
)

HIGH_VOL_SPECS = (
    dict(spot=100.0, strike=100.0, time_to_maturity=1.0, rate=0.05, volatility=4.0, dividend_yield=0.0),
    dict(spot=50.0, strike=150.0, time_to_maturity=0.5, rate=0.01, volatility=5.0, dividend_yield=0.0),
    dict(spot=90.0, strike=100.0, time_to_maturity=2.0, rate=-0.01, volatility=3.0, dividend_yield=0.02),
)


def _price(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> float:
    return black_scholes_price(
        spot,
        strike,
        time_to_maturity,
        rate,
        volatility,
        option_type,  # type: ignore[arg-type]
        dividend_yield=dividend_yield,
    )


def _implied_vol(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    price: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> float:
    return implied_volatility(
        spot,
        strike,
        time_to_maturity,
        rate,
        price,
        option_type,  # type: ignore[arg-type]
        dividend_yield=dividend_yield,
    )


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _independent_price(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> float:
    vol_sqrt_tau = volatility * math.sqrt(time_to_maturity)
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * time_to_maturity
    ) / vol_sqrt_tau
    d2 = d1 - vol_sqrt_tau
    discounted_spot = spot * math.exp(-dividend_yield * time_to_maturity)
    discounted_strike = strike * math.exp(-rate * time_to_maturity)
    if option_type == "call":
        return discounted_spot * _norm_cdf(d1) - discounted_strike * _norm_cdf(d2)
    return discounted_strike * _norm_cdf(-d2) - discounted_spot * _norm_cdf(-d1)


# ---------------------------------------------------------------------------
# Synthetic-price recovery
# ---------------------------------------------------------------------------


def test_recovers_atm_call_and_put_from_synthetic_prices() -> None:
    for option_type in ("call", "put"):
        true_vol = 0.20
        price = _price(**ATM, volatility=true_vol, option_type=option_type)
        recovered = _implied_vol(**ATM, price=price, option_type=option_type)
        assert math.isclose(recovered, true_vol, rel_tol=0, abs_tol=ABS_TOL)
        assert recovered != true_vol * 100.0


def test_recovers_hull_textbook_european_call() -> None:
    args = dict(spot=42.0, strike=40.0, time_to_maturity=0.5, rate=0.10)
    price = _price(**args, volatility=0.20, option_type="call")
    recovered = _implied_vol(**args, price=price, option_type="call")
    assert math.isclose(recovered, 0.20, rel_tol=0, abs_tol=ABS_TOL)


def test_recovers_independent_erf_formula_price() -> None:
    args = dict(spot=100.0, strike=95.0, time_to_maturity=0.75, rate=0.03)
    true_vol = 0.25
    price = _independent_price(**args, volatility=true_vol, option_type="call", dividend_yield=0.01)
    recovered = _implied_vol(**args, price=price, option_type="call", dividend_yield=0.01)
    assert math.isclose(recovered, true_vol, rel_tol=0, abs_tol=1e-8)


@pytest.mark.parametrize(
    "spot, strike, tau, rate, sigma, option_type, dividend_yield",
    RECOVERY_GRID,
)
def test_recovers_true_volatility_on_identifiable_grid(
    spot: float,
    strike: float,
    tau: float,
    rate: float,
    sigma: float,
    option_type: str,
    dividend_yield: float,
) -> None:
    price = _price(spot, strike, tau, rate, sigma, option_type, dividend_yield)
    recovered = _implied_vol(spot, strike, tau, rate, price, option_type, dividend_yield)
    scale = max(1.0, abs(spot), abs(strike))
    fitted = _price(spot, strike, tau, rate, recovered, option_type, dividend_yield)

    assert math.isfinite(recovered)
    assert recovered > 0.0
    assert math.isclose(recovered, sigma, rel_tol=1e-6, abs_tol=1e-7)
    assert math.isclose(fitted, price, rel_tol=0, abs_tol=REPRICE_TOL * scale)


@pytest.mark.parametrize("spec", HIGH_VOL_SPECS)
@pytest.mark.parametrize("option_type", ["call", "put"])
def test_bracket_expansion_recovers_volatilities_above_initial_high(
    spec: dict[str, float],
    option_type: str,
) -> None:
    true_vol = spec["volatility"]
    assert true_vol > 1.0
    price = _price(
        spec["spot"],
        spec["strike"],
        spec["time_to_maturity"],
        spec["rate"],
        true_vol,
        option_type,
        spec["dividend_yield"],
    )
    recovered = _implied_vol(
        spec["spot"],
        spec["strike"],
        spec["time_to_maturity"],
        spec["rate"],
        price,
        option_type,
        spec["dividend_yield"],
    )
    assert math.isclose(recovered, true_vol, rel_tol=1e-8, abs_tol=1e-8)


def test_call_and_put_linked_by_parity_share_the_same_implied_vol() -> None:
    spot, strike, tau, rate, q, sigma = 110.0, 100.0, 0.75, 0.03, 0.02, 0.25
    call = _price(spot, strike, tau, rate, sigma, "call", q)
    put = _price(spot, strike, tau, rate, sigma, "put", q)
    call_iv = _implied_vol(spot, strike, tau, rate, call, "call", q)
    put_iv = _implied_vol(spot, strike, tau, rate, put, "put", q)
    assert math.isclose(call_iv, put_iv, rel_tol=0, abs_tol=ABS_TOL)
    assert math.isclose(call_iv, sigma, rel_tol=0, abs_tol=ABS_TOL)


def test_nearby_identifiable_prices_map_to_nearby_implied_vols() -> None:
    base_price = _price(**ATM, volatility=0.20, option_type="call")
    bumped_price = _price(**ATM, volatility=0.21, option_type="call")
    iv_low = _implied_vol(**ATM, price=base_price, option_type="call")
    iv_high = _implied_vol(**ATM, price=bumped_price, option_type="call")
    assert iv_high > iv_low
    assert math.isclose(iv_high - iv_low, 0.01, rel_tol=0, abs_tol=1e-8)


def test_low_vega_quote_is_inverted_instead_of_accepting_nearby_endpoint() -> None:
    args = dict(spot=1.0, strike=100.0, time_to_maturity=0.5, rate=0.05)
    true_vol = 1.02
    price = _price(**args, volatility=true_vol, option_type="call")
    recovered = _implied_vol(**args, price=price, option_type="call")

    assert recovered != 1.0
    assert math.isclose(recovered, true_vol, rel_tol=0, abs_tol=1e-10)


def test_very_short_maturity_quote_uses_strict_brent_bracket() -> None:
    args = dict(spot=100.0, strike=100.0, time_to_maturity=1e-20, rate=0.0)
    true_vol = 1.02
    price = _price(**args, volatility=true_vol, option_type="call")
    recovered = _implied_vol(**args, price=price, option_type="call")

    assert recovered != 1.0
    assert math.isclose(recovered, true_vol, rel_tol=0, abs_tol=1e-5)


def test_search_floor_and_cap_are_strictly_positive_and_ordered() -> None:
    assert IV_SEARCH_FLOOR > 0.0
    assert IV_SEARCH_CAP > IV_SEARCH_FLOOR
    assert IV_SEARCH_CAP >= 5.0


# ---------------------------------------------------------------------------
# Economically admissible bounds
# ---------------------------------------------------------------------------


def test_call_price_below_intrinsic_is_rejected() -> None:
    spot, strike, tau, rate = 120.0, 100.0, 1.0, 0.05
    lower = spot - strike * math.exp(-rate * tau)
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, lower - 0.01, "call")
    assert exc.value.code == "price_below_intrinsic"


def test_put_price_below_intrinsic_is_rejected() -> None:
    spot, strike, tau, rate = 80.0, 100.0, 1.0, 0.05
    lower = strike * math.exp(-rate * tau) - spot
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, lower - 0.01, "put")
    assert exc.value.code == "price_below_intrinsic"


def test_negative_price_is_rejected_as_below_intrinsic() -> None:
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(100.0, 100.0, 1.0, 0.05, -0.01, "call")
    assert exc.value.code == "price_below_intrinsic"


def test_call_price_above_discounted_spot_is_rejected() -> None:
    spot, strike, tau, rate = 100.0, 100.0, 1.0, 0.05
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, spot + 0.01, "call")
    assert exc.value.code == "price_above_upper_bound"


def test_put_price_above_discounted_strike_is_rejected() -> None:
    spot, strike, tau, rate = 100.0, 90.0, 0.5, 0.04
    upper = strike * math.exp(-rate * tau)
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, upper + 0.01, "put")
    assert exc.value.code == "price_above_upper_bound"


def test_dividend_yield_tightens_the_call_upper_bound() -> None:
    spot, strike, tau, rate, q = 100.0, 100.0, 1.0, 0.05, 0.03
    upper = spot * math.exp(-q * tau)
    assert upper < spot
    mid = 0.5 * (upper + spot)
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, mid, "call", dividend_yield=q)
    assert exc.value.code == "price_above_upper_bound"


def test_price_at_call_intrinsic_fails_explicitly() -> None:
    spot, strike, tau, rate = 120.0, 100.0, 1.0, 0.05
    lower = spot - strike * math.exp(-rate * tau)
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, lower, "call")
    assert exc.value.code == "no_bracket"


def test_zero_otm_price_fails_explicitly() -> None:
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(80.0, 120.0, 0.25, 0.0, 0.0, "call")
    assert exc.value.code == "no_bracket"


def test_unidentifiable_synthetic_deep_otm_price_fails_explicitly() -> None:
    """Deep OTM low-vol time value underflows; inversion must not invent a vol."""

    spot, strike, tau, rate, sigma = 1.0, 1e6, 0.01, 0.0, 0.01
    price = _price(spot, strike, tau, rate, sigma, "call")
    assert math.isclose(price, 0.0, rel_tol=0, abs_tol=1e-12)
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, price, "call")
    assert exc.value.code == "no_bracket"


def test_price_at_call_upper_bound_fails_explicitly() -> None:
    spot, strike, tau, rate = 100.0, 90.0, 1.0, 0.04
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, spot, "call")
    assert exc.value.code == "no_bracket"


def test_price_between_cap_model_and_upper_bound_is_not_bracketed() -> None:
    spot, strike, tau, rate = 100.0, 100.0, 1e-6, 0.0
    price_at_cap = _price(spot, strike, tau, rate, IV_SEARCH_CAP, "call")
    upper = spot
    assert price_at_cap < upper - 1.0
    quote = 0.5 * (price_at_cap + upper)
    with pytest.raises(ImpliedVolatilityError) as exc:
        _implied_vol(spot, strike, tau, rate, quote, "call")
    assert exc.value.code == "no_bracket"
    assert "search interval" in str(exc.value)


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"rate": -1000.0}, "overflowing discounted value"),
        ({"dividend_yield": -1000.0}, "overflowing discounted value"),
        (
            {"spot": 1e308, "dividend_yield": -1.0},
            "non-finite discounted value",
        ),
    ],
)
def test_extreme_finite_discount_inputs_raise_stable_diagnostic(
    kwargs: dict[str, float],
    fragment: str,
) -> None:
    arguments = {
        "spot": 100.0,
        "strike": 100.0,
        "time_to_maturity": 1.0,
        "rate": 0.05,
        "price": 10.0,
        "option_type": "call",
    }
    arguments.update(kwargs)
    with pytest.raises(ImpliedVolatilityError) as exc:
        implied_volatility(**arguments)  # type: ignore[arg-type]
    assert exc.value.code == "invalid_input"
    assert fragment in str(exc.value)


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"spot": 0.0}, "spot"),
        ({"spot": -1.0}, "spot"),
        ({"strike": 0.0}, "strike"),
        ({"time_to_maturity": 0.0}, "time_to_maturity"),
        ({"spot": math.nan}, "spot"),
        ({"rate": math.inf}, "rate"),
        ({"price": math.nan}, "price"),
        ({"dividend_yield": math.nan}, "dividend_yield"),
        ({"option_type": "Call"}, "option_type"),
        ({"option_type": "european_call"}, "option_type"),
    ],
)
def test_invalid_inputs_raise_invalid_input_diagnostic(
    kwargs: dict[str, object],
    fragment: str,
) -> None:
    arguments: dict[str, object] = {
        "spot": 100.0,
        "strike": 100.0,
        "time_to_maturity": 1.0,
        "rate": 0.05,
        "price": 10.0,
        "option_type": "call",
    }
    arguments.update(kwargs)
    with pytest.raises(ImpliedVolatilityError) as exc:
        implied_volatility(**arguments)  # type: ignore[arg-type]
    assert exc.value.code == "invalid_input"
    assert fragment in str(exc.value)
