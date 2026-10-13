"""Independent CSV-score/share-accounting replay, plus source preservation."""
from datetime import date
import json
import numpy as np
import pandas as pd
from vrp.quant_extension import ROOT, OUT, baseline_audit, sha, persist, checked_hash, source_panel, H6_FEATURES, H7_FEATURES, HAR_FEATURES, matured_training, fit_h6, predict_h6
from vrp.quant_variance import fit_h7, predict_h7
from vrp.calendar import next_exchange_sessions


def run():
    baseline = baseline_audit(); panel = source_panel()
    h6 = json.loads((OUT/"h6.json").read_bytes()); h7 = json.loads((OUT/"h7.json").read_bytes()); h8 = json.loads((OUT/"h8.json").read_bytes())
    checked_hash(OUT/"h6_forecasts.csv", h6["forecasts_sha256"])
    checked_hash(OUT/"h7_forecasts.csv", h7["forecasts_sha256"])
    p6 = pd.read_csv(OUT/"h6_forecasts.csv", float_precision="round_trip")
    p7 = pd.read_csv(OUT/"h7_forecasts.csv", float_precision="round_trip")
    assert p6.origin.tolist() == p7.origin.tolist()
    errors = {}; anchors = []
    for m, metrics in h6["models"].items():
        error = abs(np.sum(np.square(p6.y.to_numpy()-p6[m].to_numpy()))/len(p6)-metrics["brier"])
        assert error < 1e-14; errors["brier_"+m] = float(error)
    for m, metrics in h7["models"].items():
        y = p7.y.to_numpy(); f = p7[m].to_numpy()
        loss = y/f+np.log(f)-np.log(y)-1
        error = abs(loss.sum()/len(y)-metrics["qlike"])
        assert error < 1e-13; errors["qlike_"+m] = float(error)
    for obj in (h6, h7):
        for fit in obj["fits"]:
            assert fit["latest_maturity"][:10] <= fit["as_of"]
            assert pd.Timestamp(fit["training_last_origin"])+pd.Timedelta(days=30) <= pd.Timestamp(fit["as_of"])
    # Replay anchors chosen by ordinal position, independently of forecast quality.
    for i in (0, len(p7)//2, len(p7)-1):
        day = p7.origin.iloc[i]; row = panel.loc[panel.origin.eq(day)].iloc[0]
        asof = p7.as_of_fit.iloc[i]
        models7, audit7 = fit_h7(matured_training(panel, asof, H7_FEATURES+HAR_FEATURES))
        values7, _ = predict_h7(models7, row)
        models6, audit6 = fit_h6(matured_training(panel, asof, H6_FEATURES))
        values6 = predict_h6(models6, row)
        assert all(np.isclose(v, p7[m].iloc[i], rtol=0, atol=1e-15) for m,v in values7.items())
        assert all(np.isclose(v, p6[m].iloc[i], rtol=0, atol=1e-15) for m,v in values6.items())
        anchors.append({"origin": day, "fit_as_of": asof, "h6_and_h7_exact_prediction_replay": True})
    source = h8["source"]; checked_hash(ROOT/source["path"], source["sha256"])
    spy = pd.read_csv(ROOT/source["path"], float_precision="round_trip").set_index("Date")
    accounting_error = 0.; product_error = 0.
    for name,digest in h8["log_sha256"].items():
        checked_hash(OUT/name, digest); log = pd.read_csv(OUT/name, float_precision="round_trip")
        rate = int(name.rsplit("_",1)[1].replace("bps.csv", ""))/10000
        oldq = 0.; oldcash = 1.; previousnav = 1.
        for _, r in log.iterrows():
            day = r.Date; market = spy.loc[day]
            assert next_exchange_sessions(date.fromisoformat(r.signal_origin),1)[0].isoformat() == day
            div = oldq*market.Dividends
            before = oldq*market.Open+oldcash+div
            if r.final_open_mark:
                value = before
                assert r.cost == 0 and r.trade_notional == 0 and r.shares == oldq
            else:
                value = r.shares*market.Close+r.cash
                fee = rate*abs(r.shares-oldq)*market.Open
                assert abs(fee-r.cost) < 1e-12
                assert abs(r.shares*market.Open+r.cash+r.cost-before) < 1e-12
            assert r.cash >= -1e-12 and r.shares >= 0 and r.opening_weight_after_trade <= 1+1e-12
            accounting_error = max(accounting_error,abs(value-r.nav),abs(div-r.dividend_cash),abs(value/previousnav-1-r["return"]))
            oldq, oldcash, previousnav = r.shares, r.cash, value
        product_error = max(product_error,abs(np.prod(1+log["return"])-log.nav.iloc[-1]))
    assert accounting_error < 1e-12 and product_error < 1e-11
    return {"status": "PASSED_INDEPENDENT_SCORE_AND_SHARE_CASH_REPLAY", "baseline_files_preserved": len(baseline),
            "baseline_snapshot_sha256": sha(OUT/"baseline_preservation.json"), "score_max_errors": errors,
            "common_origins": len(p6), "monthly_fits_each": len(h6["fits"]), "anchors": anchors,
            "accounting_max_abs_error": float(accounting_error), "return_product_max_abs_error": float(product_error),
            "h6_sha256": sha(OUT/"h6.json"), "h7_sha256": sha(OUT/"h7.json"), "h8_sha256": sha(OUT/"h8.json")}


if __name__ == "__main__":
    result = run(); print(result); persist(OUT/"independent_audit.json", result)
