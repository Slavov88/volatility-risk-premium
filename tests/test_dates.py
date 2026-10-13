from datetime import date, datetime

import pytest

from vrp.dates import as_date


def test_as_date_accepts_date_datetime_and_exact_iso_string() -> None:
    assert as_date(date(2024, 1, 2)) == date(2024, 1, 2)
    assert as_date(datetime(2024, 1, 2, 15, 30)) == date(2024, 1, 2)
    assert as_date("2024-01-02") == date(2024, 1, 2)


@pytest.mark.parametrize(
    "bad",
    [
        "2024-01-02garbage",
        "2024-01-02T12:00:00",
        "2024/01/02",
        "2024-1-2",
    ],
)
def test_as_date_rejects_non_exact_date_strings(bad: str) -> None:
    with pytest.raises(ValueError):
        as_date(bad)


def test_as_date_rejects_non_date_objects() -> None:
    with pytest.raises(TypeError):
        as_date(20240102)  # type: ignore[arg-type]
