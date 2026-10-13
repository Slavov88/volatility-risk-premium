import numpy as np
import pandas as pd
import pytest
from vrp.quant_extension import H7_FEATURES, HAR_FEATURES, matured_training
from vrp.quant_variance import qlike, fit_h7, predict_h7
from test_quant_extension import training_panel


def variance_panel():
    p = training_panel(); rng = np.random.default_rng(18)
    for f in H7_FEATURES:
        p[f] = rng.uniform(.001, .1, len(p))
    for f in HAR_FEATURES:
        p[f] = rng.normal(-4, 1, len(p))
    p["ewma"] = .02
    return p


def test_qlike_units_positivity_and_identity():
    y = np.array([.01, .03]); f = np.array([.02, .02])
    assert qlike(y, f) == pytest.approx([.5-np.log(.5)-1, 1.5-np.log(1.5)-1])
    assert qlike(y*100, f*100) == pytest.approx(qlike(y, f))
    assert qlike(y, y) == pytest.approx([0, 0])
    with pytest.raises(ValueError):
        qlike(y, np.array([0., .02]))


def test_variance_future_perturbation_and_coefficients():
    p = variance_panel(); asof = p.origin.iloc[700]; row = p.iloc[700].copy()
    models, audit = fit_h7(matured_training(p, asof, H7_FEATURES+HAR_FEATURES))
    pred, _ = predict_h7(models, row)
    future = p.maturity > pd.Timestamp(asof)
    p.loc[future, H7_FEATURES+HAR_FEATURES+["y"]] = 1e8
    new, newaudit = fit_h7(matured_training(p, asof, H7_FEATURES+HAR_FEATURES))
    assert audit == newaudit
    assert pred == predict_h7(new, row)[0]
    assert min(pred.values()) > 0
    assert min(audit["combined"]["raw_coefficients"]) >= 0
