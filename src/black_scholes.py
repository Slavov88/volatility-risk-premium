"""European Black--Scholes prices and implied volatility for Track A validation.

This module implements the authors' own European call and put pricer and the
implied-volatility inversion required by the locked protocol. Both objects are
Track A quantities: a single-option Black--Scholes price or implied volatility
is never interchangeable with the Cboe VIX. VIX remains a model-free
30-calendar-day expected-volatility index; the empirical variance-space
quantity is still ``IVAR = (VIX / 100)^2``.

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

Implied volatility is the unique strictly positive ``sigma`` such that the
authors' pricer recovers the quoted price, when that root exists. The solver
uses Brent's method (via ``scipy.optimize.brentq``) on a documented positive
volatility bracket. It validates ``S > 0``, ``K > 0``, ``T > 0``, rejects
prices outside the European no-arbitrage bounds, and raises an explicit
diagnostic error if no root is bracketed.

Inputs use internal research units: ``spot`` and ``strike`` in price points,
``time_to_maturity`` in years, ``rate`` and ``dividend_yield`` as continuously
compounded decimals, and ``volatility`` as annualized decimal volatility.
Percentage quotes must be converted before they enter this function.
"""

from __future__ import annotations

import math
from typing import Literal

from scipy.optimize import brentq
from scipy.special import ndtr

OptionType = Literal["call", "put"]

# Positive-volatility search interval for implied-volatility inversion.
# The floor is strictly positive so d1/d2 remain defined and is far below any
# recorded equity-index implied volatility. The initial high is 100%
# annualized, the natural equity-index scale; the interval then expands by
# doubling until a sign change appears or the cap is reached. The cap is a
# computational/economic guardrail (5000% annualized), not a claim that a
# mathematical root cannot exist beyond it. Failure to bracket is explicit.
IV_SEARCH_FLOOR = 1e-8
IV_SEARCH_INITIAL_HIGH = 1.0
IV_SEARCH_EXPANSION = 2.0
IV_SEARCH_CAP = 50.0

_IV_XTOL = 2e-12
_IV_RTOL = 1e-12
_IV_MAXITER = 100

__all__ = [
    "IV_SEARCH_CAP",
    "IV_SEARCH_FLOOR",
    "ImpliedVolatilityError",
    "black_scholes_price",
    "implied_volatility",
]


class ImpliedVolatilityError(ValueError):
    """Explicit diagnostic failure from Black--Scholes implied-volatility inversion.

    ``code`` is a stable token for callers and tests:

    - ``invalid_input``: non-finite or non-positive ``S``, ``K``, ``T``,
      non-finite rate/yield/price, or an unknown option type.
    - ``price_below_intrinsic``: quote is below the European lower bound.
    - ``price_above_upper_bound``: quote is above the European upper bound.
    - ``no_bracket``: the quote is inside the bounds but no sign change exists
      on the positive search interval.
    - ``solver_failure``: Brent's method did not converge or the fitted
      volatility failed the reprice check.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


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


def _european_price_bounds(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    dividend_yield: float,
    option_type: OptionType,
) -> tuple[float, float, float]:
    """Return ``(lower, upper, scale)`` for a European call or put.

    The bounds are the model-consistent Merton limits used by the pricer:

        discounted_spot   = S exp(-q tau)
        discounted_strike = K exp(-r tau)
        call: max(discounted_spot - discounted_strike, 0) <= C <= discounted_spot
        put:  max(discounted_strike - discounted_spot, 0) <= P <= discounted_strike

    With ``q = 0`` these recover the W2-02 bounds
    ``(S - K e^{-r tau})^+ <= C <= S`` and
    ``(K e^{-r tau} - S)^+ <= P <= K e^{-r tau}``.
    """

    try:
        discounted_spot = spot * math.exp(-dividend_yield * time_to_maturity)
        discounted_strike = strike * math.exp(-rate * time_to_maturity)
    except OverflowError as exc:
        raise ImpliedVolatilityError(
            "invalid_input",
            "rate or dividend_yield produces an overflowing discounted value",
        ) from exc
    if not math.isfinite(discounted_spot) or not math.isfinite(discounted_strike):
        raise ImpliedVolatilityError(
            "invalid_input",
            "rate or dividend_yield produces a non-finite discounted value",
        )
    if option_type == "call":
        lower = max(discounted_spot - discounted_strike, 0.0)
        upper = discounted_spot
    else:
        lower = max(discounted_strike - discounted_spot, 0.0)
        upper = discounted_strike
    scale = max(1.0, abs(spot), abs(strike), abs(discounted_spot), abs(discounted_strike))
    return lower, upper, scale


def implied_volatility(
    spot: float,
    strike: float,
    time_to_maturity: float,
    rate: float,
    price: float,
    option_type: OptionType,
    *,
    dividend_yield: float = 0.0,
) -> float:
    """Invert a European Black--Scholes price for a unique positive volatility.

    Parameters
    ----------
    spot
        Current underlying price ``S``. Must be finite and strictly positive.
    strike
        Strike price ``K``. Must be finite and strictly positive.
    time_to_maturity
        Time to expiry ``tau = T - t`` in years. Must be finite and strictly
        positive.
    rate
        Continuously compounded risk-free rate ``r`` per year, as a decimal.
        May be zero or negative, but must be finite.
    price
        Observed European option price in the same units as ``spot`` and
        ``strike``. Must be finite. The quote must lie strictly inside the
        European no-arbitrage bounds for a unique positive finite implied
        volatility to exist.
    option_type
        ``"call"`` or ``"put"``.
    dividend_yield
        Optional continuous dividend yield ``q`` per year, as a decimal.
        Defaults to ``0.0``, which is the no-dividend W2-02 core.

    Returns
    -------
    float
        Annualized decimal Black--Scholes implied volatility. This is a
        single-option Track A object, not ``VIX / 100``.

    Raises
    ------
    ImpliedVolatilityError
        If inputs are invalid, the quote violates European price bounds, no
        sign change exists on the positive search interval, or Brent's method
        fails. The exception ``code`` identifies the diagnostic.
    """

    try:
        spot = _as_positive_finite("spot", spot)
        strike = _as_positive_finite("strike", strike)
        time_to_maturity = _as_positive_finite("time_to_maturity", time_to_maturity)
        rate = _as_finite_float("rate", rate)
        price = _as_finite_float("price", price)
        dividend_yield = _as_finite_float("dividend_yield", dividend_yield)
    except ValueError as exc:
        raise ImpliedVolatilityError("invalid_input", str(exc)) from exc

    if option_type not in {"call", "put"}:
        raise ImpliedVolatilityError("invalid_input", "option_type must be 'call' or 'put'")

    lower, upper, scale = _european_price_bounds(
        spot, strike, time_to_maturity, rate, dividend_yield, option_type
    )
    bound_tol = 1e-12 * max(scale, abs(price))

    if price < lower - bound_tol:
        raise ImpliedVolatilityError(
            "price_below_intrinsic",
            (
                "quoted price is below the European lower bound "
                f"({price} < {lower})"
            ),
        )
    if price > upper + bound_tol:
        raise ImpliedVolatilityError(
            "price_above_upper_bound",
            (
                "quoted price is above the European upper bound "
                f"({price} > {upper})"
            ),
        )
    if price <= lower + bound_tol:
        raise ImpliedVolatilityError(
            "no_bracket",
            (
                "quoted price is at the European lower bound; no strictly "
                "positive implied volatility is identified"
            ),
        )
    if price >= upper - bound_tol:
        raise ImpliedVolatilityError(
            "no_bracket",
            (
                "quoted price is at the European upper bound; no finite "
                "implied volatility is identified"
            ),
        )

    def residual(volatility: float) -> float:
        return (
            black_scholes_price(
                spot,
                strike,
                time_to_maturity,
                rate,
                volatility,
                option_type,
                dividend_yield=dividend_yield,
            )
            - price
        )

    low = IV_SEARCH_FLOOR
    high = min(IV_SEARCH_INITIAL_HIGH, IV_SEARCH_CAP)
    try:
        f_low = residual(low)
        f_high = residual(high)
    except ValueError as exc:
        raise ImpliedVolatilityError("solver_failure", str(exc)) from exc

    if not math.isfinite(f_low) or not math.isfinite(f_high):
        raise ImpliedVolatilityError(
            "solver_failure",
            "Black--Scholes residual is non-finite on the initial search interval",
        )

    # Require an actual signed bracket. In particular, a small price residual
    # is not evidence that an endpoint is the implied volatility when vega is
    # low. If the residual is exactly zero at an expandable high endpoint,
    # move beyond it so Brent can invert across a strict sign change.
    while f_high <= 0.0 and high < IV_SEARCH_CAP:
        high = min(high * IV_SEARCH_EXPANSION, IV_SEARCH_CAP)
        try:
            f_high = residual(high)
        except ValueError as exc:
            raise ImpliedVolatilityError("solver_failure", str(exc)) from exc
        if not math.isfinite(f_high):
            raise ImpliedVolatilityError(
                "solver_failure",
                f"Black--Scholes residual is non-finite at volatility {high}",
            )

    if not (f_low < 0.0 < f_high):
        endpoint_detail = ""
        if f_low == 0.0 or f_high == 0.0:
            endpoint_detail = (
                "; an endpoint price is numerically indistinguishable from "
                "the quote, so implied volatility is not identified"
            )
        raise ImpliedVolatilityError(
            "no_bracket",
            (
                "no strict sign change on the positive volatility search interval "
                f"[{low}, {high}]; residual(low)={f_low:.6g}, "
                f"residual(high)={f_high:.6g}{endpoint_detail}"
            ),
        )

    try:
        sigma, solver_info = brentq(
            residual,
            low,
            high,
            xtol=_IV_XTOL,
            rtol=_IV_RTOL,
            maxiter=_IV_MAXITER,
            full_output=True,
            disp=False,
        )
    except ValueError as exc:
        raise ImpliedVolatilityError(
            "no_bracket",
            (
                "Brent's method could not bracket a root on "
                f"[{low}, {high}]; residual(low)={f_low:.6g}, "
                f"residual(high)={f_high:.6g}"
            ),
        ) from exc
    if not solver_info.converged:
        raise ImpliedVolatilityError(
            "solver_failure",
            (
                "Brent's method did not converge within "
                f"{_IV_MAXITER} iterations"
            ),
        )
    sigma = float(sigma)

    if not math.isfinite(sigma) or sigma <= 0.0:
        raise ImpliedVolatilityError(
            "solver_failure",
            f"Brent's method returned a non-positive or non-finite volatility {sigma}",
        )

    fitted = black_scholes_price(
        spot,
        strike,
        time_to_maturity,
        rate,
        sigma,
        option_type,
        dividend_yield=dividend_yield,
    )
    if not math.isfinite(fitted) or abs(fitted - price) > max(1e-8, 1e-10 * scale):
        raise ImpliedVolatilityError(
            "solver_failure",
            (
                "recovered volatility does not reprice the quote "
                f"(fitted={fitted}, quote={price}, sigma={sigma})"
            ),
        )

    return sigma
