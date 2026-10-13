import math

import pytest

from vrp.premium import ivar_from_vix, ivol_from_vix, volgap, vrp_x


def test_vix_scaling_ivol_and_ivar() -> None:
    assert math.isclose(ivol_from_vix(20.0), 0.20, abs_tol=1e-12)
    assert math.isclose(ivar_from_vix(20.0), 0.04, abs_tol=1e-12)


def test_vrp_and_volgap_signs_are_implied_minus_realized() -> None:
    assert math.isclose(vrp_x(0.04, 0.01), 0.03, abs_tol=1e-12)
    assert math.isclose(volgap(0.20, 0.10), 0.10, abs_tol=1e-12)


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_premium_helpers_reject_invalid_inputs(bad) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        ivol_from_vix(bad)
    with pytest.raises(ValueError, match="finite and non-negative"):
        vrp_x(0.04, bad)
    with pytest.raises(ValueError, match="finite and non-negative"):
        volgap(0.2, bad)
