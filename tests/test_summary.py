import math

import pytest

from vrp.summary import summary_statistics


def test_summary_statistics_known_three_point_sample() -> None:
    stats = summary_statistics([1.0, 2.0, 3.0])
    assert stats["n_obs"] == 3.0
    assert stats["mean"] == 2.0
    assert math.isclose(stats["std"], 1.0, abs_tol=1e-15)
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


def test_summary_uses_bias_corrected_fisher_moments() -> None:
    stats = summary_statistics([1.0, 2.0, 3.0, 8.0, 10.0])
    values = [1.0, 2.0, 3.0, 8.0, 10.0]
    mean = sum(values) / len(values)
    centered = [x - mean for x in values]
    n = len(values)
    m2 = sum(x*x for x in centered) / n
    m3 = sum(x**3 for x in centered) / n
    m4 = sum(x**4 for x in centered) / n
    g1 = m3 / (m2**1.5)
    g2 = m4 / (m2**2) - 3.0
    expected_skew = math.sqrt(n*(n-1))/(n-2) * g1
    expected_kurt = ((n-1)/((n-2)*(n-3))) * ((n+1)*g2 + 6.0)
    assert math.isclose(stats["skewness"], expected_skew, rel_tol=1e-12)
    assert math.isclose(stats["excess_kurtosis"], expected_kurt, rel_tol=1e-12)
