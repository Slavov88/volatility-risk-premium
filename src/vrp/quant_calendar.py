"""Ex-ante regular schedule; future ad-hoc closures never enter forecasts."""
from datetime import timedelta
import pandas as pd
from vrp.calendar import xnys_calendar


def scheduled_forward_sessions(origin):
    day = pd.Timestamp(origin).normalize()
    end = day+timedelta(days=30)
    candidates = pd.date_range(day+timedelta(days=1), end, freq="B")
    holidays = xnys_calendar().regular_holidays.holidays(day+timedelta(days=1), end)
    return tuple(x.date() for x in candidates.difference(holidays))


def reaggregate_garch(record):
    sessions = scheduled_forward_sessions(record["origin"])
    values = list(record["daily_decimal_variances"])
    if record["training_end"] > record["origin"]:
        raise ValueError("Future GARCH training")
    import numpy as np
    if len(values) < 2:
        raise ValueError("Cached horizon too short to verify recurrence")
    parameters = record.get("parameters", {})
    if not all(p in parameters for p in ["omega", "alpha[1]", "beta[1]"]):
        raise ValueError("Missing horizon recurrence parameters")
    omega = parameters["omega"]/10000
    persistence = parameters["alpha[1]"]+parameters["beta[1]"]
    if not np.isfinite([omega,persistence]).all() or omega <= 0 or persistence < 0:
        raise ValueError("Invalid horizon parameters")
    if not np.allclose(np.asarray(values[1:]), omega+persistence*np.asarray(values[:-1]), rtol=1e-9, atol=1e-13):
        raise ValueError("Cached horizon recurrence mismatch")
    while len(values) < len(sessions):
        values.append(omega+persistence*values[-1])
    daily = np.asarray(values[:len(sessions)], float)
    if np.any(~np.isfinite(daily)) or np.any(daily <= 0):
        raise ValueError("Invalid daily GARCH variance units")
    return float(daily.sum()*365/30)
