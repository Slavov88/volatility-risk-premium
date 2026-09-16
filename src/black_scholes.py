"""European Black--Scholes prices for Track A validation.

This module implements the authors' own European call and put pricer. It is a
Track A object: a single-option Black--Scholes price, and later a single-option
implied volatility, is never interchangeable with the Cboe VIX. VIX remains a
model-free 30-calendar-day expected-volatility index; the empirical
variance-space quantity is still ``IVAR = (VIX / 100)^2``.

The core formulas are the no-dividend Black--Scholes prices derived in
``docs/w2_02_european_option_formula.md``:

    d1 = [log(S / K) + (r + 0.5 sigma^2) tau] / (sigma sqrt(tau))
    d2 = d1 - sigma sqrt(tau)
    C  = S N(d1) - K exp(-r tau) N(d2)
    P  = K exp(-r tau) N(-d2) - S N(-d1)

An optional continuous dividend yield ``q`` recovers the Merton (1973)
extension. Setting ``q = 0`` (the default) restores the W2-02 core. Real SPX
option validation must still address discrete dividends, rates, bid/ask
spreads, timing, and contract details; those are not absorbed into this
formula.

Inputs use internal research units: ``spot`` and ``strike`` in price points,
``time_to_maturity`` in years, ``rate`` and ``dividend_yield`` as continuously
compounded decimals, and ``volatility`` as annualized decimal volatility.
Percentage quotes must be converted before they enter this function.
"""

from __future__ import annotations

import math
from typing import Literal

from scipy.special import ndtr

OptionType = Literal["call", "put"]

__all__ = ["black_scholes_price"]


def _as_finite_float(name: str, value: object) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{name} must be a finite real number")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite real number")
    return number


def _as_positive_finite(name: str, value: object) -> float:
    number = _as_finite_float(name, value)
    if number <= 0.0:
        raise ValueError(f"{name} must be strictly positive")
    return number


def _d1_d2(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    volatility: float,
    dividend_yield: float,
) -> tuple[float, float]:
    vol_sqrt_tau = volatility * math.sqrt(time_to_maturity)
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * time_to_maturity
    ) / vol_sqrt_tau
    return d1, d1 - vol_sqrt_tau


def black_scholes_price(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    volatility: float,
    option_type: OptionType,
    *,
    dividend_yield: float = 0.0,
) -> float:
    """Price a European call or put under Black--Scholes / Merton.

    Parameters
    ----------
    spot
        Current underlying price ``S``. Must be finite and strictly positive.
    strike
        Strike price ``K``. Must be finite and strictly positive.
    time_to_maturity
        Time to expiry ``tau = T - t`` in years. Must be finite and strictly
        positive. At expiry the analytic ``d1`` / ``d2`` formulas are
        undefined; use the contractual payoff instead.
    rate
        Continuously compounded risk-free rate ``r`` per year, as a decimal
        (``0.05``, not ``5``). May be zero or negative, but must be finite.
    volatility
        Constant annualized decimal volatility ``sigma``. Must be finite and
        strictly positive. This is a single-option Black--Scholes input, not
        ``VIX / 100``.
    option_type
        ``"call"`` or ``"put"``.
    dividend_yield
        Optional continuous dividend yield ``q`` per year, as a decimal.
        Defaults to ``0.0``, which is the no-dividend W2-02 core. Must be
        finite. This is an extension, not a change to the locked empirical
        protocol.

    Returns
    -------
    float
        Present-value European option price in the same units as ``spot``
        and ``strike``.

    Raises
    ------
    ValueError
        If any input is non-finite, if ``spot``, ``strike``,
        ``time_to_maturity``, or ``volatility`` is not strictly positive, or if
        ``option_type`` is not ``"call"`` or ``"put"``.
    """

    spot = _as_positive_finite("spot", spot)
    strike = _as_positive_finite("strike", strike)
    time_to_maturity = _as_positive_finite("time_to_maturity", time_to_maturity)
    rate = _as_finite_float("rate", rate)
    volatility = _as_positive_finite("volatility", volatility)
    dividend_yield = _as_finite_float("dividend_yield", dividend_yield)

    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'")

    d1, d2 = _d1_d2(
        spot,
        strike,
        time_to_maturity,
        rate,
        volatility,
        dividend_yield,
    )
    discounted_spot = spot * math.exp(-dividend_yield * time_to_maturity)
    discounted_strike = strike * math.exp(-rate * time_to_maturity)

    if option_type == "call":
        price = discounted_spot * ndtr(d1) - discounted_strike * ndtr(d2)
    else:
        price = discounted_strike * ndtr(-d2) - discounted_spot * ndtr(-d1)

    return float(price)
