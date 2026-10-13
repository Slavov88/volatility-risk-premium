"""Fixed monthly mature-label physical variance forecasts; no GARCH refitting."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from vrp.quant_extension import (STATUS, OUT, FLOOR, H7_FEATURES, HAR_FEATURES, PERIODS,
    matured_training, evaluation_panel, paired, bootstrap_pair, holm, csv_immutable, implementation)
from vrp.provisional_analysis import checked_regression


def qlike(y, forecast):
    y = np.asarray(y, float); f = np.asarray(forecast, float)
    if y.shape != f.shape or np.any(~np.isfinite(y)) or np.any(~np.isfinite(f)) or np.any(y <= 0) or np.any(f <= 0):
        raise ValueError("QLIKE requires equal positive finite variance arrays")
    ratio = y/f
    loss = ratio-np.log(ratio)-1
    oracle = y/f+np.log(f)-np.log(y)-1
    if not np.allclose(loss, oracle, rtol=1e-11, atol=1e-13):
        raise ValueError("Independent QLIKE identity mismatch")
    return loss


def fit_h7(train):
    if len(train) < 500:
        raise ValueError("Insufficient variance training data")
    models = {}; audit = {"training_n": len(train), "latest_maturity": train.maturity.max().isoformat(),
                          "training_last_origin": train.origin.iloc[-1]}
    for name, features in [("har", HAR_FEATURES), ("combined", H7_FEATURES)]:
        scaler = StandardScaler().fit(train[features].to_numpy())
        x = scaler.transform(train[features].to_numpy())
        target = np.log(train.y.to_numpy()) if name == "har" else train.y.to_numpy()
        model = Ridge(alpha=1., positive=(name == "combined"), fit_intercept=True, tol=1e-8, max_iter=10000)
        model.fit(x, target)
        smearing = float(np.exp(target-model.predict(x)).mean()) if name == "har" else 1.
        models[name] = (scaler, model, smearing)
        rawcoef = model.coef_/scaler.scale_
        audit[name] = {"features": features, "scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist(),
                       "standardized_coefficients": model.coef_.tolist(), "raw_coefficients": rawcoef.tolist(),
                       "raw_intercept": float(model.intercept_-scaler.mean_@rawcoef), "smearing": smearing,
                       "params": model.get_params()}
        if name == "har":
            # Independent centered ridge linear-system solution.
            yc = target-target.mean(); oracle = np.linalg.solve(x.T@x+np.eye(x.shape[1]), x.T@yc)
            if not np.allclose(oracle, model.coef_, rtol=1e-9, atol=1e-11):
                raise ValueError("Independent HAR ridge coefficient mismatch")
        else:
            # Nonnegative ridge KKT check, including intercept centering.
            gradient = x.T@(x@model.coef_+model.intercept_-target)+model.coef_
            active = model.coef_ > 1e-7
            if np.max(np.abs(gradient[active]), initial=0) > 1e-3 or np.min(gradient[~active], initial=0) < -1e-3:
                raise ValueError("Constrained combination KKT check failed")
    return models, audit


def predict_h7(models, row):
    predictions = {name: float(row[column]) for name, column in [("vix", "ivar"), ("garch", "garch"), ("trailing", "trailing"), ("ewma", "ewma")]}
    for name, features in [("har", HAR_FEATURES), ("combined", H7_FEATURES)]:
        scaler, model, smearing = models[name]
        value = float(model.predict(scaler.transform(row[features].to_numpy(float)[None, :]))[0])
        predictions[name] = float(np.exp(value)*smearing) if name == "har" else value
    clipping = {name: int(value < FLOOR) for name, value in predictions.items()}
    predictions = {name: max(FLOOR, value) for name, value in predictions.items()}
    if not all(np.isfinite(list(predictions.values()))):
        raise ValueError("Nonfinite variance forecast")
    return predictions, clipping


def variance_metrics(y, forecast):
    y = np.asarray(y, float); f = np.asarray(forecast, float)
    return {"qlike": float(qlike(y, f).mean()), "rmse": float(np.sqrt(np.mean((y-f)**2))),
            "mae": float(np.mean(np.abs(y-f))), "bias_forecast_minus_actual": float((f-y).mean()),
            "underprediction_1_5_rate": float(np.mean(y > 1.5*f)),
            "calibration_hac63": checked_regression(y, f, 63)}


def run_h7(panel):
    sample = evaluation_panel(panel); fits = []; rows = []; previous = None
    clipcount = {name: 0 for name in ("vix", "garch", "trailing", "ewma", "har", "combined")}
    for _, row in sample.iterrows():
        if row.origin[:7] != previous:
            train = matured_training(panel, row.origin, H7_FEATURES+HAR_FEATURES)
            models, audit = fit_h7(train); audit["as_of"] = row.origin; fits.append(audit); previous = row.origin[:7]
        values, clips = predict_h7(models, row)
        for name, count in clips.items():
            clipcount[name] += count
        rows.append({"origin": row.origin, "y": float(row.y), "as_of_fit": audit["as_of"], **values})
    forecasts = pd.DataFrame(rows); y = forecasts.y.to_numpy()
    metrics = {name: variance_metrics(y, forecasts[name].to_numpy()) for name in clipcount}
    tests = []
    a = qlike(y, forecasts.combined.to_numpy())
    for baseline in ("vix", "garch", "trailing"):
        b = qlike(y, forecasts[baseline].to_numpy())
        tests.append({"candidate": "combined", "baseline": baseline, **paired(a-b),
                      "relative_qlike_reduction": bootstrap_pair(a, b, lambda u, v: float(1-u.mean()/v.mean())),
                      "mse_difference": paired((y-forecasts.combined)**2-(y-forecasts[baseline])**2),
                      "mae_difference": paired(np.abs(y-forecasts.combined)-np.abs(y-forecasts[baseline]))})
    holm(tests)
    periods = {}
    for name, (lo, hi) in PERIODS.items():
        sub = forecasts.loc[forecasts.origin.between(lo, hi)]
        periods[name] = {"n": len(sub), "models": {m: variance_metrics(sub.y.to_numpy(), sub[m].to_numpy()) for m in metrics}}
    digest = csv_immutable(OUT/"h7_forecasts.csv", forecasts)
    import hashlib
    return {"status": STATUS, "n": len(forecasts), "models": metrics, "comparisons": tests, "periods": periods,
            "fits": fits, "failed_fits": 0, "floor_counts": clipcount, "forecasts_sha256": digest,
            "common_origin_sha256": hashlib.sha256("\n".join(forecasts.origin).encode()).hexdigest(),
            "implementation": implementation(["src/vrp/quant_extension.py", "src/vrp/quant_calendar.py", "src/vrp/quant_variance.py", "scripts/run_quant_extension.py"])}
