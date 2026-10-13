import math

import pytest

from vrp.summary import summary_statistics


def test_summary_statistics_known_three_point_sample() -> None:
    stats = summary_statistics([1.0, 2.0, 3.0])
    assert stats["n_obs"] == 3.0
    assert stats["mean"] == 2.0
    assert math.isclose(stats["std"], math.sqrt(2.0 / 3.0), abs_tol=1e-15)
    assert stats["median"] == 2.0
    assert stats["q25"] == 1.5
    assert stats["q75"] == 2.5
    assert stats["proportion_positive"] == 1.0


def test_summary_statistics_constant_and_empty() -> None:
    stats = summary_statistics([2.0, 2.0, 2.0])
    assert stats["std"] == 0.0
    assert stats["skewness"] == 0.0
    assert stats["excess_kurtosis"] == 0.0
    assert summary_statistics([]) == {"n_obs": 0.0}


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_summary_statistics_reject_nonfinite(bad) -> None:
    with pytest.raises(ValueError, match="finite"):
        summary_statistics([1.0, bad])
