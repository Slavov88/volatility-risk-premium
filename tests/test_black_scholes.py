"""Track A Black--Scholes validation: parity, limits, vega, and reference prices.

The independent reference formula below uses libm ``erf``, not
``scipy.special.ndtr`` (the CDF used by the authors' pricer). Reference
libraries validate the implementation; they do not replace it. These tests
price a single European option. That object is never interchangeable with
the Cboe VIX or with ``IVAR = (VIX / 100)^2``.
"""

from __future__ import annotations

import math
from itertools import product

import pytest

from black_scholes import black_scholes_price

ABS_TOL = 1e-12

ATM = dict(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    rate=0.05,
    volatility=0.20,
)

# (spot, strike, tau, rate, volatility, dividend_yield)
PARITY_GRID = tuple(
    product(
        (50.0, 100.0, 150.0),
        (80.0, 100.0, 120.0),
        (1.0 / 365.0, 0.25, 2.0),
        (-0.01, 0.0, 0.05),
        (0.01, 0.20, 1.0),
        (0.0, 0.03),
    )
)

MONOTONICITY_SPECS = tuple(
    product(
        (80.0, 100.0, 125.0),
        (90.0, 100.0, 110.0),
        (0.25, 1.0),
        (0.0, 0.05),
        ("call", "put"),
        (0.0, 0.02),
    )
)

EDGE_SPECS = (
    # tiny maturity
    dict(spot=120.0, strike=100.0, time_to_maturity=1e-12, rate=0.05, volatility=0.20),
    dict(spot=80.0, strike=100.0, time_to_maturity=1e-12, rate=0.05, volatility=0.20),
    dict(spot=100.0, strike=100.0, time_to_maturity=1e-12, rate=0.0, volatility=0.20),
    # tiny volatility
    dict(spot=120.0, strike=100.0, time_to_maturity=1.0, rate=0.05, volatility=1e-12),
    dict(spot=80.0, strike=100.0, time_to_maturity=1.0, rate=0.05, volatility=1e-12),
    dict(spot=100.0, strike=100.0, time_to_maturity=1.0, rate=0.05, volatility=1e-12),
    # large volatility
    dict(spot=100.0, strike=100.0, time_to_maturity=1.0, rate=0.05, volatility=8.0),
    dict(spot=50.0, strike=150.0, time_to_maturity=0.5, rate=0.01, volatility=5.0),
    # extreme moneyness
    dict(spot=1e-8, strike=100.0, time_to_maturity=1.0, rate=0.05, volatility=0.20),
    dict(spot=1e8, strike=100.0, time_to_maturity=1.0, rate=0.05, volatility=0.20),
    dict(spot=100.0, strike=1e-8, time_to_maturity=0.5, rate=0.02, volatility=0.15),
    dict(spot=100.0, strike=1e8, time_to_maturity=0.5, rate=0.02, volatility=0.15),
    # negative rate, long maturity, dividend yield
    dict(spot=90.0, strike=100.0, time_to_maturity=5.0, rate=-0.02, volatility=0.25),
    dict(spot=100.0, strike=100.0, time_to_maturity=30.0, rate=0.03, volatility=0.20),
    dict(spot=110.0, strike=100.0, time_to_maturity=0.75, rate=0.01, volatility=0.40),
)


def _norm_cdf(x: float) -> float:
    """Standard normal CDF from libm erf; independent of scipy.special.ndtr."""

    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _reference_price(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> float:
    """Closed-form Black--Scholes / Merton price assembled outside the pricer."""

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


def _forward_diff(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    dividend_yield: float = 0.0,
) -> float:
    return spot * math.exp(-dividend_yield * time_to_maturity) - strike * math.exp(
        -rate * time_to_maturity
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


# ---------------------------------------------------------------------------
# Reference prices
# ---------------------------------------------------------------------------


def test_atm_call_and_put_match_w2_02_formula() -> None:
    """W2-02 ATM case: d1 = 0.35 and d2 = 0.15 exactly."""

    call = _price(**ATM, option_type="call")
    put = _price(**ATM, option_type="put")
    expected_call = _reference_price(**ATM, option_type="call")
    expected_put = _reference_price(**ATM, option_type="put")

    assert math.isclose(call, expected_call, rel_tol=0, abs_tol=ABS_TOL)
    assert math.isclose(put, expected_put, rel_tol=0, abs_tol=ABS_TOL)
    assert math.isclose(call, 10.450583572185565, rel_tol=0, abs_tol=ABS_TOL)
    assert math.isclose(put, 5.573526022256971, rel_tol=0, abs_tol=ABS_TOL)


def test_hull_textbook_european_prices() -> None:
    """Hull OFOD European example, S=42, K=40, r=0.10, sigma=0.20, T=0.5."""

    args = dict(spot=42.0, strike=40.0, time_to_maturity=0.5, rate=0.10, volatility=0.20)
    call = _price(**args, option_type="call")
    put = _price(**args, option_type="put")
    assert math.isclose(call, 4.76, rel_tol=0, abs_tol=5e-3)
    assert math.isclose(put, 0.81, rel_tol=0, abs_tol=5e-3)
    assert math.isclose(call, _reference_price(**args, option_type="call"), rel_tol=0, abs_tol=ABS_TOL)
    assert math.isclose(put, _reference_price(**args, option_type="put"), rel_tol=0, abs_tol=ABS_TOL)


def test_haug_gbs_no_dividend_reference_prices() -> None:
    """Haug GBS European example, S=60, K=65, T=0.25, r=0.08, sigma=0.30."""

    args = dict(spot=60.0, strike=65.0, time_to_maturity=0.25, rate=0.08, volatility=0.30)
    call = _price(**args, option_type="call")
    put = _price(**args, option_type="put")
    assert math.isclose(call, 2.1334, rel_tol=0, abs_tol=5e-5)
    assert math.isclose(put, 5.8463, rel_tol=0, abs_tol=5e-5)
    assert math.isclose(call, _reference_price(**args, option_type="call"), rel_tol=0, abs_tol=ABS_TOL)
    assert math.isclose(put, _reference_price(**args, option_type="put"), rel_tol=0, abs_tol=ABS_TOL)


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize(
    "spot, strike, tau, rate, sigma, dividend_yield",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.0),
        (100.0, 90.0, 0.5, 0.08, 0.25, 0.0),
        (80.0, 100.0, 0.25, 0.01, 0.35, 0.02),
        (110.0, 100.0, 2.0, -0.01, 0.15, 0.03),
        (50.0, 70.0, 1.0 / 365.0, 0.04, 0.50, 0.0),
        (200.0, 150.0, 3.0, 0.06, 0.10, 0.04),
    ],
)
def test_matches_independent_erf_formula(
    option_type: str,
    spot: float,
    strike: float,
    tau: float,
    rate: float,
    sigma: float,
    dividend_yield: float,
) -> None:
    price = _price(spot, strike, tau, rate, sigma, option_type, dividend_yield)
    expected = _reference_price(
        spot, strike, tau, rate, sigma, option_type, dividend_yield
    )
    assert math.isclose(price, expected, rel_tol=0, abs_tol=ABS_TOL)


def test_zero_dividend_yield_matches_core() -> None:
    core_call = _price(**ATM, option_type="call")
    core_put = _price(**ATM, option_type="put")
    q_call = _price(**ATM, option_type="call", dividend_yield=0.0)
    q_put = _price(**ATM, option_type="put", dividend_yield=0.0)
    assert core_call == q_call
    assert core_put == q_put


# ---------------------------------------------------------------------------
# Put-call parity
# ---------------------------------------------------------------------------


def test_put_call_parity_no_dividend() -> None:
    call = _price(110.0, 100.0, 0.75, 0.03, 0.25, "call")
    put = _price(110.0, 100.0, 0.75, 0.03, 0.25, "put")
    assert math.isclose(call - put, _forward_diff(110.0, 100.0, 0.75, 0.03), rel_tol=0, abs_tol=ABS_TOL)


def test_put_call_parity_with_dividend_yield() -> None:
    q = 0.02
    call = _price(110.0, 100.0, 0.75, 0.03, 0.25, "call", dividend_yield=q)
    put = _price(110.0, 100.0, 0.75, 0.03, 0.25, "put", dividend_yield=q)
    assert math.isclose(
        call - put,
        _forward_diff(110.0, 100.0, 0.75, 0.03, q),
        rel_tol=0,
        abs_tol=ABS_TOL,
    )


@pytest.mark.parametrize("spot, strike, tau, rate, sigma, dividend_yield", PARITY_GRID)
def test_put_call_parity_grid(
    spot: float,
    strike: float,
    tau: float,
    rate: float,
    sigma: float,
    dividend_yield: float,
) -> None:
    call = _price(spot, strike, tau, rate, sigma, "call", dividend_yield)
    put = _price(spot, strike, tau, rate, sigma, "put", dividend_yield)
    assert math.isclose(
        call - put,
        _forward_diff(spot, strike, tau, rate, dividend_yield),
        rel_tol=0,
        abs_tol=1e-10,
    )


def test_put_call_parity_independent_of_volatility() -> None:
    spot, strike, tau, rate, q = 95.0, 100.0, 0.4, 0.01, 0.015
    diffs = [
        _price(spot, strike, tau, rate, sigma, "call", q)
        - _price(spot, strike, tau, rate, sigma, "put", q)
        for sigma in (0.05, 0.20, 0.80, 2.0)
    ]
    for diff in diffs[1:]:
        assert math.isclose(diff, diffs[0], rel_tol=0, abs_tol=ABS_TOL)
    assert math.isclose(diffs[0], _forward_diff(spot, strike, tau, rate, q), rel_tol=0, abs_tol=ABS_TOL)


def test_put_call_parity_at_numerical_edges() -> None:
    for spec in EDGE_SPECS:
        q = 0.01 if spec["spot"] < spec["strike"] else 0.0
        call = _price(**spec, option_type="call", dividend_yield=q)
        put = _price(**spec, option_type="put", dividend_yield=q)
        expected = _forward_diff(
            spec["spot"],
            spec["strike"],
            spec["time_to_maturity"],
            spec["rate"],
            q,
        )
        scale = max(1.0, abs(spec["spot"]), abs(spec["strike"]), abs(expected))
        assert math.isclose(call - put, expected, rel_tol=0, abs_tol=1e-9 * scale)


# ---------------------------------------------------------------------------
# Limiting cases
# ---------------------------------------------------------------------------


def test_short_maturity_approaches_payoff() -> None:
    tau = 1e-10
    rate = 0.05
    itm_call = _price(120.0, 100.0, tau, rate, 0.20, "call")
    otm_call = _price(80.0, 100.0, tau, rate, 0.20, "call")
    itm_put = _price(80.0, 100.0, tau, rate, 0.20, "put")
    otm_put = _price(120.0, 100.0, tau, rate, 0.20, "put")
    discounted_strike = 100.0 * math.exp(-rate * tau)

    assert math.isclose(itm_call, 120.0 - discounted_strike, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(otm_call, 0.0, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(itm_put, discounted_strike - 80.0, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(otm_put, 0.0, rel_tol=0, abs_tol=1e-8)


def test_short_maturity_atm_scales_like_sqrt_tau() -> None:
    """ATM payoff is zero; leading time value is S sigma sqrt(tau / 2 pi)."""

    taus = (1e-8, 1e-10, 1e-12)
    calls = [_price(100.0, 100.0, tau, 0.0, 0.20, "call") for tau in taus]
    puts = [_price(100.0, 100.0, tau, 0.0, 0.20, "put") for tau in taus]
    for tau, call, put in zip(taus, calls, puts):
        approx = 100.0 * 0.20 * math.sqrt(tau / (2.0 * math.pi))
        assert math.isclose(call, approx, rel_tol=1e-8, abs_tol=0.0)
        assert math.isclose(put, approx, rel_tol=1e-8, abs_tol=0.0)
    assert calls[0] > calls[1] > calls[2]
    assert puts[0] > puts[1] > puts[2]
    assert calls[-1] < 1e-5


def test_spot_near_zero_recovers_discounted_strike_put() -> None:
    strike, tau, rate, sigma = 100.0, 1.0, 0.05, 0.20
    spot = 1e-10
    call = _price(spot, strike, tau, rate, sigma, "call")
    put = _price(spot, strike, tau, rate, sigma, "put")
    discounted_strike = strike * math.exp(-rate * tau)
    assert math.isclose(call, 0.0, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(put, discounted_strike, rel_tol=0, abs_tol=1e-8)


def test_large_spot_call_tracks_forward_put_vanishes() -> None:
    strike, tau, rate, sigma = 100.0, 1.0, 0.05, 0.20
    spot = 1e6
    call = _price(spot, strike, tau, rate, sigma, "call")
    put = _price(spot, strike, tau, rate, sigma, "put")
    forward = _forward_diff(spot, strike, tau, rate)
    assert math.isclose(call, forward, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(put, 0.0, rel_tol=0, abs_tol=1e-6)


def test_vanishing_volatility_recovers_forward_intrinsic() -> None:
    tau, rate, q, sigma = 1.0, 0.05, 0.01, 1e-12
    cases = (
        (120.0, 100.0),
        (80.0, 100.0),
        (100.0 * math.exp((rate - q) * tau), 100.0),
    )
    for spot, strike in cases:
        call = _price(spot, strike, tau, rate, sigma, "call", q)
        put = _price(spot, strike, tau, rate, sigma, "put", q)
        forward = _forward_diff(spot, strike, tau, rate, q)
        assert math.isclose(call, max(forward, 0.0), rel_tol=0, abs_tol=1e-8)
        assert math.isclose(put, max(-forward, 0.0), rel_tol=0, abs_tol=1e-8)


def test_large_volatility_approaches_upper_bounds() -> None:
    spot, strike, tau, rate, q, sigma = 100.0, 90.0, 1.25, 0.04, 0.01, 12.0
    call = _price(spot, strike, tau, rate, sigma, "call", q)
    put = _price(spot, strike, tau, rate, sigma, "put", q)
    discounted_spot = spot * math.exp(-q * tau)
    discounted_strike = strike * math.exp(-rate * tau)
    assert math.isclose(call, discounted_spot, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(put, discounted_strike, rel_tol=0, abs_tol=1e-6)


def test_no_dividend_analytic_bounds() -> None:
    spot, strike, tau, rate, sigma = 95.0, 100.0, 0.4, 0.01, 0.30
    call = _price(spot, strike, tau, rate, sigma, "call")
    put = _price(spot, strike, tau, rate, sigma, "put")
    discounted_strike = strike * math.exp(-rate * tau)
    assert max(spot - discounted_strike, 0.0) <= call <= spot
    assert max(discounted_strike - spot, 0.0) <= put <= discounted_strike


def test_merton_analytic_bounds_on_grid() -> None:
    for spot, strike, tau, rate, sigma, q in PARITY_GRID:
        call = _price(spot, strike, tau, rate, sigma, "call", q)
        put = _price(spot, strike, tau, rate, sigma, "put", q)
        discounted_spot = spot * math.exp(-q * tau)
        discounted_strike = strike * math.exp(-rate * tau)
        assert max(discounted_spot - discounted_strike, 0.0) <= call + 1e-12
        assert call <= discounted_spot + 1e-12
        assert max(discounted_strike - discounted_spot, 0.0) <= put + 1e-12
        assert put <= discounted_strike + 1e-12


def test_dividend_yield_lowers_calls_and_raises_puts() -> None:
    call_core = _price(**ATM, option_type="call")
    put_core = _price(**ATM, option_type="put")
    call_q = _price(**ATM, option_type="call", dividend_yield=0.03)
    put_q = _price(**ATM, option_type="put", dividend_yield=0.03)
    assert call_q < call_core
    assert put_q > put_core


# ---------------------------------------------------------------------------
# Monotonicity in volatility
# ---------------------------------------------------------------------------


def test_price_is_strictly_increasing_in_volatility() -> None:
    vols = (0.10, 0.20, 0.35)
    calls = [_price(100.0, 100.0, 1.0, 0.05, vol, "call") for vol in vols]
    puts = [_price(100.0, 100.0, 1.0, 0.05, vol, "put") for vol in vols]
    assert calls[0] < calls[1] < calls[2]
    assert puts[0] < puts[1] < puts[2]


@pytest.mark.parametrize(
    "spot, strike, tau, rate, option_type, dividend_yield",
    MONOTONICITY_SPECS,
)
def test_strict_monotonicity_in_volatility_grid(
    spot: float,
    strike: float,
    tau: float,
    rate: float,
    option_type: str,
    dividend_yield: float,
) -> None:
    # Moderate vols keep time value above float64 saturation for deep ITM/OTM.
    vols = (0.10, 0.20, 0.35, 0.80, 1.5)
    prices = [
        _price(spot, strike, tau, rate, vol, option_type, dividend_yield) for vol in vols
    ]
    assert all(left < right for left, right in zip(prices, prices[1:]))


@pytest.mark.parametrize(
    "spot, strike, tau, rate, option_type, dividend_yield",
    MONOTONICITY_SPECS,
)
def test_prices_are_nondecreasing_in_volatility_including_tiny_vol(
    spot: float,
    strike: float,
    tau: float,
    rate: float,
    option_type: str,
    dividend_yield: float,
) -> None:
    # Deep ITM/OTM time value can underflow at tiny sigma, so only weak
    # monotonicity is asserted on this wider grid.
    vols = (1e-4, 0.05, 0.10, 0.20, 0.35, 0.80, 1.5)
    prices = [
        _price(spot, strike, tau, rate, vol, option_type, dividend_yield) for vol in vols
    ]
    assert all(left <= right for left, right in zip(prices, prices[1:]))


def test_tiny_volatility_increment_raises_price() -> None:
    sigma = 0.20
    bump = 1e-8
    for option_type in ("call", "put"):
        low = _price(100.0, 105.0, 0.5, 0.03, sigma, option_type, 0.01)
        high = _price(100.0, 105.0, 0.5, 0.03, sigma + bump, option_type, 0.01)
        assert high > low


def test_finite_difference_vega_matches_analytic_and_is_positive() -> None:
    spot, strike, tau, rate, sigma, q = 100.0, 100.0, 1.0, 0.05, 0.20, 0.0
    bump = 1e-6
    call_up = _price(spot, strike, tau, rate, sigma + bump, "call", q)
    call_down = _price(spot, strike, tau, rate, sigma - bump, "call", q)
    put_up = _price(spot, strike, tau, rate, sigma + bump, "put", q)
    put_down = _price(spot, strike, tau, rate, sigma - bump, "put", q)
    call_vega = (call_up - call_down) / (2.0 * bump)
    put_vega = (put_up - put_down) / (2.0 * bump)

    vol_sqrt_tau = sigma * math.sqrt(tau)
    d1 = (math.log(spot / strike) + (rate - q + 0.5 * sigma * sigma) * tau) / vol_sqrt_tau
    analytic = spot * math.exp(-q * tau) * math.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi) * math.sqrt(tau)

    assert call_vega > 0.0
    assert put_vega > 0.0
    assert math.isclose(call_vega, put_vega, rel_tol=0, abs_tol=1e-8)
    assert math.isclose(call_vega, analytic, rel_tol=0, abs_tol=1e-6)


# ---------------------------------------------------------------------------
# Numerical edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spec", EDGE_SPECS)
@pytest.mark.parametrize("option_type", ["call", "put"])
def test_edge_prices_are_finite_nonnegative_and_within_bounds(
    spec: dict[str, float],
    option_type: str,
) -> None:
    q = 0.0
    price = _price(**spec, option_type=option_type, dividend_yield=q)
    discounted_spot = spec["spot"] * math.exp(-q * spec["time_to_maturity"])
    discounted_strike = spec["strike"] * math.exp(-spec["rate"] * spec["time_to_maturity"])
    upper = discounted_spot if option_type == "call" else discounted_strike
    scale = max(1.0, abs(upper), abs(spec["spot"]), abs(spec["strike"]))

    assert math.isfinite(price)
    assert price >= -1e-12
    assert price <= upper + 1e-9 * scale


def test_prices_are_nonnegative() -> None:
    for option_type in ("call", "put"):
        price = _price(50.0, 120.0, 0.25, -0.01, 0.15, option_type)
        assert price >= 0.0


def test_deep_otm_prices_are_numerically_zero() -> None:
    call = _price(1.0, 1e6, 0.01, 0.0, 0.01, "call")
    put = _price(1e6, 1.0, 0.01, 0.0, 0.01, "put")
    assert math.isclose(call, 0.0, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(put, 0.0, rel_tol=0, abs_tol=1e-12)


def test_homogeneous_of_degree_one() -> None:
    scale = 7.5
    args = dict(spot=80.0, strike=90.0, time_to_maturity=0.8, rate=0.02, volatility=0.22)
    for option_type in ("call", "put"):
        base = _price(**args, option_type=option_type, dividend_yield=0.01)
        scaled = _price(
            args["spot"] * scale,
            args["strike"] * scale,
            args["time_to_maturity"],
            args["rate"],
            args["volatility"],
            option_type,
            0.01,
        )
        assert math.isclose(scaled, scale * base, rel_tol=0, abs_tol=1e-10)


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
