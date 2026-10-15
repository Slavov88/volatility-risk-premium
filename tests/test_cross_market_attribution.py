import pandas as pd
import pytest

from vrp.cross_market_attribution import decompose_ledger


def test_daily_self_financing_components_separate_equity_dividends_cash_and_fees():
    ledger=pd.DataFrame([
        {"Date":"2020-01-02","final_open_mark":False,"old_shares":0.,"shares":.01,
         "dividend_cash":0.,"cash_interest":0.,"cost":.001,"trade_notional":1.,"turnover_nav":1.,
         "nav":1.099,"return":.099},
        {"Date":"2020-01-03","final_open_mark":False,"old_shares":.01,"shares":.005,
         "dividend_cash":.01,"cash_interest":.005,"cost":.0025,"trade_notional":.5,"turnover_nav":.01,
         "nav":1.1415,"return":.0425/1.099},
        {"Date":"2020-01-06","final_open_mark":True,"old_shares":.005,"shares":.005,
         "dividend_cash":.0025,"cash_interest":.002,"cost":0.,"trade_notional":0.,"turnover_nav":0.,
         "nav":1.156,"return":.0145/1.1415},
    ])
    prices=pd.DataFrame([{"Date":"2020-01-02","Open":100.,"Close":110.},
                         {"Date":"2020-01-03","Open":112.,"Close":114.},
                         {"Date":"2020-01-06","Open":116.,"Close":118.}])
    components=decompose_ledger(ledger,prices)
    assert components.overnight_equity_pnl.tolist()==[0.,.02,.01]
    assert components.dividend_cash_pnl.tolist()==[0.,.01,.0025]
    assert components.intraday_equity_pnl.tolist()==[.1,.01,0.]
    assert components.cash_interest_pnl.tolist()==[0.,.005,.002]
    assert components.transaction_fee_pnl.tolist()==[-.001,-.0025,0.]
    assert components.return_residual.abs().max()<1e-14


def test_daily_component_audit_rejects_return_mismatch():
    ledger=pd.DataFrame([{"Date":"2020-01-02","final_open_mark":False,"old_shares":0.,"shares":1.,
        "dividend_cash":0.,"cash_interest":0.,"cost":0.,"trade_notional":1.,"turnover_nav":1.,
        "nav":2.,"return":2.}])
    prices=pd.DataFrame([{"Date":"2020-01-02","Open":100.,"Close":101.}])
    with pytest.raises(ValueError,match="component identity"):
        decompose_ledger(ledger,prices)
