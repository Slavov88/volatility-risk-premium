from datetime import date

import pytest

from vrp.regimes import label_nber_regimes, recession_months_from_chronology


def test_daily_origin_inherits_calendar_month() -> None:
    labeled = label_nber_regimes(
        [date(2020, 2, 15), date(2020, 3, 1), "2020-03-31"],
        {"2020-03"},
    )
    assert labeled == [
        (date(2020, 2, 15), "expansion"),
        (date(2020, 3, 1), "recession"),
        (date(2020, 3, 31), "recession"),
    ]


def test_string_zero_is_expansion_not_truthy_recession() -> None:
    months = recession_months_from_chronology(
        ["2020-02-01", "2020-03-01"],
        ["0", "1"],
    )
    assert months == {"2020-03"}


@pytest.mark.parametrize("bad", ["yes", "", 2, -1, None, 0.0])
def test_ambiguous_flags_are_rejected(bad) -> None:
    with pytest.raises(ValueError, match="recession flags|integer"):
        recession_months_from_chronology(["2020-01-01"], [bad])


def test_duplicate_chronology_month_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        recession_months_from_chronology(
            ["2020-01-01", "2020-01-15"],
            [0, 1],
        )
