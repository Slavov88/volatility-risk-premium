"""Deterministic checks for the Track A Black--Scholes pricer."""

from __future__ import annotations

import math

import pytest
from scipy.special import ndtr

from black_scholes import black_scholes_price


ATM = dict(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    rate=0.05,
    volatility=0.20,
)


def _manual_core_price(option_type: str) -> float:
    """W2-02 no-dividend formula assembled independently of the pricer."""

    spot = ATM["spot"]
    strike = ATM["strike"]
    tau = ATM["time_to_maturity"]
    rate = ATM["rate"]
    sigma = ATM["volatility"]
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * tau) / (
        sigma * math.sqrt(tau)
    )
    d2 = d1 - sigma * math.sqrt(tau)
    discounted_strike = strike * math.exp(-rate * tau)
    if option_type == "call":
        return spot * ndtr(d1) - discounted_strike * ndtr(d2)
    return discounted_strike * ndtr(-d2) - spot * ndtr(-d1)


def test_atm_call_and_put_match_w2_02_formula() -> None:
    call = black_scholes_price(**ATM, option_type="call")
    put = black_scholes_price(**ATM, option_type="put")
    expected_call = _manual_core_price("call")
    expected_put = _manual_core_price("put")

    assert math.isclose(call, expected_call, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(put, expected_put, rel_tol=0, abs_tol=1e-12)
    # ATM with r=0.05, sigma=0.20, tau=1 gives d1=0.35 and d2=0.15 exactly.
    assert math.isclose(call, 10.450583572185565, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(put, 5.573526022256971, rel_tol=0, abs_tol=1e-12)


def test_put_call_parity_no_dividend() -> None:
    call = black_scholes_price(110.0, 100.0, 0.75, 0.03, 0.25, "call")
    put = black_scholes_price(110.0, 100.0, 0.75, 0.03, 0.25, "put")
    forward_diff = 110.0 - 100.0 * math.exp(-0.03 * 0.75)
    assert math.isclose(call - put, forward_diff, rel_tol=0, abs_tol=1e-12)


def test_put_call_parity_with_dividend_yield() -> None:
    q = 0.02
    call = black_scholes_price(
        110.0, 100.0, 0.75, 0.03, 0.25, "call", dividend_yield=q
    )
    put = black_scholes_price(
        110.0, 100.0, 0.75, 0.03, 0.25, "put", dividend_yield=q
    )
    forward_diff = 110.0 * math.exp(-q * 0.75) - 100.0 * math.exp(-0.03 * 0.75)
    assert math.isclose(call - put, forward_diff, rel_tol=0, abs_tol=1e-12)


def test_zero_dividend_yield_matches_core() -> None:
    core_call = black_scholes_price(**ATM, option_type="call")
    core_put = black_scholes_price(**ATM, option_type="put")
    q_call = black_scholes_price(**ATM, option_type="call", dividend_yield=0.0)
    q_put = black_scholes_price(**ATM, option_type="put", dividend_yield=0.0)
    assert core_call == q_call
    assert core_put == q_put


def test_dividend_yield_lowers_calls_and_raises_puts() -> None:
    call_core = black_scholes_price(**ATM, option_type="call")
    put_core = black_scholes_price(**ATM, option_type="put")
    call_q = black_scholes_price(**ATM, option_type="call", dividend_yield=0.03)
    put_q = black_scholes_price(**ATM, option_type="put", dividend_yield=0.03)
    assert call_q < call_core
    assert put_q > put_core


def test_price_is_strictly_increasing_in_volatility() -> None:
    vols = (0.10, 0.20, 0.35)
    calls = [black_scholes_price(100.0, 100.0, 1.0, 0.05, vol, "call") for vol in vols]
    puts = [black_scholes_price(100.0, 100.0, 1.0, 0.05, vol, "put") for vol in vols]
    assert calls[0] < calls[1] < calls[2]
    assert puts[0] < puts[1] < puts[2]


def test_no_dividend_analytic_bounds() -> None:
    spot, strike, tau, rate, sigma = 95.0, 100.0, 0.4, 0.01, 0.30
    call = black_scholes_price(spot, strike, tau, rate, sigma, "call")
    put = black_scholes_price(spot, strike, tau, rate, sigma, "put")
    discounted_strike = strike * math.exp(-rate * tau)
    assert max(spot - discounted_strike, 0.0) <= call <= spot
    assert max(discounted_strike - spot, 0.0) <= put <= discounted_strike


def test_short_maturity_approaches_payoff() -> None:
    tau = 1e-10
    rate = 0.05
    itm_call = black_scholes_price(120.0, 100.0, tau, rate, 0.20, "call")
    otm_call = black_scholes_price(80.0, 100.0, tau, rate, 0.20, "call")
    itm_put = black_scholes_price(80.0, 100.0, tau, rate, 0.20, "put")
    otm_put = black_scholes_price(120.0, 100.0, tau, rate, 0.20, "put")
    discounted_strike = 100.0 * math.exp(-rate * tau)

    assert math.isclose(itm_call, 120.0 - discounted_strike, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(otm_call, 0.0, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(itm_put, discounted_strike - 80.0, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(otm_put, 0.0, rel_tol=0, abs_tol=1e-8)


def test_prices_are_nonnegative() -> None:
    for option_type in ("call", "put"):
        price = black_scholes_price(50.0, 120.0, 0.25, -0.01, 0.15, option_type)
        assert price >= 0.0


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"spot": 0.0}, "spot"),
        ({"spot": -1.0}, "spot"),
        ({"strike": 0.0}, "strike"),
        ({"time_to_maturity": 0.0}, "time_to_maturity"),
        ({"volatility": 0.0}, "volatility"),
        ({"volatility": -0.2}, "volatility"),
        ({"spot": math.nan}, "spot"),
        ({"rate": math.inf}, "rate"),
        ({"dividend_yield": math.nan}, "dividend_yield"),
        ({"option_type": "Call"}, "option_type"),
        ({"option_type": "european_call"}, "option_type"),
    ],
)
def test_invalid_inputs_are_rejected(kwargs: dict[str, object], message: str) -> None:
    arguments: dict[str, object] = {
        "spot": 100.0,
        "strike": 100.0,
        "time_to_maturity": 1.0,
        "rate": 0.05,
        "volatility": 0.2,
        "option_type": "call",
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=message):
        black_scholes_price(**arguments)  # type: ignore[arg-type]
