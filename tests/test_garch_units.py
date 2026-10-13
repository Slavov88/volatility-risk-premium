import math

import pytest

from vrp.garch_units import from_garch_variance, to_garch_fit_returns


def test_garch_return_and_variance_scaling_is_dimensionally_exact() -> None:
    assert to_garch_fit_returns([0.01, -0.025]) == pytest.approx([1.0, -2.5])
    assert math.isclose(from_garch_variance(4.0), 0.0004, abs_tol=1e-15)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_garch_unit_helpers_reject_nonfinite(bad: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        to_garch_fit_returns([bad])
    with pytest.raises(ValueError, match="finite"):
        from_garch_variance(bad)


def test_garch_variance_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        from_garch_variance(-0.01)
