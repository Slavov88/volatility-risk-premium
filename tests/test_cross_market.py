from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
import exchange_calendars as xc

from vrp.cross_market import build_close_panel


def market_fixture():
    cal = xc.get_calendar("XNYS")
    sessions = [x.date() for x in cal.sessions_in_range("2024-10-01", "2025-03-31")]
    underlying = pd.DataFrame({"day": sessions, "close": np.exp(np.arange(len(sessions)) * .001)})
    implied = pd.DataFrame({"asof": sessions, "level": np.full(len(sessions), 20.0)})
    return cal, sessions, underlying, implied


def test_close_panel_exact_horizons_units_and_target_endpoints():
    cal, sessions, underlying, implied = market_fixture()
    panel = build_close_panel(underlying, implied, underlying_date="day", underlying_close="close",
                              implied_date="asof", implied_close="level", cutoff=date(2025, 1, 31))
    row = panel.loc[panel.origin.eq("2024-11-01")].iloc[0]
    origin = date.fromisoformat(row.origin)
    sessions30 = [x.date() for x in cal.sessions_in_range(origin + timedelta(days=1), origin + timedelta(days=30))]
    sessions21 = [x.date() for x in cal.sessions_in_range(origin + timedelta(days=1), origin + timedelta(days=90))][:21]
    close = dict(zip(sessions, underlying.close))
    returns = {d: np.log(close[d] / close[sessions[sessions.index(d)-1]]) for d in sessions[1:]}
    assert row.implied_points == 20.0
    assert row.ivar == pytest.approx(.04)
    assert row.n_sessions_30c == len(sessions30)
    assert row.target_30c_end == "2024-12-01"
    assert row.target_21t_end == sessions21[-1].isoformat()
    assert row.rvar_30c == pytest.approx(365/30 * sum(returns[d]**2 for d in sessions30))
    assert row.rvar_21t == pytest.approx(252/21 * sum(returns[d]**2 for d in sessions21))


def test_missing_actual_session_excludes_incomplete_forward_targets():
    _, sessions, underlying, implied = market_fixture()
    omitted = sessions[35]
    underlying = underlying.loc[underlying.day.ne(omitted)].reset_index(drop=True)
    panel = build_close_panel(underlying, implied, underlying_date="day", underlying_close="close",
                              implied_date="asof", implied_close="level", cutoff=date(2025, 1, 31))
    touching = panel.loc[(panel.target_30c_start <= omitted.isoformat()) &
                         (panel.target_30c_end >= omitted.isoformat())]
    assert touching.empty


def test_missing_underlying_session_is_not_bridged_into_a_one_day_return():
    _, sessions, underlying, implied = market_fixture()
    missing = sessions[35]
    underlying = underlying.loc[underlying.day.ne(missing)].reset_index(drop=True)
    panel = build_close_panel(underlying, implied, underlying_date="day", underlying_close="close",
                              implied_date="asof", implied_close="level", cutoff=date(2025, 1, 31))
    # Every candidate 30c target intersecting the missing daily return is
    # excluded. The return on the next observed date is not treated as a
    # one-session return spanning the source gap.
    touching = panel.loc[(panel.target_30c_start <= missing.isoformat()) &
                         (panel.target_30c_end >= missing.isoformat())]
    assert touching.empty


def test_duplicate_observation_rejected():
    _, _, underlying, implied = market_fixture()
    implied = pd.concat([implied, implied.iloc[[3]]], ignore_index=True).sort_values("asof")
    with pytest.raises(ValueError, match="unique and ordered"):
        build_close_panel(underlying, implied, underlying_date="day", underlying_close="close",
                          implied_date="asof", implied_close="level", cutoff=date(2025, 1, 31))
