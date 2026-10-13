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
    values = record["daily_decimal_variances"]
    if len(values) < len(sessions):
        raise ValueError("Cached daily forecast vector does not cover scheduled horizon")
    if record["training_end"] > record["origin"]:
        raise ValueError("Future GARCH training")
    import numpy as np
    daily = np.asarray(values[:len(sessions)], float)
    if np.any(~np.isfinite(daily)) or np.any(daily <= 0):
        raise ValueError("Invalid daily GARCH variance units")
    return float(daily.sum()*365/30)
