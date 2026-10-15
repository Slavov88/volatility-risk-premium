"""Independent daily P&L component reconstruction for a self-financing ledger."""
from __future__ import annotations

import numpy as np
import pandas as pd


def decompose_ledger(ledger: pd.DataFrame, prices: pd.DataFrame, *, atol: float = 2e-11) -> pd.DataFrame:
    """Reconstruct equity/dividend/cash/fee dollars and verify each daily return."""
    required_ledger = {"Date", "final_open_mark", "old_shares", "shares", "dividend_cash",
                      "cash_interest", "cost", "trade_notional", "turnover_nav", "nav", "return"}
    required_prices = {"Date", "Open", "Close"}
    if not required_ledger.issubset(ledger.columns) or not required_prices.issubset(prices.columns):
        raise ValueError("Ledger or price frame is missing required accounting columns")
    if ledger.Date.duplicated().any() or prices.Date.duplicated().any():
        raise ValueError("Dates must be unique in ledger and prices")
    if not ledger.Date.is_monotonic_increasing or not prices.Date.is_monotonic_increasing:
        raise ValueError("Ledger and prices must be chronological")
    joined = ledger.merge(prices[["Date", "Open", "Close"]], on="Date", how="left", validate="one_to_one")
    if joined[["Open", "Close"]].isna().any().any():
        raise ValueError("A ledger date has no matched open/close price")
    overnight = np.zeros(len(joined), float)
    if len(joined) > 1:
        overnight[1:] = joined.old_shares.to_numpy(float)[1:] * (
            joined.Open.to_numpy(float)[1:] - joined.Close.to_numpy(float)[:-1])
    intraday = joined.shares.to_numpy(float) * (joined.Close.to_numpy(float)-joined.Open.to_numpy(float))
    intraday[joined.final_open_mark.to_numpy(bool)] = 0.0
    dividend = joined.dividend_cash.to_numpy(float)
    interest = joined.cash_interest.to_numpy(float)
    fee = -joined.cost.to_numpy(float)
    previous_nav = np.r_[1.0, joined.nav.to_numpy(float)[:-1]]
    component_return = (overnight+dividend+intraday+interest+fee)/previous_nav
    residual = joined["return"].to_numpy(float)-component_return
    if not np.isfinite(residual).all() or np.max(np.abs(residual), initial=0.0) > atol:
        raise ValueError(f"Daily P&L component identity failed: {np.max(np.abs(residual))}")
    return pd.DataFrame({"Date": joined.Date, "overnight_equity_pnl": overnight,
        "dividend_cash_pnl": dividend, "intraday_equity_pnl": intraday,
        "cash_interest_pnl": interest, "trade_notional": joined.trade_notional.to_numpy(float),
        "transaction_fee_pnl": fee, "beginning_nav": previous_nav,
        "reconstructed_return": component_return, "observed_return": joined["return"].to_numpy(float),
        "return_residual": residual})
