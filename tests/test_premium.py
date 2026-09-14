import math

from vrp.premium import ivar_from_vix, ivol_from_vix, volgap, vrp_x


def test_vix_scaling_ivol_and_ivar() -> None:
    assert math.isclose(ivol_from_vix(20.0), 0.20, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(ivar_from_vix(20.0), 0.04, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(ivar_from_vix(20.0), ivol_from_vix(20.0) ** 2, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(ivol_from_vix(0.0), 0.0, rel_tol=0, abs_tol=0.0)
    assert math.isclose(ivar_from_vix(12.5), (0.125) ** 2, rel_tol=0, abs_tol=1e-15)


def test_vrp_x_sign_is_implied_minus_realized() -> None:
    assert math.isclose(vrp_x(0.04, 0.01), 0.03, rel_tol=0, abs_tol=1e-12)
    assert vrp_x(0.01, 0.04) < 0
    assert math.isclose(vrp_x(0.01, 0.04), -0.03, rel_tol=0, abs_tol=1e-12)


def test_volgap_sign_is_implied_minus_realized() -> None:
    assert math.isclose(volgap(0.20, 0.10), 0.10, rel_tol=0, abs_tol=1e-12)
    assert volgap(0.10, 0.20) < 0
    assert math.isclose(volgap(0.10, 0.20), -0.10, rel_tol=0, abs_tol=1e-12)
