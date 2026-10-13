"""Self-financing SPY execution: old overnight holdings, next-open rebalance."""
from datetime import date, datetime, timezone
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from vrp.calendar import exchange_sessions, next_exchange_sessions
from vrp.quant_extension import (ROOT, OUT, STATUS, sha, checked_hash, csv_immutable, persist,
    implementation, block_indices, paired, PERIODS)


def validate_spy(frame):
    required = ["Open", "High", "Low", "Close", "Adj Close", "Dividends", "Stock Splits"]
    if frame.Date.duplicated().any() or not frame.Date.is_monotonic_increasing:
        raise ValueError("SPY duplicate/disordered dates")
    expected = [d.isoformat() for d in exchange_sessions(date(2006, 12, 1), date(2026, 2, 2))]
    if frame.Date.tolist() != expected:
        raise ValueError("SPY missing or extra exchange sessions")
    x = frame[required].to_numpy(float)
    if not np.isfinite(x).all() or (x[:, :5] <= 0).any() or (x[:, 5:] < 0).any():
        raise ValueError("SPY invalid prices/actions")
    if not ((frame.High >= frame[["Open", "Close"]].max(axis=1)) & (frame.Low <= frame[["Open", "Close"]].min(axis=1)) & (frame.High >= frame.Low)).all():
        raise ValueError("SPY OHLC inconsistency")
    if frame["Stock Splits"].ne(0).any():
        raise ValueError("Nonzero split requires independently validated unit conversion")
    cash_return = ((frame.Close+frame.Dividends)/frame.Close.shift(1)-1).iloc[1:].to_numpy()
    vendor_return = frame["Adj Close"].pct_change(fill_method=None).iloc[1:].to_numpy()
    error = cash_return-vendor_return
    cumulative_difference = float(np.prod(1+cash_return)/np.prod(1+vendor_return)-1)
    if np.max(np.abs(error)) > .002 or abs(cumulative_difference) > .01:
        raise ValueError("SPY total-return validation gate failed")
    return {"rows": len(frame), "start": frame.Date.iloc[0], "end": frame.Date.iloc[-1],
            "missing_sessions": 0, "splits": 0, "dividend_events": int(frame.Dividends.gt(0).sum()),
            "max_daily_return_difference": float(np.max(np.abs(error))),
            "cumulative_cash_vs_vendor_return_factor_difference": cumulative_difference,
            "max_daily_difference_date": frame.Date.iloc[1+int(np.argmax(np.abs(error)))],
            "independent_provider_validation": "NOT_AVAILABLE; internal action/adjustment consistency only"}


def acquire_spy():
    pointer = ROOT/"data/manifests/quant_extension_spy.json"
    if pointer.exists():
        meta = json.loads(pointer.read_bytes()); checked_hash(ROOT/meta["path"], meta["sha256"])
        frame = pd.read_csv(ROOT/meta["path"], float_precision="round_trip")
        if validate_spy(frame) != meta["validation"]:
            raise ValueError("SPY validation replay mismatch")
        return frame, meta
    stamp = datetime.now(timezone.utc).isoformat()
    frame = yf.Ticker("SPY").history(start="2006-12-01", end="2026-02-03", auto_adjust=False,
                                    actions=True, repair=False, raise_errors=True)
    if frame.empty:
        raise ValueError("Empty SPY provider response")
    frame = frame.reset_index()
    frame["Date"] = frame.Date.dt.strftime("%Y-%m-%d")
    validation = validate_spy(frame)
    directory = ROOT/"data/raw"/datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")/"quant_extension_spy"
    digest = csv_immutable(directory/"spy_ohlc_actions.csv", frame)
    meta = {"provider": "Yahoo Finance via yfinance", "symbol": "SPY", "retrieved_utc": stamp,
            "parameters": {"start": "2006-12-01", "end_exclusive": "2026-02-03", "auto_adjust": False,
                           "actions": True, "repair": False, "raise_errors": True},
            "tls": "normal provider library certificate verification; no overrides",
            "yfinance": yf.__version__, "path": (directory/"spy_ohlc_actions.csv").relative_to(ROOT).as_posix(),
            "sha256": digest, "validation": validation,
            "limitations": "Vendor OHLC/actions, not executable historical quotes. Dividend ex-date cash credit; no external provider validation."}
    persist(directory/"source_manifest.json", meta); persist(pointer, meta)
    return frame, meta


def rebalance(shares, cash, opening, weight, cost_rate):
    if not (0 <= weight <= 1) or not (0 <= cost_rate < 1) or opening <= 0 or shares < 0 or cash < -1e-12:
        raise ValueError("Invalid long-only self-financing state")
    held = shares*opening; nav = held+cash
    if nav <= 0:
        raise ValueError("Nonpositive NAV")
    desired = weight*nav-held
    cost = (cost_rate*desired/(1+cost_rate*weight) if desired >= 0
            else cost_rate*(-desired)/(1-cost_rate*weight))
    newnav = nav-cost; newshares = weight*newnav/opening; newcash = (1-weight)*newnav
    traded = abs(newshares-shares)*opening
    if not np.isclose(cost, cost_rate*traded, rtol=1e-10, atol=1e-14) or not np.isclose(newshares*opening+newcash+cost, nav, atol=1e-13):
        raise ValueError("Self-financing accounting failed")
    if newcash < -1e-12 or newshares < 0:
        raise ValueError("Unreported leverage")
    return newshares, newcash, cost, traded


def simulate_spy(spy, signals, weights, cost_bps):
    if len(signals) != len(weights) or signals.origin.duplicated().any() or not signals.origin.is_monotonic_increasing:
        raise ValueError("Signal chronology mismatch")
    market = spy.set_index("Date")
    dates = signals.origin.tolist()
    executions = [next_exchange_sessions(date.fromisoformat(s), 1)[0].isoformat() for s in dates]
    schedule = dict(zip(executions, zip(dates, weights)))
    first, final = executions[0], executions[-1]
    trading_dates = [d.isoformat() for d in exchange_sessions(date.fromisoformat(first), date.fromisoformat(final))]
    if not set(trading_dates).issubset(market.index):
        raise ValueError("Missing SPY execution sessions")
    if not set(trading_dates).issubset(schedule):
        raise ValueError("Missing common forecast signal")
    shares = 0.; cash = 1.; previous = 1.; records = []
    for day in trading_dates:
        row = market.loc[day]; opening = float(row.Open); closing = float(row.Close)
        oldshares = shares; dividend = oldshares*float(row.Dividends); cash += dividend
        nav_open = shares*opening+cash
        origin, weight = schedule[day]
        if origin >= day:
            raise ValueError("Signal precedes no execution time")
        if day == final:
            # Registered next-open endpoint: final origin has no earned return.
            cost = 0.; traded = 0.; nav_close = nav_open; final_mark = True
        else:
            shares, cash, cost, traded = rebalance(shares, cash, opening, float(weight), cost_bps/10000)
            nav_close = shares*closing+cash; final_mark = False
        realized_weight = shares*opening/(shares*opening+cash)
        if not 0 <= realized_weight <= 1+1e-12 or cash < -1e-12:
            raise ValueError("Exposure bounds failed")
        records.append({"Date": day, "signal_origin": origin, "final_open_mark": final_mark,
                        "target_weight": float(weight), "opening_weight_after_trade": realized_weight,
                        "old_shares": oldshares, "shares": shares, "cash": cash, "dividend_cash": dividend,
                        "nav_open_before_cost": nav_open, "trade_notional": traded, "turnover_nav": traded/nav_open,
                        "cost": cost, "nav": nav_close, "return": nav_close/previous-1})
        previous = nav_close
    return pd.DataFrame(records)


def rolling_volatility(returns):
    return pd.Series(returns).rolling(21).std(ddof=1).to_numpy()*np.sqrt(252)


def portfolio_metrics(log):
    r = log["return"].to_numpy(); vol = float(r.std(ddof=1)*np.sqrt(252)); rolling = rolling_volatility(r)[20:]
    nav = np.r_[1., log.nav.to_numpy()]; peak = np.maximum.accumulate(nav)
    years = (pd.Timestamp(log.Date.iloc[-1])-pd.Timestamp(log.Date.iloc[0])).days/365.25
    if years <= 0:
        years = len(r)/252
    months = pd.DataFrame({"month": pd.to_datetime(log.Date).dt.strftime("%Y-%m"), "r": r}).groupby("month").r.apply(lambda x: float(np.prod(1+x)-1))
    return {"n": len(r), "start": log.Date.iloc[0], "end_open": log.Date.iloc[-1], "terminal_nav": float(nav[-1]),
            "annual_vol": vol, "abs_target_deviation": abs(vol-.1),
            "rolling21_target_rmse": float(np.sqrt(np.mean((rolling-.1)**2))),
            "max_drawdown": float(np.min(nav/peak-1)), "cagr": float(nav[-1]**(1/years)-1),
            "sharpe_zero_reference": float(r.mean()/r.std(ddof=1)*np.sqrt(252)),
            "annual_turnover_nav": float(log.turnover_nav.sum()/years), "cost_initial_nav": float(log.cost.sum()),
            "downside_rms": float(np.sqrt(np.mean(np.minimum(r, 0)**2))*np.sqrt(252)),
            "worst_month": float(months.min()), "worst_month_date": str(months.idxmin()),
            "mean_open_weight": float(log.opening_weight_after_trade.mean())}


def boot_portfolio(candidate, baseline, years):
    a = candidate["return"].to_numpy(); b = baseline["return"].to_numpy()
    def stats(r):
        rolling = rolling_volatility(r)[20:]; vol = r.std(ddof=1)*np.sqrt(252)
        return np.array([np.sqrt(np.mean((rolling-.1)**2)), vol,
                         np.exp(np.log1p(r).sum()/years)-1, r.mean()/r.std(ddof=1)*np.sqrt(252)])
    rng = np.random.default_rng(1729)
    estimates = np.asarray([stats(a[i])-stats(b[i]) for i in (block_indices(len(a), rng) for _ in range(1000))])
    return {name: {"estimate": float(value), "ci95": np.quantile(estimates[:, j], [.025, .975]).tolist()}
            for j, (name, value) in enumerate(zip(["rolling_target_rmse", "volatility", "cagr", "sharpe"], stats(a)-stats(b)))}


def run_h8():
    spy, source = acquire_spy()
    h7 = json.loads((OUT/"h7.json").read_bytes()); checked_hash(OUT/"h7_forecasts.csv", h7["forecasts_sha256"])
    signals = pd.read_csv(OUT/"h7_forecasts.csv", float_precision="round_trip")
    strategies = {"buyhold": np.ones(len(signals)), **{name: np.clip(.1/np.sqrt(signals[name].to_numpy()), 0, 1) for name in ("trailing", "vix", "garch", "combined")}}
    metrics = {}; hashes = {}; logs = {}; periods = {}
    for cost in (0, 1, 5, 10, 25):
        metrics[str(cost)] = {}; logs[cost] = {}
        for name, weights in strategies.items():
            log = simulate_spy(spy, signals, weights, cost)
            logs[cost][name] = log; metrics[str(cost)][name] = portfolio_metrics(log)
            hashes[f"h8_{name}_{cost}bps.csv"] = csv_immutable(OUT/f"h8_{name}_{cost}bps.csv", log)
    contrasts = {}
    for cost in logs:
        candidate, baseline = logs[cost]["combined"], logs[cost]["trailing"]
        years = (pd.Timestamp(candidate.Date.iloc[-1])-pd.Timestamp(candidate.Date.iloc[0])).days/365.25
        a = (rolling_volatility(candidate["return"].to_numpy())[20:]-.1)**2
        b = (rolling_volatility(baseline["return"].to_numpy())[20:]-.1)**2
        contrasts[str(cost)] = {"paired_rolling_squared_error": paired(a-b), "bootstrap": boot_portfolio(candidate, baseline, years)}
    for period, (lo, hi) in PERIODS.items():
        periods[period] = {}
        for name, log in logs[5].items():
            sub = log.loc[log.Date.between(lo, hi)].copy()
            # Period-local NAV starts at1; retain return stream and costs relative baseline units.
            sub["nav"] = np.cumprod(1+sub["return"].to_numpy())
            periods[period][name] = portfolio_metrics(sub)
    return {"status": STATUS, "n_signals": len(signals), "n_executed_signals": len(signals)-1,
            "last_signal_no_earned_return": signals.origin.iloc[-1], "source": source,
            "models": metrics, "comparisons_combined_minus_trailing": contrasts, "periods_5bps": periods,
            "log_sha256": hashes, "failed_strategies": 0,
            "timing": "next-open rebalance; old holdings earn overnight/dividends; final next-open mark without last-signal trade",
            "cash_interest": 0., "cost_bps": [0, 1, 5, 10, 25],
            "implementation": implementation(["src/vrp/quant_portfolio.py", "src/vrp/quant_extension.py", "src/vrp/quant_calendar.py", "scripts/run_quant_portfolio.py"])}
