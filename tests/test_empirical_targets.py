from datetime import date
import math

import pandas as pd
import pytest

from vrp.calendar import exchange_sessions, forward_30c_sessions
from vrp.empirical_targets import construct_targets, audit_targets
from vrp.premium import ivar_from_vix, ivol_from_vix


@pytest.fixture
def inputs():
    dates = exchange_sessions(date(2024,1,2), date(2024,3,15))
    closes = [100*math.exp(.002*i) for i in range(len(dates))]
    spx = pd.DataFrame({"Date": [d.isoformat() for d in dates], "Open": closes,
        "High": [c*1.01 for c in closes], "Low": [c*.99 for c in closes], "Close": closes})
    # A missing VIX at the second SPX session must not remove its return.
    panel = pd.DataFrame([{ "origin": dates[i].isoformat(), "spx_close": closes[i],
        "vix_close": 20., "ivol": ivol_from_vix(20), "ivar": ivar_from_vix(20)} for i in [0,2]])
    return spx, panel


def test_full_returns_despite_missing_nearby_predictor_and_six_formulas(inputs):
    spx, panel = inputs; before = spx.copy(deep=True)
    daily, targets = construct_targets(spx, panel)
    audit = audit_targets(spx, panel, daily, targets)
    pd.testing.assert_frame_equal(spx, before)
    assert len(daily) == len(spx) and daily.log_return.notna().sum() == len(spx)-1
    assert daily.Date.iloc[1] not in set(panel.origin) and math.isfinite(daily.log_return.iloc[1])
    expected = 365/30 * len(forward_30c_sessions(date(2024,1,2))) * .002**2
    assert targets.rvar_cc_fwd_30c.iloc[0] == pytest.approx(expected, abs=1e-14)
    assert targets.rvar_cc_fwd_21t.iloc[0] == pytest.approx(252*.002**2, abs=1e-14)
    assert targets.vrp_x_cc_30c.iloc[0] == pytest.approx(.04-expected)
    assert all(v == {"complete": 2, "missing": 0} for v in audit["counts"].values())


def test_incomplete_support_is_explicit_not_shortened(inputs):
    spx, panel = inputs; spx = spx.iloc[:8].copy()
    daily, targets = construct_targets(spx, panel)
    audit = audit_targets(spx, panel, daily, targets)
    assert all(v["missing"] == 2 for v in audit["counts"].values())
    assert targets.rvar_cc_fwd_30c.isna().all()


@pytest.mark.parametrize("column", ["rvar_cc_fwd_30c", "rvar_parkinson_fwd_21t", "vrp_x_gk_30c",
    "target_session_count_30c", "target_end_date_21t", "target_status_cc_30c"])
def test_independent_audit_detects_target_drift(inputs, column):
    spx, panel = inputs; daily, targets = construct_targets(spx, panel)
    if column == "target_end_date_21t": targets.loc[0,column] = "2024-12-31"
    elif column == "target_status_cc_30c": targets.loc[0,column] = "MISSING_REQUIRED_SESSION"
    else: targets.loc[0,column] += 1
    with pytest.raises(ValueError): audit_targets(spx, panel, daily, targets)


def test_future_outcomes_cannot_change_predictors(inputs):
    spx, panel = inputs; _, first = construct_targets(spx, panel)
    changed = spx.copy(deep=True); changed.loc[5,"Close"] *= 1.001
    _, second = construct_targets(changed, panel)
    pd.testing.assert_frame_equal(first[panel.columns], second[panel.columns])
    assert first.rvar_cc_fwd_30c.iloc[0] != second.rvar_cc_fwd_30c.iloc[0]


def test_mutated_daily_returns_and_ivar_are_rejected(inputs):
    spx, panel = inputs; daily, targets = construct_targets(spx, panel)
    daily.loc[1,"log_return"] = 99
    with pytest.raises(ValueError, match="return audit"):
        audit_targets(spx, panel, daily, targets)
    panel.loc[0,"ivar"] = 400
    with pytest.raises(ValueError, match="Predictor unit"):
        construct_targets(spx, panel)


def test_missing_spx_session_and_duplicate_origins_fail(inputs):
    spx, panel = inputs
    with pytest.raises(ValueError, match="not consecutive"):
        construct_targets(spx.drop(index=5), panel)
    with pytest.raises(ValueError, match="unique"):
        construct_targets(spx, pd.concat([panel,panel]))
