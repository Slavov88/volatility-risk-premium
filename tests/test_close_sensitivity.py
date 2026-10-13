import pandas as pd
import pytest

import vrp.close_sensitivity as sensitivity
from test_empirical_targets import inputs
from vrp.empirical_targets import construct_targets


def test_joint_adjacent_corrections_are_recomputed_and_isolated(inputs, monkeypatch):
    spx, panel = inputs; before = spx.copy(deep=True)
    days = ("2024-01-03", "2024-01-04")
    monkeypatch.setattr(sensitivity, "DISCREPANCY_DATES", days)
    replacements = {d: float(spx.loc[spx.Date == d,"Close"].iloc[0])*1.001 for d in days}
    _, baseline = construct_targets(spx,panel)
    result = sensitivity.evaluate_alternate_closes(spx,baseline,replacements)
    pd.testing.assert_frame_equal(spx,before)
    assert len(result["scenarios"]) == 3 and not result["canonical_source_modified"]
    alternate = spx.copy()
    for d,v in replacements.items(): alternate.loc[alternate.Date == d,"Close"] = v
    _, oracle = construct_targets(alternate,panel)
    joint = result["scenarios"][-1]["horizons"]["30c"]
    assert joint["alternate_mean_vrp_full_sample"] == pytest.approx(oracle.vrp_x_cc_30c.mean(),abs=1e-14)


def test_partial_unregistered_sensitivity_rejected(inputs):
    spx,panel = inputs; _,targets = construct_targets(spx,panel)
    with pytest.raises(ValueError,match="all seven"):
        sensitivity.evaluate_alternate_closes(spx,targets,{"2021-08-11":4447.7})
