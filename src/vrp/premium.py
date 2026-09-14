"""Implied variance and the locked implied-minus-realized empirical objects.

VIX is treated as a model-free 30-calendar-day expected-volatility index.
Internal units are annualized decimals: ``IVOL = VIX / 100``, ``IVAR = IVOL^2``.
"""

from __future__ import annotations

from vrp.config import CONVENTIONS


def ivol_from_vix(vix: float) -> float:
    """``IVOL_t = VIX_t / 100``."""

    return vix / CONVENTIONS.percent_scale


def ivar_from_vix(vix: float) -> float:
    """``IVAR_t = IVOL_t^2 = (VIX_t / 100)^2``."""

    ivol = ivol_from_vix(vix)
    return ivol * ivol


def vrp_x(ivar: float, rvar: float) -> float:
    """Primary object: ``VRP_X = IVAR - RVAR`` (implied minus realized)."""

    return ivar - rvar


def volgap(ivol: float, rvol: float) -> float:
    """Secondary object: ``VOLGAP = IVOL - RVOL`` (implied minus realized)."""

    return ivol - rvol
