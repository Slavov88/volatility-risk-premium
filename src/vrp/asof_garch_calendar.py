"""Forecast-time schedule and deterministic replay of cached GARCH horizons."""
from datetime import timedelta
import numpy as np
import pandas as pd
from vrp.quant_calendar import regular_holiday_dates, scheduled_forward_sessions, reaggregate_garch

POLICY = "scheduled_regular_holidays_no_future_adhoc/1.0"


def scheduled_steps(origin, count):
    day = pd.Timestamp(origin).date()
    if not 1 <= count <= 22 or not pd.Timestamp("2007-01-01").date() <= day <= pd.Timestamp("2025-12-31").date():
        raise ValueError("Audited schedule scope is 2007-2025 and at most22 steps")
    holidays = regular_holiday_dates(); sessions = []
    while len(sessions) < count:
        day += timedelta(days=1)
        if day.weekday() < 5 and day not in holidays:
            sessions.append(day)
    return tuple(sessions)


def forecast_schedule(origin):
    sessions30 = scheduled_forward_sessions(origin)
    sessions = scheduled_steps(origin, max(len(sessions30), 21))
    if sessions[:len(sessions30)] != sessions30:
        raise ValueError("Scheduled30c/step mapping mismatch")
    return sessions30, sessions


def corrected_record(record, distribution):
    if record["status"] != "CONVERGED" or record["training_end"] > record["origin"]:
        raise ValueError("Unsafe cached fit or training time")
    params = record["parameters"]
    if distribution == "t" and (not np.isfinite(params.get("nu", np.nan)) or params["nu"] <= 2):
        raise ValueError("Student-t forecast requires finite standardized second moment")
    if distribution not in ("normal", "t"):
        raise ValueError("Unsupported exact fitted distribution")
    sessions30, sessions = forecast_schedule(record["origin"])
    values = list(record["daily_decimal_variances"])
    if len(values) < 21:
        raise ValueError("Missing original21-step vector")
    # Extension helper independently verifies every stored multi-step recurrence.
    corrected30 = reaggregate_garch(record)
    omega = params["omega"]/10000; persistence = params["alpha[1]"]+params["beta[1]"]
    extension_count = max(0, len(sessions)-len(values))
    old_last = values[-1]
    while len(values) < len(sessions):
        values.append(omega+persistence*values[-1])
    # Independent finite geometric-sum formula avoids a stationary assumption.
    for h in range(1, extension_count+1):
        oracle = persistence**h*old_last+omega*sum(persistence**j for j in range(h))
        if not np.isclose(values[len(record["daily_decimal_variances"])+h-1], oracle, rtol=1e-12, atol=1e-15):
            raise ValueError("Independent horizon-extension oracle mismatch")
    original30 = (365/30)*sum(record["daily_decimal_variances"][:record["session_count_30c"]])
    original21 = (252/21)*sum(record["daily_decimal_variances"][:21])
    if original30 != record["garch_30c"] or original21 != record["garch_21t"]:
        raise ValueError("Original forecast annualization mismatch")
    # Same arithmetic order as original: fixed21 identity must be exact.
    forecast21 = (252/21)*sum(values[:21])
    if forecast21 != record["garch_21t"]:
        raise ValueError("Fixed21 forecast unexpectedly changed")
    recurrence_error = float(np.max(np.abs(np.asarray(record["daily_decimal_variances"][1:])-omega-persistence*np.asarray(record["daily_decimal_variances"][:-1]))))
    result = dict(record)
    result.update({"forecast_sessions": [d.isoformat() for d in sessions], "session_count_30c": len(sessions30),
                   "daily_decimal_variances": values, "garch_30c": corrected30, "garch_21t": forecast21,
                   "calendar_policy": POLICY,
                   "original_calendar_metadata": {k:record[k] for k in ["forecast_sessions","session_count_30c","garch_30c","garch_21t"]},
                   "correction_audit": {"extended_steps": extension_count, "stored_recurrence_max_error_decimal_variance": recurrence_error,
                                        "fixed21_exact_identity": True, "parameter_refits": 0}})
    return result
