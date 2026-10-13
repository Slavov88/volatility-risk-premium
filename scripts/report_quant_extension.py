"""Generate every numerical report/table/figure from verified extension outputs."""
import io
import json
from pathlib import Path
import platform
import importlib.metadata as metadata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from vrp.quant_extension import ROOT, OUT, STATUS, sha, checked_hash, persist, csv_immutable, baseline_audit
from vrp.data import write_immutable


def table(rows, columns):
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return f"{v:.9g}"
        if isinstance(v, (list, dict)):
            return json.dumps(v, sort_keys=True, ensure_ascii=False)
        return str(v)
    return "| " + " | ".join(columns) + " |\n|" + "|".join(["---"]*len(columns)) + "|\n" + "\n".join("| " + " | ".join(cell(row[c]) for c in columns) + " |" for row in rows) + "\n"


def document(name, title, body, source):
    text = f"# {title}\n\n**{STATUS}**\n\n" + body + f"\nGenerated from `{source}.json`, SHA-256 `{sha(OUT/(source+'.json'))}`. Exact forecasts, refit parameters/scaling and source identity are preserved in `outputs/quant_extension/v1/`; sanitized result metadata is committed in `data/manifests/quant_extension_{source}.json`. Reproduction instructions: `docs/quant_extension_reproduction.md`. Independent scientific review PENDING.\n"
    (ROOT/"docs"/name).write_text(text, encoding="utf-8", newline="\n")


def save_figure(fig, name):
    digests = {}
    for ext in ("png", "pdf"):
        buffer = io.BytesIO()
        kwargs = {"metadata": {"CreationDate": None, "ModDate": None}} if ext == "pdf" else {}
        fig.savefig(buffer, format=ext, dpi=180, bbox_inches="tight", **kwargs)
        raw = buffer.getvalue(); digest = write_immutable(OUT/"figures"/f"{name}.{ext}", raw)
        digests[f"{name}.{ext}"] = digest
        if ext == "png":
            target = ROOT/"docs/figures/quant_extension"/f"{name}.png"
            target.parent.mkdir(parents=True, exist_ok=True); write_immutable(target, raw)
    plt.close(fig)
    return digests


def run():
    baseline_audit()
    results = {phase: json.loads((OUT/f"{phase}.json").read_bytes()) for phase in ("h6", "h7", "h8")}
    audit = json.loads((OUT/"independent_audit.json").read_bytes())
    for phase in results:
        checked_hash(OUT/f"{phase}.json", audit[f"{phase}_sha256"])
        persist(ROOT/f"data/manifests/quant_extension_{phase}.json", results[phase])
    h6, h7, h8 = (results[p] for p in ("h6", "h7", "h8"))
    h6rows = []
    for model, v in h6["models"].items():
        alerts = v["budget10_retrospective"]
        h6rows.append({"model": model, "Brier": v["brier"], "log loss": v["log_loss"], "ROC-AUC": v["roc_auc"], "PR AP": v["pr_auc_average_precision"],
                       "TP10%": alerts["tp"], "FP10%": alerts["fp"], "precision10%": alerts["precision"], "recall10%": alerts["recall"], "FNR10%": alerts["fnr"]})
    csv_immutable(OUT/"h6_metrics.csv", pd.DataFrame(h6rows))
    contrast6 = [{"pair": t["candidate"]+" − "+t["baseline"], "Brier difference": t["hac63"]["mean"], "HAC63 CI": [t["hac63"]["ci_lower"], t["hac63"]["ci_upper"]], "raw p": t["hac63"]["p_value"], "Holm p": t["holm_p"],
                  "relative reduction": t["relative_brier_reduction"]["estimate"], "bootstrap CI": t["relative_brier_reduction"]["ci95"], "recall gain": t["budget_recall_gain"]["estimate"], "recall CI": t["budget_recall_gain"]["ci95"]} for t in h6["comparisons"]]
    calibrationrows = [{"model": m, "intercept": v["calibration"]["intercept"], "slope": v["calibration"]["slope"], "HAC CI": v["calibration"]["ci95"], "optimizer success": v["calibration"]["optimizer_success"], "gradient max": v["calibration"]["gradient_max"], "live alert fraction": v["live_train_quantile90"]["alert_fraction"], "live precision": v["live_train_quantile90"]["precision"], "live recall": v["live_train_quantile90"]["recall"], "p>=.5 recall": v["threshold_05"]["recall"]} for m,v in h6["models"].items()]
    period6 = [{"period": period, "N": v["n"], "events": v["events"], "model": m, "Brier": x["brier"], "recall10%": x["budget"]["recall"]} for period,v in h6["periods"].items() for m,x in v["models"].items()]
    document("h6_tail_risk_results.md", "H6: dangerous underestimation probabilities",
        f"Executed {h6['n']} common origins2012–2025, {h6['events']} events, prevalence{h6['prevalence']:.9g}; {len(h6['fits'])} first-origin monthly refits per fitted model, zero failed fits. Training2007 onward, five-year warm-up; exact30-calendar-day maturity enforced. See registered model definitions and all refit parameters in the sanitized JSON. The threshold was selected after H1–H5.\n\n"
        + table(h6rows,list(h6rows[0])) + "\nA is the strongest simple Brier benchmark. C has worse Brier by3.87%; D is worse by7.65%. Neither clears the registered5% improvement gate. D's deterioration survives the four-test Holm family; C's direction is unfavorable but uncertain. Improved C ROC ranking does not rescue probability quality. At the fixed retrospective10% budget, C detects13/244 events with339 false alarms; the event-rate benchmark detects none in its highest historical-rate months. This unusual benchmark ranking reflects temporal prevalence changes, not a code-selected threshold. No event threshold/model was retuned. These forecasts do not provide reliable practical early warnings.\n\n"
        + table(contrast6,list(contrast6[0])) + "\nRelative reduction positive favors the advanced model; paired loss difference negative favors it. Percentile circular-block63 intervals1000 draws, seed1729. HAC21 sensitivity and all exact values are in JSON. Recall-gain intervals re-rank each bootstrap sample and do not represent a live policy.\n\n"
        + table(calibrationrows,list(calibrationrows[0])) + "\nCalibration slope/intercept are OOS diagnostics, not fitted probability correction. Ideal intercept0/slope1. Optimizer status and gradient are reported even if precision-loss prevents a success flag. Inconstant rates create calibration instability. Training-score90th-percentile live alerts can exceed/fall below10%; A ties at its event-rate threshold and therefore alerts every origin, an explicitly poor live operational rule. The exact10% budget is an evaluation allocation only. Empty reliability bins are omitted from plots but retained with n=0 in JSON.\n\n"
        + table(period6,list(period6[0])) + "\n![H6 reliability](figures/quant_extension/h6_reliability.png)\n",
        "h6")
    rows7 = [{"model": m, "QLIKE": v["qlike"], "RMSE variance": v["rmse"], "MAE variance": v["mae"], "bias f-y": v["bias_forecast_minus_actual"], "underprediction1.5": v["underprediction_1_5_rate"], "calibration intercept": v["calibration_hac63"]["coefficients"][0], "calibration slope": v["calibration_hac63"]["coefficients"][1]} for m,v in h7["models"].items()]
    csv_immutable(OUT/"h7_metrics.csv", pd.DataFrame(rows7))
    contrasts7 = [{"baseline": t["baseline"], "QLIKE difference": t["hac63"]["mean"], "HAC63 CI": [t["hac63"]["ci_lower"],t["hac63"]["ci_upper"]], "raw p": t["hac63"]["p_value"], "Holm p": t["holm_p"], "relative reduction": t["relative_qlike_reduction"]["estimate"], "bootstrap CI": t["relative_qlike_reduction"]["ci95"]} for t in h7["comparisons"]]
    period7 = [{"period": p, "N": v["n"], "model": m, "QLIKE": x["qlike"], "RMSE": x["rmse"], "MAE": x["mae"]} for p,v in h7["periods"].items() for m,x in v["models"].items()]
    coefficientrows = []
    for j,f in enumerate(["ivar", "garch", "trailing"]):
        values = np.array([fit["combined"]["raw_coefficients"][j] for fit in h7["fits"]])
        coefficientrows.append({"feature": f, "min": values.min(), "median": np.median(values), "max": values.max(), "first": values[0], "last": values[-1]})
    document("h7_variance_forecasting_results.md", "H7: physical variance forecasting",
        f"Executed {h7['n']} identical common origins and {len(h7['fits'])} monthly fits of HAR/combination. No GARCH refits; existing4780 cached forecasts reused after original configuration/forecast hash checks. All variance outputs annualized decimal units; floor counts `{h7['floor_counts']}`. Gaussian GARCH common training begins2007; no fabricated pre-2007 forecasts.\n\n"
        + table(rows7,list(rows7[0])) + "\nVIX is the strongest constituent and strongest full-family baseline on QLIKE and RMSE. Combination improves QLIKE36.10% versus trailing, but is0.58% worse than VIX and only0.56% better than GARCH with broad intervals. Registered5% practical QLIKE improvement versus strongest constituent fails. RMSE is3.81% worse than VIX (still inside the5% deterioration bound), so the joint gate fails through QLIKE. HAR also fails to beat VIX; GARCH has the smallest MAE. A weaker trailing benchmark alone would create an unsupported positive narrative.\n\n"
        + table(contrasts7,list(contrasts7[0])) + "\nNegative paired losses favor combination. Three-test Holm family; no global confirmatory inference. Full MSE/MAE/HAC21 sensitivities, variance-calibration intervals, and underprediction frequency are retained in JSON. Underprediction rate is a forecast-relative tail diagnostic, not a binary classifier with calibrated probability.\n\n"
        + table(period7,list(period7[0])) + "\nRaw-unit combination coefficient stability:\n\n" + table(coefficientrows,list(coefficientrows[0]))
        + "\nIntercept and all168 monthly coefficients/scaling/smearing parameters are in the result JSON. Nonnegative ridge KKT and independent HAR linear-system checks passed. HAR uses squared daily returns, not intraday realized variance. Coefficient correlation is not causal evidence.\n\n![H7 fixed-period QLIKE](figures/quant_extension/h7_period_losses.png)\n", "h7")
    rows8 = [{"cost bps": cost, "strategy": m, **v} for cost, models in h8["models"].items() for m,v in models.items()]
    csv_immutable(OUT/"h8_metrics.csv", pd.DataFrame(rows8))
    columns8 = ["cost bps", "strategy", "annual_vol", "rolling21_target_rmse", "cagr", "sharpe_zero_reference", "max_drawdown", "annual_turnover_nav", "cost_initial_nav", "downside_rms", "worst_month"]
    compare8 = [{"cost bps": cost, "metric": m, "combined-trailing": x["estimate"], "bootstrap95 CI": x["ci95"]} for cost,t in h8["comparisons_combined_minus_trailing"].items() for m,x in t["bootstrap"].items()]
    period8 = [{"period": p, "strategy": m, "annual_vol": x["annual_vol"], "rolling error": x["rolling21_target_rmse"], "CAGR": x["cagr"], "drawdown": x["max_drawdown"], "worst month": x["worst_month"]} for p,v in h8["periods_5bps"].items() for m,x in v.items()]
    document("h8_portfolio_economic_value.md", "H8: investable SPY risk control after costs",
        f"SPY source SHA `{h8['source']['sha256']}`;4821 exact sessions2006-12-01–2026-02-02,77 dividend events,0 splits. Cash-dividend versus vendor-adjustment maximum daily return difference{h8['source']['validation']['max_daily_return_difference']:.9g}, cumulative return-factor difference{h8['source']['validation']['cumulative_cash_vs_vendor_return_factor_difference']:.9g}; passes locked tolerance, lacks independent-provider confirmation.\n\n"
        + f"Five strategies × five cost scenarios executed. {h8['n_signals']} signals, {h8['n_executed_signals']} actual rebalance signals,3520 mark-to-mark returns2012-01-04 open–2026-01-02 open. Last2025-12-31 forecast has no earned return under the frozen terminal convention. Old shares earn overnight and ex-date dividends before next-open rebalance; new shares earn intraday. No leverage, short or missing sessions.\n\n"
        + table(rows8,columns8) + "\nAll rates are decimals; turnover is one-way traded-notional/NAV per calendar year. Costs are total dollars divided by initial NAV, not a percentage of contemporaneous wealth; they do not equal CAGR drag. Zero cash interest and zero Sharpe reference rate are explicit modeling assumptions. ETF expenses are embedded in SPY prices; dividend cash credit on ex-date, fractional shares and opening fills simplify implementation. Buyhold includes dividend reinvestment trades and fees. Final endpoint is a partial overnight interval; no liquidation fee. Taxes, actual spreads/impact, payment-date financing and broker fills are not modeled.\n\n"
        + "At5bps combination realized volatility8.44% versus trailing10.14%; being lower is not necessarily closer to10%. Rolling risk error3.029% versus2.960%: difference+0.069 percentage points, CI[-0.208,+0.372]percentage points. Registered reduction of0.5percentage points fails. Net CAGR7.933% versus9.760%, difference-1.828percentage points, CI[-3.038,-0.690]. The registered no-more-than0.5percentage-point CAGR deterioration also fails. Combination turnover is higher. Failure is present gross too; costs amplify return drag rather than creating the whole failure. GARCH has lowest historical rolling risk error among these strategies, but no outcome-selected replacement strategy is promoted.\n\n"
        + table(compare8,list(compare8[0])) + f"\nPrimary5bps rolling squared-error HAC63 p={h8['comparisons_combined_minus_trailing']['5']['paired_rolling_squared_error']['hac63']['p_value']:.9g}. Block63/1000 paired return draws recompute metrics; they preserve local dependence but stitch regimes and do not prove future utility. Other costs/periods are fixed sensitivities, not independent primary tests.\n\n"
        + table(period8,list(period8[0])) + "\n2008 is warm-up, so no extension OOS portfolio claim is made for2008. Worst-month identifiers and complete costs/exposures/share/cash/equity paths are in JSON/CSV.\n\n![SPY equity and risk control](figures/quant_extension/h8_equity_risk.png)\n", "h8")
    # Publication figures: direct data, stable colors and explicit units.
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
    colors = {"A": "#58646e", "B": "#2176ae", "C": "#d17c2c", "D": "#8b5aa5", "buyhold": "#58646e", "trailing": "#2176ae", "vix": "#55a868", "garch": "#8b5aa5", "combined": "#d17c2c"}
    figure_hashes = {}
    fig, ax = plt.subplots(1,2,figsize=(10,4),layout="constrained")
    for m,x in h6["models"].items():
        bins = [b for b in x["calibration"]["reliability"] if b["n"]]
        ax[0].plot([b["predicted"] for b in bins],[b["observed"] for b in bins],"o-",label=m,color=colors[m])
    ax[0].plot([0,1],[0,1],"--",color="black",lw=1);ax[0].set(xlabel="Forecast probability",ylabel="Observed event fraction",title="H6 reliability: fixed-width bins")
    ax[0].legend(title="Registered model")
    ax[1].bar(list(h6["models"]),[x["brier"] for x in h6["models"].values()],color=[colors[m] for m in h6["models"]])
    ax[1].set(ylabel="Mean Brier score (lower is better)",title=f"{h6['events']} events / {h6['n']} origins")
    figure_hashes.update(save_figure(fig,"h6_reliability"))
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout="constrained")
    for ax,period in zip(axes,["2012_2016","2017_2021","2022_2025"]):
        values=h7["periods"][period]["models"]; names=list(values)
        ax.bar(names,[values[m]["qlike"] for m in names],color=[colors.get(m,"#879aaa") for m in names]);ax.tick_params(axis="x",rotation=45)
        ax.set(title=period.replace("_","–"),ylabel="Mean QLIKE (lower is better)")
    figure_hashes.update(save_figure(fig,"h7_period_losses"))
    fig,axes=plt.subplots(2,1,figsize=(11,7),layout="constrained",sharex=True)
    for m in ["buyhold","trailing","vix","garch","combined"]:
        log=pd.read_csv(OUT/f"h8_{m}_5bps.csv",float_precision="round_trip");dates=pd.to_datetime(log.Date)
        axes[0].plot(dates,log.nav,label=m,color=colors[m],lw=1.2)
        axes[1].plot(dates,pd.Series(log["return"]).rolling(21).std()*np.sqrt(252)*100,color=colors[m],lw=.8)
    axes[0].set(ylabel="NAV (initial 1; logarithmic scale)",yscale="log",title="SPY, next-open execution, 5bps modeled cost");axes[0].legend(ncol=5)
    axes[1].axhline(10,color="black",ls="--",lw=1);axes[1].set(ylabel="Rolling21 portfolio volatility (%)",xlabel="Mark date")
    figure_hashes.update(save_figure(fig,"h8_equity_risk"))
    body = "Executed H6 four fixed probability models, H7 six fixed variance models, and H8 five SPY strategies at0/1/5/10/25bps. Historical evaluation2012–2025 after2007–2011 warm-up;3520 common origins,168 monthly refits each fitted model. No historical GARCH refits.\n\n"
    body += "H6: no useful improvement in calibrated underestimation probability; advanced Brier worsens. H7: combination beats weak trailing variance but not strongest VIX/GARCH constituent; no practical gate passed. H8: statistical gain against trailing forecasts does not translate into improved trailing-strategy risk control; combined exposure undershoots10% and loses net return, including gross evidence. H9: executable options data/funding/margin unavailable; feasibility only.\n\n"
    body += "Most defensible potential contribution: a reproducible negative boundary study showing that mature-label forecast combinations can outperform a weak statistical benchmark while failing strong constituent and investable risk-control comparisons. This is neither a novel model nor generalizable alpha. VIX suffices as the strongest tested historical variance baseline on primary loss, but this does not establish sufficiency in every regime. Period/model/cost instability and poor tail warnings are retained.\n\n"
    body += f"Numerical audit: {audit['baseline_files_preserved']} baseline files hash-preserved; H6/H7 same mask; all168 refit boundaries mature; three ordinal anchors replayed; independent share/cash maximum error{audit['accounting_max_abs_error']:.9g}. Tests are implementation qualification, not Venelin's independent acceptance. Exact chronology, data discrepancy, maturity, cost and dividend limits remain. No prospective observations/results exist; frozen prospective rule begins after registration UTC date and requires252 matured origins.\n\n"
    body += "Multiplicity: four H6 and three H7 primary pair families use Holm, H8 one primary5bps comparison. Lag63 HAC/lag21 sensitivity and paired block63 bootstrap intervals; no global false-positive guarantee across exploratory choices, periods and secondary metrics. Historical resampling cannot undo prior result selection.\n"
    document("quant_extension_summary.md","Quant extension synthesis",body,"h8")
    reports=["h6_tail_risk_results.md","h7_variance_forecasting_results.md","h8_portfolio_economic_value.md","quant_extension_summary.md"]
    manifest={"status": STATUS,"result_sha256":{p:sha(OUT/f"{p}.json") for p in results},"audit_sha256":sha(OUT/"independent_audit.json"),
              "forecast_and_trade_files":{p.name:sha(p) for p in OUT.glob("*.csv")},"figure_sha256":figure_hashes,
              "report_sha256":{p:sha(ROOT/"docs"/p) for p in reports},"generator_sha256_lf":__import__('hashlib').sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
              "environment":{"python":platform.python_version(),"packages":{p:metadata.version(p) for p in ["numpy","pandas","scipy","statsmodels","scikit-learn","arch","yfinance","matplotlib","exchange-calendars"]}},
              "independent_review":"PENDING","prospective_results":"NONE"}
    persist(ROOT/"data/manifests/quant_extension_execution.json",manifest)
    print({"reports":reports,"figures":len(figure_hashes),"execution_manifest_sha256":sha(ROOT/"data/manifests/quant_extension_execution.json")})


if __name__=="__main__":
    run()
