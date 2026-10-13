"""Adversarial information-set and score contracts for the extension."""
import numpy as np
import pandas as pd
import pytest
from vrp.quant_extension import (matured_training, fit_h6, predict_h6, H6_FEATURES,
    probability_metrics, budget_alerts, csv_immutable, checked_hash, sha)


def training_panel(n=900):
    rng = np.random.default_rng(19)
    dates = pd.date_range("2007-01-03", periods=n, freq="B")
    data = pd.DataFrame(rng.normal(size=(n, 6)), columns=H6_FEATURES)
    data["origin"] = dates.strftime("%Y-%m-%d")
    data["maturity"] = dates + pd.Timedelta(days=30)
    data["feature_as_of"] = dates
    data["y"] = rng.uniform(.001, .1, n)
    data["event"] = rng.binomial(1, .1, n)
    data["target_status_cc_30c"] = "COMPLETE"
    return data


def test_exact_maturity_and_incomplete_labels():
    p = training_panel(10); asof = p.maturity.iloc[3]
    t = matured_training(p, asof, H6_FEATURES)
    assert len(t) == 4 and t.maturity.max() == asof
    p.loc[0, "y"] = np.nan; p.loc[1, "target_status_cc_30c"] = "INCOMPLETE"
    assert len(matured_training(p, asof, H6_FEATURES)) == 2
    p.loc[2, "maturity"] -= pd.Timedelta(days=1)
    with pytest.raises(ValueError, match="origin\+30"):
        matured_training(p, asof, H6_FEATURES)


def test_future_features_excluded_and_disorder_rejected():
    p = training_panel(10); p.loc[0, "feature_as_of"] += pd.Timedelta(days=1)
    assert len(matured_training(p, p.maturity.iloc[-1], H6_FEATURES)) == 9
    with pytest.raises(ValueError, match="chronology"):
        matured_training(p.iloc[::-1], p.maturity.iloc[-1], H6_FEATURES)


def test_future_perturbations_do_not_affect_fit_scaling_or_prediction():
    p = training_panel(); asof = p.origin.iloc[700]
    old = matured_training(p, asof, H6_FEATURES); models, audit = fit_h6(old)
    row = p.iloc[700]; before = predict_h6(models, row)
    future = p.maturity > pd.Timestamp(asof)
    p.loc[future, H6_FEATURES + ["y"]] = 1e10
    p.loc[future, "event"] = 1
    newmodels, newaudit = fit_h6(matured_training(p, asof, H6_FEATURES))
    assert audit == newaudit
    assert before == predict_h6(newmodels, row)


def test_scores_budget_and_calibration():
    y = np.tile([0, 1], 100); p = np.tile([.2, .8], 100)
    m = probability_metrics(y, p, np.repeat(.7, 200))
    assert m["brier"] == pytest.approx(.04)
    assert m["log_loss"] == pytest.approx(-np.log(.8))
    assert budget_alerts(np.ones(100)).sum() == 10
    assert np.flatnonzero(budget_alerts(np.ones(100))).tolist() == list(range(10))
    assert m["threshold_05"]["fnr"] == 0
    with pytest.raises(ValueError):
        probability_metrics(y, np.repeat(2., 200), p)


def test_hash_and_immutable_rerun(tmp_path):
    p = tmp_path/"f.csv"; frame = pd.DataFrame({"a": [.01, .2]})
    csv_immutable(p, frame); digest = sha(p)
    csv_immutable(p, frame); checked_hash(p, digest)
    with pytest.raises(Exception):
        csv_immutable(p, pd.DataFrame({"a": [1., 2.]}))
    p.write_text("corruption")
    with pytest.raises(ValueError, match="Hash"):
        checked_hash(p, digest)
