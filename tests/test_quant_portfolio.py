"""Independent share/cash accounting and delayed-execution controls."""
import numpy as np
import pandas as pd
import pytest
from vrp.quant_portfolio import rebalance, simulate_spy, validate_spy


@pytest.mark.parametrize("weight", [0., .1, .5, 1.])
@pytest.mark.parametrize("cost", [0., .0001, .0005, .0025])
@pytest.mark.parametrize("old_weight", [0., .3, 1.])
def test_rebalance_cash_cost_and_exposure(weight, cost, old_weight):
    q, cash, fee, notional = rebalance(old_weight/100, 1-old_weight, 100, weight, cost)
    assert cash >= 0 and q >= 0
    assert fee == pytest.approx(cost*notional)
    assert q*100+cash+fee == pytest.approx(1.)
    assert q*100/(q*100+cash) == pytest.approx(weight)
    # Independent scalar root of the traded-notional cost equation.
    from scipy.optimize import brentq
    oracle = brentq(lambda k: k-cost*abs(weight*(1-k)-old_weight), 0, .01, xtol=1e-15)
    assert fee == pytest.approx(oracle, abs=1e-14)


def toy():
    spy = pd.DataFrame({"Date": ["2020-01-06", "2020-01-07", "2020-01-08"],
                        "Open": [100., 110., 120.], "Close": [105., 115., 125.], "Dividends": [0., 1., 0.]})
    signals = pd.DataFrame({"origin": ["2020-01-03", "2020-01-06", "2020-01-07"]})
    return spy, signals


def test_signal_next_open_and_dividend_old_holder():
    spy, signals = toy()
    log = simulate_spy(spy, signals, [1, 0, 1], 0)
    assert log.Date.iloc[0] == "2020-01-06"
    assert log.nav.iloc[0] == pytest.approx(1.05)
    assert log.dividend_cash.iloc[1] == pytest.approx(.01)
    assert log.nav.iloc[1] == pytest.approx(1.11)
    assert log.nav.iloc[2] == pytest.approx(1.11)
    assert log.shares.iloc[1] == 0
    assert log.final_open_mark.iloc[-1]
    assert log.trade_notional.iloc[-1] == 0
    assert np.prod(1+log["return"]) == pytest.approx(log.nav.iloc[-1])


def test_future_signal_price_perturbation_invariance_and_missing_fail():
    spy, signals = toy(); old = simulate_spy(spy, signals, [.5, .8, 0], 5)
    future = spy.copy(); future.loc[2, ["Open", "Close"]] *= 10
    new = simulate_spy(future, signals, [.5, .8, 1], 5)
    pd.testing.assert_frame_equal(old.iloc[:2], new.iloc[:2])
    with pytest.raises(ValueError, match="Missing"):
        simulate_spy(spy.iloc[[0, 2]], signals, [.5, .8, 0], 5)
    with pytest.raises(ValueError):
        simulate_spy(spy, signals, [1.5, 0, 0], 5)


def test_no_trade_no_cost():
    q, cash, fee, trade = rebalance(.005, .5, 100., .5, .0025)
    assert fee == 0 and trade == 0


def test_nonzero_split_gate():
    from vrp.calendar import exchange_sessions
    from datetime import date
    days = exchange_sessions(date(2006,12,1), date(2026,2,2))
    f = pd.DataFrame({"Date": [d.isoformat() for d in days], **{c: 100. for c in ["Open", "High", "Low", "Close", "Adj Close"]}, "Dividends": 0., "Stock Splits": 0.})
    assert validate_spy(f)["splits"] == 0
    f.loc[100, "Stock Splits"] = 2
    with pytest.raises(ValueError, match="split"):
        validate_spy(f)
