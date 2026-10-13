from datetime import date

import math
import pytest

from vrp.origin_panel import align_origin_panel


def test_alignment_excludes_post_2025_spx_support_rows() -> None:
    spx = [date(2025, 12, 31), date(2026, 1, 2)]
    rows, report = align_origin_panel(
        spx,
        [(date(2025, 12, 31), 20.0), (date(2026, 1, 2), 21.0)],
    )
    assert [row.origin for row in rows] == [date(2025, 12, 31)]
    assert math.isclose(rows[0].ivol, 0.20)
    assert math.isclose(rows[0].ivar, 0.04)
    assert report.common_origins == 1


def test_alignment_reports_missing_vix_without_silent_drop() -> None:
    spx = [date(2024, 1, 2), date(2024, 1, 3)]
    rows, report = align_origin_panel(spx, [(date(2024, 1, 2), 15.0)])
    assert len(rows) == 1
    assert report.missing_vix_on_spx == ("2024-01-03",)


def test_alignment_labels_2014_methodology_regime() -> None:
    spx = [date(2014, 10, 3), date(2014, 10, 6)]
    rows, _ = align_origin_panel(
        spx,
        [(date(2014, 10, 3), 15.0), (date(2014, 10, 6), 16.0)],
    )
    assert [row.vix_methodology_regime for row in rows] == [
        "month_only",
        "weekly_inclusive",
    ]


def test_alignment_rejects_non_session_or_invalid_vix() -> None:
    with pytest.raises(ValueError, match="XNYS"):
        align_origin_panel([date(2024, 1, 6)], [])
    with pytest.raises(ValueError, match="strictly positive"):
        align_origin_panel([date(2024, 1, 2)], [(date(2024, 1, 2), 0.0)])
