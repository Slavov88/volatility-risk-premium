from datetime import date
import numpy as np
import pandas as pd
import pytest

from vrp.calendar import exchange_sessions
from vrp.forecast_analysis import compare, qlike


def test_qlike_is_normalized_and_rejects_invalid_units():
    assert qlike([.04,.05],[.04,.05]).tolist()==[0.,0.]
    assert qlike([.04],[.02])[0]==pytest.approx(2-np.log(2)-1)
    with pytest.raises(ValueError):qlike([.04],[0.])


def test_incomplete_coverage_cannot_produce_full_period_claim():
    with pytest.raises(ValueError,match="Incomplete"):
        compare(None,None,[],"normal_expanding")


def test_full_common_mask_includes_exact_same_origins_for_h3_h4():
    origins=exchange_sessions(date(2007,1,1),date(2025,12,31));assert len(origins)==4780
    x=np.arange(len(origins));vix=.03+.01*np.sin(x/17);garch=.025+.008*np.cos(x/19)
    actual=.005+.2*vix+.5*garch+.001*np.sin(x/3)
    targets=pd.DataFrame({"origin":[d.isoformat() for d in origins],"ivar":vix,
        "rvar_cc_fwd_30c":actual,"rvar_cc_fwd_21t":actual})
    dates=exchange_sessions(date(2006,1,3),date(2026,2,2))
    daily=pd.DataFrame({"Date":[d.isoformat() for d in dates],"log_return":np.random.default_rng(42).normal(0,.01,len(dates))})
    records=[{"origin":d.isoformat(),"status":"CONVERGED","garch_30c":float(g),"garch_21t":float(g),
        "persistence":.95,"warnings":[]} for d,g in zip(origins,garch)]
    records[5].update(status="FAILED",garch_30c=None,garch_21t=None)
    result=compare(targets,daily,records,"synthetic")
    assert result["fit_counts"]["failed"]==1
    for output in result["horizons"].values():
        assert output["n_common"]==4779
        assert records[5]["origin"] not in output["common_origins"]
        assert all(r["n"]==4779 for r in output["h4"])
        assert all(m["n"]==4779 for m in output["metrics"].values())
        assert all(t["squared_error"]["vix_vs_naive"]["holm_p_value"]>=t["squared_error"]["vix_vs_naive"]["p_value"] for t in output["h3_tests"])
