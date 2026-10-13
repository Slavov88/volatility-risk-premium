from datetime import date
import numpy as np
import pytest

from vrp.calendar import exchange_sessions, forward_30c_sessions
from vrp.inference import overlap_l0
from vrp.provisional_analysis import checked_mean, checked_regression


@pytest.mark.parametrize("horizon", [1,2,3,7,30,45])
def test_overlap_optimized_matches_exact_set_oracle(horizon):
    origins=exchange_sessions(date(2001,8,20),date(2001,10,15))[::2]
    sets=[set(forward_30c_sessions(o,horizon)) for o in origins]
    expected=max([j-i for i in range(len(origins)) for j in range(i+1,len(origins)) if sets[i]&sets[j]] or [0])
    assert overlap_l0(origins,horizon_calendar_days=horizon)==expected


def test_independent_hac_and_joint_wald():
    rng=np.random.default_rng(42);x=rng.normal(size=400);e=rng.normal(scale=.2,size=400)
    y=.15+.8*x+e
    result=checked_regression(y,x,21,np.eye(2),[0,1])
    assert result["wald"]["df"]==2 and result["wald"]["p_value"]<.01
    assert result["independent_covariance_max_error"]<1e-12
    assert checked_mean(e,20)["n_obs"]==400


def test_invalid_inference_inputs_are_not_silently_dropped():
    with pytest.raises(ValueError):checked_mean([1,np.nan,2],0)
    with pytest.raises(ValueError):checked_regression([1,2,3,4],[1,1,1,1],1)
