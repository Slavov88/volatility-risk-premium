import pytest
from vrp.regime_analysis import parse_nber


def html(extra=""):
    return ('''<table><tr><td>July 1990 (1990Q3)</td><td>March 1991 (1991Q1)</td></tr>
    <tr><td>March 2001 (2001Q1)</td><td>November 2001 (2001Q4)</td></tr>
    <tr><td>December 2007 (2007Q4)</td><td>June 2009 (2009Q2)</td></tr>
    <tr><td>February 2020 (2019Q4)</td><td>April 2020 (2020Q2)</td></tr>'''+extra+'</table>').encode()


def test_monthly_rule_uses_month_not_quarter_and_peak_exclusive():
    rows=parse_nber(html());flags={r['month']:r['recession'] for r in rows}
    assert len(rows)==432 and sum(flags.values())==36
    assert flags['2020-02']==0 and flags['2020-03']==flags['2020-04']==1 and flags['2020-05']==0
    assert flags['1990-07']==0 and flags['1990-08']==1 and flags['1991-03']==1 and flags['1991-04']==0


def test_missing_changed_or_duplicate_turning_points_rejected():
    for raw in [b'no table',html().replace(b'March 1991',b'April 1991'),html('<tr><td>February 2020 (2019Q4)</td><td>April 2020 (2020Q2)</td></tr>')]:
        with pytest.raises(ValueError):parse_nber(raw)
