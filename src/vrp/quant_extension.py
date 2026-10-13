"""Registered exploratory extension: immutable inputs and strict as-of fitting."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, log_loss
from scipy.special import expit, logit
from scipy.optimize import minimize
from scipy.stats import norm

from vrp.calendar import forward_30c_sessions
from vrp.quant_calendar import scheduled_forward_sessions, reaggregate_garch
from vrp.provisional_analysis import inputs, checked_mean, checked_regression, persist
from vrp.data import write_immutable

STATUS = "EXPLORATORY — POST H1–H5 RESULT SELECTION — PENDING INDEPENDENT REVIEW"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/quant_extension/v2"
FLOOR = 1e-8
H6_FEATURES = ["log_ivar", "log_rv21", "log_rv63", "log_downside21", "negative_return", "log_garch"]
H7_FEATURES = ["ivar", "garch", "trailing"]
HAR_FEATURES = ["har1", "har5", "har22"]
PERIODS = {"2012_2016": ("2012-01-01", "2016-12-31"),
           "2017_2021": ("2017-01-01", "2021-12-31"),
           "2022_2025": ("2022-01-01", "2025-12-31"),
           "2020": ("2020-01-01", "2020-12-31"), "2022": ("2022-01-01", "2022-12-31")}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_hash(path, expected):
    if sha(path) != expected:
        raise ValueError(f"Hash mismatch: {path}")


def implementation(files):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    sources = {}
    for name in files:
        raw = (ROOT/name).read_bytes().replace(b"\r\n", b"\n")
        saved = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT)
        if raw != saved.replace(b"\r\n", b"\n"):
            raise ValueError("Commit code before execution: " + name)
        sources[name] = hashlib.sha256(raw).hexdigest()
    return {"commit": commit, "sources_sha256_lf": sources}


def baseline_audit():
    """Check pinned baseline evidence and snapshot all baseline data/checkpoints."""
    meta = json.loads((ROOT/"data/manifests/2026-10-13_h1_h5_execution_v2.json").read_bytes())
    for name, digest in meta["result_sources"].items():
        checked_hash(ROOT/"outputs/empirical_h1_h5/v1"/name, digest)
    for name, digest in meta["report_files"].items():
        checked_hash(ROOT/"docs"/name, digest)
    for name, digest in meta["publication_files"].items():
        checked_hash(ROOT/meta["publication_root"]/name, digest)
    snapshot_path = OUT/"baseline_preservation.json"
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_bytes())
        for name, digest in snapshot.items():
            checked_hash(ROOT/name, digest)
        return snapshot
    paths = []
    for folder in ["data/processed/interim", "outputs/empirical_h1_h5/v1"]:
        paths.extend(p for p in (ROOT/folder).rglob("*") if p.is_file())
    paths.extend(ROOT/"docs"/name for name in meta["report_files"])
    snapshot = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths))}
    persist(snapshot_path, snapshot)
    return snapshot


def source_panel():
    baseline_audit()
    # Preserve baseline parser environment; it remains outside the core lock.
    sys.path.insert(0, str(ROOT/"outputs/archive_inspection"))
    targets, daily, _ = inputs(ROOT)
    path = ROOT/"outputs/empirical_h1_h5/v1/garch/normal_expanding/7c3d01aecf3e612f"
    meta = json.loads((ROOT/"data/manifests/2026-10-13_h1_h5_execution_v2.json").read_bytes())
    source = meta["garch_sources"]["normal_expanding"]
    checked_hash(path/"forecasts.json", source["forecasts_sha256"])
    checked_hash(path/"configuration.json", source["configuration_sha256"])
    records = json.loads((path/"forecasts.json").read_bytes())["records"]
    if len(records) != 4780 or len({r["origin"] for r in records}) != 4780:
        raise ValueError("Cached GARCH coverage mismatch")
    for r in records:
        if r["training_end"] > r["origin"] or r["status"] != "CONVERGED":
            raise ValueError("GARCH information-set mismatch")
    garch = pd.DataFrame({"origin": [r["origin"] for r in records], "garch": [reaggregate_garch(r) for r in records]})
    return build_features(targets, daily, garch)


def build_features(targets, daily, garch):
    dates = pd.to_datetime(daily.Date)
    r = pd.Series(daily.log_return.to_numpy(float), index=dates)
    sq = r*r
    frame = pd.DataFrame(index=dates)
    for n in (21, 63):
        frame[f"log_rv{n}"] = np.log(np.maximum(252*sq.rolling(n).mean(), FLOOR))
    frame["log_downside21"] = np.log(np.maximum(252*r.clip(upper=0).pow(2).rolling(21).mean(), FLOOR))
    frame["negative_return"] = (-r).clip(lower=0)
    frame["trailing"] = sq.rolling("30D", closed="right").sum()*365/30
    frame["ewma_daily"] = sq.ewm(alpha=.06, adjust=False).mean()
    for n in (1, 5, 22):
        frame[f"har{n}"] = np.log(np.maximum(252*sq.rolling(n).mean(), FLOOR))
    frame["origin"] = frame.index.strftime("%Y-%m-%d")
    panel = targets.merge(frame.reset_index(drop=True), on="origin", validate="one_to_one").merge(garch, on="origin", how="inner", validate="one_to_one")
    panel["log_ivar"] = np.log(np.maximum(panel.ivar, FLOOR))
    panel["log_garch"] = np.log(np.maximum(panel.garch, FLOOR))
    panel["y"] = panel.rvar_cc_fwd_30c
    panel["event"] = (panel.y > 1.5*panel.ivar).astype(int)
    panel["maturity"] = pd.to_datetime(panel.origin) + pd.Timedelta(days=30)
    panel["feature_as_of"] = pd.to_datetime(panel.origin)
    panel["ewma"] = [v*len(scheduled_forward_sessions(d))*365/30 for d, v in zip(panel.origin, panel.ewma_daily)]
    return panel.sort_values("origin").reset_index(drop=True)


def matured_training(panel, as_of, features):
    """Reject immature labels and future features inside the fit boundary."""
    now = pd.Timestamp(as_of)
    required = list(dict.fromkeys(features + ["y"]))
    valid = np.isfinite(panel[required].to_numpy(float)).all(axis=1)
    valid &= panel.y.to_numpy() > 0
    valid &= panel.target_status_cc_30c.eq("COMPLETE").to_numpy()
    maturity = pd.to_datetime(panel.origin) + pd.Timedelta(days=30)
    if not maturity.equals(pd.to_datetime(panel.maturity)):
        raise ValueError("Target availability must equal origin+30 calendar days")
    train = panel.loc[valid & (maturity <= now) & (pd.to_datetime(panel.feature_as_of) <= pd.to_datetime(panel.origin))].copy()
    if not train.origin.is_monotonic_increasing or train.origin.duplicated().any():
        raise ValueError("Training chronology invalid")
    if len(train) and (train.maturity.max() > now or pd.to_datetime(train.origin).max() >= now):
        raise ValueError("Immature or future training observation")
    return train


def evaluation_panel(panel):
    required = H6_FEATURES + H7_FEATURES + HAR_FEATURES + ["ewma", "y"]
    sample = panel.loc[(panel.origin >= "2012-01-01") & (panel.origin <= "2025-12-31")].copy()
    valid = np.isfinite(sample[required].to_numpy(float)).all(axis=1) & sample.y.gt(0).to_numpy() & sample.target_status_cc_30c.eq("COMPLETE").to_numpy()
    if not valid.all():
        raise ValueError(f"Incomplete common evaluation: {int((~valid).sum())} rows")
    if len(sample) == 0 or sample.origin.duplicated().any():
        raise ValueError("Empty/duplicate common mask")
    return sample


def csv_immutable(path, frame):
    return write_immutable(path, frame.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode())


def paired(values):
    return {"hac63": checked_mean(values, 63), "hac21": checked_mean(values, 21)}


def block_indices(n, rng, block=63):
    starts = rng.integers(0, n, size=int(np.ceil(n/block)))
    return ((starts[:, None] + np.arange(block)) % n).ravel()[:n]


def bootstrap_pair(a, b, statistic=None):
    a = np.asarray(a); b = np.asarray(b)
    statistic = statistic or (lambda x, z: float((x-z).mean()))
    rng = np.random.default_rng(1729)
    estimates = [statistic(a[i], b[i]) for i in (block_indices(len(a), rng) for _ in range(1000))]
    return {"estimate": statistic(a, b), "ci95": np.quantile(estimates, [.025, .975]).tolist(), "block": 63, "replications": 1000, "seed": 1729}


def holm(tests):
    order = sorted(range(len(tests)), key=lambda i: tests[i]["hac63"]["p_value"])
    bound = 0.
    for rank, i in enumerate(order):
        bound = max(bound, min(1., (len(tests)-rank)*tests[i]["hac63"]["p_value"]))
        tests[i]["holm_p"] = bound


def alert_metrics(y, alerts):
    y = np.asarray(y, int); alerts = np.asarray(alerts, bool)
    tp = int(np.sum(alerts & (y == 1))); fp = int(np.sum(alerts & (y == 0)))
    positives = int(y.sum())
    return {"alerts": int(alerts.sum()), "alert_fraction": float(alerts.mean()), "tp": tp, "fp": fp,
            "fn": positives-tp, "precision": float(tp/alerts.sum()) if alerts.sum() else 0.,
            "recall": float(tp/positives) if positives else 0., "fnr": float(1-tp/positives) if positives else 0.}


def budget_alerts(p):
    order = np.argsort(-np.asarray(p), kind="stable")
    mask = np.zeros(len(p), bool); mask[order[:int(np.ceil(.1*len(p)))]] = True
    return mask


def calibration(y, p):
    """OOS logistic diagnostic; never used to transform forecasts."""
    z = logit(np.clip(p, 1e-6, 1-1e-6)); x = np.column_stack([np.ones(len(z)), z])
    def objective(beta):
        eta = x@beta
        return float(np.sum(np.logaddexp(0, eta)-y*eta)), x.T@(expit(eta)-y)
    fit = minimize(objective, [0., 1.], jac=True, method="BFGS", options={"gtol": 1e-7, "maxiter": 2000})
    prob = expit(x@fit.x)
    score = x*(y-prob)[:, None]; meat = score.T@score
    for lag in range(1, 64):
        c = score[lag:].T@score[:-lag]; meat += (1-lag/64)*(c+c.T)
    bread = np.linalg.pinv(x.T@(x*(prob*(1-prob))[:, None]))
    se = np.sqrt(np.maximum(np.diag(bread@meat@bread), 0))
    bins = []
    for lo in np.arange(0, 1, .1):
        mask = (p >= lo) & ((p < lo+.1) if lo < .9 else (p <= 1))
        bins.append({"lower": float(lo), "n": int(mask.sum()), "predicted": float(p[mask].mean()) if mask.any() else None,
                     "observed": float(y[mask].mean()) if mask.any() else None})
    return {"intercept": float(fit.x[0]), "slope": float(fit.x[1]), "hac63_se": se.tolist(),
            "ci95": np.column_stack([fit.x-1.96*se, fit.x+1.96*se]).tolist(),
            "optimizer_success": bool(fit.success), "gradient_max": float(np.max(np.abs(fit.jac))),
            "message": str(fit.message), "reliability": bins}


def probability_metrics(y, p, live):
    y = np.asarray(y, int); p = np.asarray(p, float)
    if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError("Invalid probability")
    brier = float(np.mean((y-p)**2)); clipped = np.clip(p, 1e-6, 1-1e-6)
    ll = float(-np.mean(y*np.log(clipped)+(1-y)*np.log1p(-clipped)))
    if not np.isclose(brier, brier_score_loss(y, p), atol=1e-15) or not np.isclose(ll, log_loss(y, clipped), atol=1e-15):
        raise ValueError("Independent probability-score oracle failed")
    return {"brier": brier, "log_loss": ll, "roc_auc": float(roc_auc_score(y, p)),
            "pr_auc_average_precision": float(average_precision_score(y, p)),
            "threshold_05": alert_metrics(y, p >= .5), "budget10_retrospective": alert_metrics(y, budget_alerts(p)),
            "live_train_quantile90": alert_metrics(y, p >= live), "calibration": calibration(y, p)}


def fit_h6(train):
    if len(train) < 500 or train.event.nunique() != 2:
        raise ValueError("Insufficient H6 training data")
    models = {}; audit = {"training_n": len(train), "training_events": int(train.event.sum()), "latest_maturity": train.maturity.max().isoformat(), "training_last_origin": train.origin.iloc[-1]}
    models["A"] = (None, (train.event.sum()+.5)/(len(train)+1))
    for name, features in [("B", ["log_ivar"]), ("C", H6_FEATURES), ("D", H6_FEATURES)]:
        scaler = StandardScaler().fit(train[features].to_numpy())
        x = scaler.transform(train[features].to_numpy())
        model = (GradientBoostingClassifier(n_estimators=50, max_depth=2, learning_rate=.05, min_samples_leaf=50, subsample=1., random_state=1729)
                 if name == "D" else LogisticRegression(C=1., solver="lbfgs", max_iter=2000, tol=1e-8))
        model.fit(x, train.event)
        if name != "D" and np.any(model.n_iter_ >= 2000):
            raise ValueError("Logistic convergence failure")
        models[name] = (scaler, model)
        audit[name] = {"features": features, "scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist(),
                       "params": model.get_params(), "threshold90": float(np.quantile(model.predict_proba(x)[:, 1], .9)),
                       "coefficients": model.coef_.tolist() if name != "D" else None,
                       "intercept": model.intercept_.tolist() if name != "D" else None,
                       "feature_importance": model.feature_importances_.tolist() if name == "D" else None}
    audit["A"] = {"probability": float(models["A"][1]), "threshold90": float(models["A"][1])}
    return models, audit


def predict_h6(models, row):
    predictions = {"A": float(models["A"][1])}
    for name in ("B", "C", "D"):
        features = ["log_ivar"] if name == "B" else H6_FEATURES
        scaler, model = models[name]
        predictions[name] = float(model.predict_proba(scaler.transform(row[features].to_numpy(float)[None, :]))[0, 1])
    return predictions


def run_h6(panel):
    sample = evaluation_panel(panel); fits = []; rows = []; previous = None
    for _, row in sample.iterrows():
        month = row.origin[:7]
        if month != previous:
            train = matured_training(panel, row.origin, H6_FEATURES)
            models, audit = fit_h6(train); audit["as_of"] = row.origin; fits.append(audit); previous = month
        predictions = predict_h6(models, row)
        rows.append({"origin": row.origin, "y": int(row.event), "as_of_fit": audit["as_of"],
                     **predictions, **{f"{name}_alert_threshold": audit[name]["threshold90"] for name in predictions}})
    forecasts = pd.DataFrame(rows); y = forecasts.y.to_numpy(); metrics = {}
    for name in ("A", "B", "C", "D"):
        metrics[name] = probability_metrics(y, forecasts[name].to_numpy(), forecasts[f"{name}_alert_threshold"].to_numpy())
    tests = []
    for candidate in ("C", "D"):
        for baseline in ("A", "B"):
            a = (y-forecasts[candidate].to_numpy())**2; b = (y-forecasts[baseline].to_numpy())**2
            test = {"candidate": candidate, "baseline": baseline, **paired(a-b),
                    "relative_brier_reduction": bootstrap_pair(a, b, lambda u, v: float(1-u.mean()/v.mean()))}
            pa = forecasts[candidate].to_numpy(); pb = forecasts[baseline].to_numpy()
            rng = np.random.default_rng(1729); effects = []
            for _ in range(1000):
                i = block_indices(len(y), rng)
                if y[i].sum():
                    effects.append(alert_metrics(y[i], budget_alerts(pa[i]))["recall"]-alert_metrics(y[i], budget_alerts(pb[i]))["recall"])
            test["budget_recall_gain"] = {"estimate": metrics[candidate]["budget10_retrospective"]["recall"]-metrics[baseline]["budget10_retrospective"]["recall"], "ci95": np.quantile(effects, [.025, .975]).tolist()}
            tests.append(test)
    holm(tests)
    periods = {}
    for name, (lo, hi) in PERIODS.items():
        sub = forecasts.loc[forecasts.origin.between(lo, hi)]; yy = sub.y.to_numpy()
        periods[name] = {"n": len(sub), "events": int(yy.sum()), "models": {m: {"brier": float(np.mean((yy-sub[m])**2)), "budget": alert_metrics(yy, budget_alerts(sub[m]))} for m in metrics}}
    digest = csv_immutable(OUT/"h6_forecasts.csv", forecasts)
    return {"status": STATUS, "n": len(forecasts), "events": int(y.sum()), "prevalence": float(y.mean()),
            "models": metrics, "comparisons": tests, "periods": periods, "fits": fits, "failed_fits": 0,
            "forecasts_sha256": digest, "common_origin_sha256": hashlib.sha256("\n".join(forecasts.origin).encode()).hexdigest(),
            "implementation": implementation(["src/vrp/quant_extension.py", "src/vrp/quant_calendar.py", "scripts/run_quant_extension.py"])}
