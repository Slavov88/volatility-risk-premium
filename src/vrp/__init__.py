"""Research utilities for the volatility risk premium project."""

from vrp.config import CONVENTIONS
from vrp.evaluation import (
    common_evaluation_mask,
    estimation_window,
    naive_variance_21t,
    naive_variance_30c,
    out_of_sample_split,
)
from vrp.inference import holm_adjust_two, newey_west_mean, nonoverlapping_origins_30c, overlap_l0
from vrp.garch_units import from_garch_variance, to_garch_fit_returns
from vrp.origin_panel import align_origin_panel
from vrp.premium import ivar_from_vix, ivol_from_vix, volgap, vrp_x
from vrp.range_estimators import garman_klass_daily, parkinson_daily
from vrp.regimes import label_nber_regimes
from vrp.returns import log_returns
from vrp.summary import summary_statistics
from vrp.targets import realized_variance_21t, realized_variance_30c, realized_volatility

__all__ = [
    "CONVENTIONS",
    "common_evaluation_mask",
    "estimation_window",
    "align_origin_panel",
    "from_garch_variance",
    "garman_klass_daily",
    "ivar_from_vix",
    "ivol_from_vix",
    "label_nber_regimes",
    "log_returns",
    "naive_variance_21t",
    "naive_variance_30c",
    "holm_adjust_two",
    "newey_west_mean",
    "nonoverlapping_origins_30c",
    "out_of_sample_split",
    "overlap_l0",
    "parkinson_daily",
    "realized_variance_21t",
    "realized_variance_30c",
    "realized_volatility",
    "summary_statistics",
    "to_garch_fit_returns",
    "volgap",
    "vrp_x",
]
