"""Research utilities for the volatility risk premium project."""

from vrp.config import CONVENTIONS
from vrp.inference import newey_west_mean, overlap_l0
from vrp.premium import ivar_from_vix, ivol_from_vix, volgap, vrp_x
from vrp.range_estimators import garman_klass_daily, parkinson_daily
from vrp.regimes import label_nber_regimes
from vrp.returns import log_returns
from vrp.summary import summary_statistics
from vrp.targets import realized_variance_21t, realized_variance_30c, realized_volatility

__all__ = [
    "CONVENTIONS",
    "garman_klass_daily",
    "ivar_from_vix",
    "ivol_from_vix",
    "label_nber_regimes",
    "log_returns",
    "newey_west_mean",
    "overlap_l0",
    "parkinson_daily",
    "realized_variance_21t",
    "realized_variance_30c",
    "realized_volatility",
    "summary_statistics",
    "volgap",
    "vrp_x",
]
