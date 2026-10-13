"""Implied variance and implied-minus-realized empirical objects."""

from __future__ import annotations

import math

from vrp.config import CONVENTIONS


def _nonnegative_finite(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return number


def ivol_from_vix(vix: float) -> float:
    """IVOL_t = VIX_t / 100."""

    value = _nonnegative_finite("VIX", vix)
    return value / CONVENTIONS.percent_scale


def ivar_from_vix(vix: float) -> float:
    """IVAR_t = IVOL_t squared."""

    ivol = ivol_from_vix(vix)
    return ivol * ivol


def vrp_x(ivar: float, rvar: float) -> float:
    """Primary object: VRP_X = IVAR - RVAR."""

    implied = _nonnegative_finite("implied variance", ivar)
    realized = _nonnegative_finite("realized variance", rvar)
    return implied - realized


def volgap(ivol: float, rvol: float) -> float:
    """Secondary object: VOLGAP = IVOL - RVOL."""

    implied = _nonnegative_finite("implied volatility", ivol)
    realized = _nonnegative_finite("realized volatility", rvol)
    return implied - realized
