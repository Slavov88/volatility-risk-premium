from datetime import date

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


def test_recession_months_from_supplied_chronology_table() -> None:
    months = recession_months_from_chronology(
        ["2008-12-01", "2009-01-01", "2009-02-01"],
        [True, True, False],
    )
    assert months == {"2008-12", "2009-01"}
    labeled = label_nber_regimes(
        [date(2008, 12, 15), date(2009, 2, 10)],
        months,
    )
    assert labeled[0][1] == "recession"
    assert labeled[1][1] == "expansion"
