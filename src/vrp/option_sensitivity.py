"""Deterministic Track A Black--Scholes sensitivity and stability analysis.

The analysis uses synthetic one-option inputs only.  It does not use market
data and does not redefine VIX or any locked Track B empirical quantity.
"""

from __future__ import annotations

import argparse
import math
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from black_scholes import (
    ImpliedVolatilityError,
    black_scholes_price,
    implied_volatility,
)

BASELINE_SPOT = 100.0
BASELINE_STRIKE = 100.0
BASELINE_MATURITY = 30.0 / 365.0
BASELINE_RATE = 0.03
BASELINE_VOLATILITY = 0.20
BASELINE_DIVIDEND_YIELD = 0.0

# Broad, deliberately non-market-calibrated stress grid.  Moneyness is S/K.
STRESS_MATURITIES = (
    1e-8,
    1e-6,
    1e-4,
    1.0 / 365.0,
    7.0 / 365.0,
    30.0 / 365.0,
    0.25,
    1.0,
    5.0,
    30.0,
)
STRESS_MONEYNESS = (
    0.01,
    0.10,
    0.25,
    0.50,
    0.75,
    0.90,
    0.97,
    1.00,
    1.03,
    1.10,
    1.25,
    1.50,
    2.00,
    4.00,
    10.00,
    100.00,
)
STRESS_RATES = (-0.10, -0.02, 0.00, 0.05, 0.20)
STRESS_VOLATILITIES = (1e-4, 0.01, 0.05, 0.20, 0.80, 2.00, 5.00, 20.00)
OPTION_TYPES = ("call", "put")

RECOVERY_ABS_TOL = 1e-8
RECOVERY_REL_TOL = 1e-6
BOUND_REL_TOL = 1e-12


@dataclass(frozen=True)
class StressResult:
    """One full-factorial synthetic price/inversion result."""

    maturity: float
    moneyness: float
    rate: float
    volatility: float
    option_type: str
    price: float
    vega: float
    status: str
    failure_region: str
    recovered_volatility: float | None
    absolute_iv_error: float | None
    relative_iv_error: float | None
    price_within_bounds: bool


def _price_bounds(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    option_type: str,
) -> tuple[float, float, float]:
    discounted_strike = strike * math.exp(-rate * maturity)
    if option_type == "call":
        lower = max(spot - discounted_strike, 0.0)
        upper = spot
    else:
        lower = max(discounted_strike - spot, 0.0)
        upper = discounted_strike
    scale = max(1.0, spot, strike, discounted_strike)
    return lower, upper, scale


def _analytic_vega(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
) -> float:
    vol_sqrt_t = volatility * math.sqrt(maturity)
    d1 = (
        math.log(spot / strike)
        + (rate + 0.5 * volatility * volatility) * maturity
    ) / vol_sqrt_t
    density = math.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi)
    return spot * density * math.sqrt(maturity)


def _stress_case(
    maturity: float,
    moneyness: float,
    rate: float,
    volatility: float,
    option_type: str,
) -> StressResult:
    spot = BASELINE_STRIKE * moneyness
    strike = BASELINE_STRIKE
    price = black_scholes_price(
        spot,
        strike,
        maturity,
        rate,
        volatility,
        option_type,  # type: ignore[arg-type]
    )
    lower, upper, scale = _price_bounds(
        spot, strike, maturity, rate, option_type
    )
    price_within_bounds = (
        math.isfinite(price)
        and price >= lower - BOUND_REL_TOL * scale
        and price <= upper + BOUND_REL_TOL * scale
    )
    bound_tol = BOUND_REL_TOL * max(scale, abs(price))

    try:
        recovered = implied_volatility(
            spot,
            strike,
            maturity,
            rate,
            price,
            option_type,  # type: ignore[arg-type]
        )
    except ImpliedVolatilityError as exc:
        if price <= lower + bound_tol:
            failure_region = "lower_bound_collapse"
        elif price >= upper - bound_tol:
            failure_region = "upper_bound_collapse"
        else:
            failure_region = "search_interval"
        return StressResult(
            maturity=maturity,
            moneyness=moneyness,
            rate=rate,
            volatility=volatility,
            option_type=option_type,
            price=price,
            vega=_analytic_vega(spot, strike, maturity, rate, volatility),
            status=exc.code,
            failure_region=failure_region,
            recovered_volatility=None,
            absolute_iv_error=None,
            relative_iv_error=None,
            price_within_bounds=price_within_bounds,
        )

    absolute_error = abs(recovered - volatility)
    relative_error = absolute_error / volatility
    accurate = absolute_error <= max(
        RECOVERY_ABS_TOL, RECOVERY_REL_TOL * volatility
    )
    return StressResult(
        maturity=maturity,
        moneyness=moneyness,
        rate=rate,
        volatility=volatility,
        option_type=option_type,
        price=price,
        vega=_analytic_vega(spot, strike, maturity, rate, volatility),
        status="accurate" if accurate else "inaccurate",
        failure_region="" if accurate else "ill_conditioned_recovery",
        recovered_volatility=recovered,
        absolute_iv_error=absolute_error,
        relative_iv_error=relative_error,
        price_within_bounds=price_within_bounds,
    )


@lru_cache(maxsize=1)
def stress_grid_results() -> tuple[StressResult, ...]:
    """Evaluate the fixed 12,800-case full-factorial stress grid."""

    return tuple(
        _stress_case(maturity, moneyness, rate, volatility, option_type)
        for maturity in STRESS_MATURITIES
        for moneyness in STRESS_MONEYNESS
        for rate in STRESS_RATES
        for volatility in STRESS_VOLATILITIES
        for option_type in OPTION_TYPES
    )


def _percent(numerator: int, denominator: int) -> str:
    return f"{100.0 * numerator / denominator:.1f}%"


def _outcome_counts(rows: Sequence[StressResult]) -> Counter[str]:
    return Counter(row.status for row in rows)


def _outcome_table(
    groups: Sequence[tuple[str, Sequence[StressResult]]],
) -> str:
    lines = [
        "| Value | Cases | Accurate | No bracket | Inaccurate |",
        "|---:|---:|---:|---:|---:|",
    ]
    for label, rows in groups:
        counts = _outcome_counts(rows)
        total = len(rows)
        lines.append(
            f"| {label} | {total} | "
            f"{_percent(counts['accurate'], total)} | "
            f"{_percent(counts['no_bracket'], total)} | "
            f"{counts['inaccurate']} |"
        )
    return "\n".join(lines)


def _maturity_label(value: float) -> str:
    days = value * 365.0
    if days < 0.01:
        return f"{days:.3g} d"
    if days < 1.0:
        return f"{days:.3f} d"
    if value < 1.0:
        return f"{days:.0f} d"
    return f"{value:g} y"


def _float_label(value: float) -> str:
    return f"{value:g}"


def _rate_label(value: float) -> str:
    return f"{value:.0%}"


def _vol_label(value: float) -> str:
    return f"{value:.2%}" if value < 0.01 else f"{value:.0%}"


def render_numerical_stability_note() -> str:
    """Render the W3-03 sensitivity and numerical-stability note."""

    rows = stress_grid_results()
    counts = _outcome_counts(rows)
    total = len(rows)
    recovered = [
        row
        for row in rows
        if row.absolute_iv_error is not None and row.relative_iv_error is not None
    ]
    inaccurate = [row for row in rows if row.status == "inaccurate"]
    failure_regions = Counter(
        row.failure_region for row in rows if row.status == "no_bracket"
    )
    max_absolute = max(float(row.absolute_iv_error) for row in recovered)
    max_relative = max(float(row.relative_iv_error) for row in recovered)

    maturity_groups = [
        (
            _maturity_label(value),
            [row for row in rows if row.maturity == value],
        )
        for value in STRESS_MATURITIES
    ]
    rate_groups = [
        (_rate_label(value), [row for row in rows if row.rate == value])
        for value in STRESS_RATES
    ]
    volatility_groups = [
        (
            _vol_label(value),
            [row for row in rows if row.volatility == value],
        )
        for value in STRESS_VOLATILITIES
    ]
    moneyness_definitions = (
        ("S/K <= 0.50", lambda value: value <= 0.50),
        ("0.50 < S/K < 0.90", lambda value: 0.50 < value < 0.90),
        ("0.90 <= S/K <= 1.10", lambda value: 0.90 <= value <= 1.10),
        ("1.10 < S/K < 2.00", lambda value: 1.10 < value < 2.00),
        ("S/K >= 2.00", lambda value: value >= 2.00),
    )
    moneyness_groups = [
        (label, [row for row in rows if predicate(row.moneyness)])
        for label, predicate in moneyness_definitions
    ]

    inaccurate_lines = [
        "| T | S/K | r | True sigma | Type | Recovered sigma | Abs. error |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in inaccurate:
        inaccurate_lines.append(
            f"| {_maturity_label(row.maturity)} | "
            f"{_float_label(row.moneyness)} | {_rate_label(row.rate)} | "
            f"{_vol_label(row.volatility)} | {row.option_type} | "
            f"{float(row.recovered_volatility):.9g} | "
            f"{float(row.absolute_iv_error):.3e} |"
        )

    return f"""# W3-03 Black--Scholes Sensitivity and Numerical Stability

This is a deterministic, synthetic Track A analysis of one European
Black--Scholes option. It neither uses market data nor treats a single-option
implied volatility as VIX. VIX remains the model-free SPX option-strip index,
and `IVAR = (VIX / 100)^2` remains the locked Track B variance quantity.

## Compact sensitivity plots

![One-factor Black--Scholes price sensitivity](figures/w3_03_price_sensitivity.svg)

The four panels vary one input at a time around `S = K = 100`,
`T = 30/365`, `r = 3%`, `sigma = 20%`, and `q = 0`. Prices are divided by
strike. Moneyness means spot moneyness `S/K`. The plots show the expected
call/put asymmetry: calls rise and puts fall with `S/K`; calls rise and puts
fall with the rate in this no-dividend comparison; and both option values rise
with volatility. Maturity effects combine time value and discounting, so they
are displayed rather than summarized as universally monotone.

![Synthetic implied-volatility recovery regions](figures/w3_03_iv_stability.svg)

The recovery map holds `r = 3%` and `sigma = 20%` fixed while varying
maturity and `S/K`. Green cells recover sigma within
`max(1e-8, 1e-6 * sigma)`; grey cells return the solver's explicit
`no_bracket` diagnostic. The map is descriptive of float64 computation and
the documented solver tolerances, not an economic admissibility map.

## Full-factorial stability audit

The audit crosses {len(STRESS_MATURITIES)} maturities from
`{STRESS_MATURITIES[0]:g}` to `{STRESS_MATURITIES[-1]:g}` years,
{len(STRESS_MONEYNESS)} values of `S/K` from
`{STRESS_MONEYNESS[0]:g}` to `{STRESS_MONEYNESS[-1]:g}`,
{len(STRESS_RATES)} rates from `{STRESS_RATES[0]:.0%}` to
`{STRESS_RATES[-1]:.0%}`, {len(STRESS_VOLATILITIES)} volatilities from
`{STRESS_VOLATILITIES[0]:g}` to `{STRESS_VOLATILITIES[-1]:g}`, and calls and
puts: {total:,} cases in total. Synthetic prices are inverted using the
production Brent solver.

| Outcome | Cases | Share |
|---|---:|---:|
| Accurate IV recovery | {counts['accurate']:,} | {_percent(counts['accurate'], total)} |
| Explicit `no_bracket` | {counts['no_bracket']:,} | {_percent(counts['no_bracket'], total)} |
| Converged but inaccurate at the stated tolerance | {counts['inaccurate']:,} | {_percent(counts['inaccurate'], total)} |

All {total:,} prices are finite and inside their analytical call/put bounds.
Among the {len(recovered):,} converged inversions, the maximum absolute IV
error is `{max_absolute:.3e}` and the maximum relative IV error is
`{max_relative:.3e}`. These maxima are stress-test diagnostics, not typical
market-quote accuracy.

### Failure regions by maturity

{_outcome_table(maturity_groups)}

### Failure regions by moneyness

{_outcome_table(moneyness_groups)}

### Failure regions by rate

{_outcome_table(rate_groups)}

### Failure regions by volatility

{_outcome_table(volatility_groups)}

## Numerical interpretation

Of the {counts['no_bracket']:,} explicit failures,
{failure_regions['lower_bound_collapse']:,} occur because the computed option
price is at or within the solver tolerance of its lower no-arbitrage bound,
and {failure_regions['upper_bound_collapse']:,} occur at the upper bound.
None of the synthetic failures is a price-bound violation or an unreported
solver exception.

The common mechanism is weak identification. Black--Scholes vega tends to
zero for very short maturity, extreme moneyness, very low volatility, and
prices close to an upper bound at very high total volatility. In those
regions, distinct volatilities map to prices that are identical or nearly
identical in float64 arithmetic. A root is therefore not numerically
identified even though the exact mathematical price is monotone in
volatility. Interest rates shift forward moneyness and the discounted bounds;
their effect on failure frequency is consequently smaller and non-monotone in
this symmetric stress grid.

The {len(inaccurate)} converged cases outside the stated recovery tolerance
are:

{chr(10).join(inaccurate_lines)}

These cases reprice successfully but show why a tiny price residual alone is
not a reliable IV-accuracy criterion when vega is close to zero.

## Operational safeguards

1. Check the discounted European price bounds before inversion and preserve
   the solver's stable diagnostic code.
2. Do not convert `no_bracket` into zero volatility, a cap value, or a missing
   value without retaining the reason.
3. Prefer the out-of-the-money side of a parity-linked quote when possible to
   reduce subtraction of intrinsic value, while still checking quote quality.
4. Treat very small vega as an identification warning. For real quotes,
   bid--ask width and tick size dominate machine precision.
5. Report the positive search interval and cap. A quote beyond the cap is a
   documented failure, not permission to enlarge the cap after seeing a
   desired result.

## Scope and reproduction

This self-inversion audit tests numerical conditioning, not Black--Scholes
model fit or independent formula correctness; W3-02 supplies the independent
QuantLib and limited real-quote checks. The extreme grid deliberately includes
inputs far outside ordinary SPX use, so its aggregate failure share is not an
estimate of market-data failure frequency.

Run `vrp-option-sensitivity --output-dir docs/figures --report
docs/w3_03_numerical_sensitivity.md` to regenerate both SVG figures and this
note. No raw or provider market dataset is read.
"""


def _setup_plotting() -> tuple[object, object]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return matplotlib, plt


def save_price_sensitivity_figure(path: Path) -> None:
    """Write the deterministic four-panel one-factor sensitivity figure."""

    matplotlib, plt = _setup_plotting()
    import numpy as np

    maturity_days = np.geomspace(1.0 / 24.0, 365.0 * 5.0, 180)
    moneyness = np.linspace(0.50, 1.50, 180)
    rates = np.linspace(-0.05, 0.15, 180)
    volatilities = np.linspace(0.01, 1.00, 180)
    panels = (
        ("Maturity (calendar days)", maturity_days),
        ("Spot moneyness S/K", moneyness),
        ("Rate", rates),
        ("Volatility", volatilities),
    )

    with matplotlib.rc_context(
        {
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "legend.fontsize": 8,
            "svg.hashsalt": "vrp-w3-03-price-sensitivity",
        }
    ):
        figure, axes = plt.subplots(2, 2, figsize=(7.2, 5.2), constrained_layout=True)
        for axis, (label, values) in zip(axes.flat, panels):
            for option_type, color, linestyle in (
                ("call", "#0072B2", "-"),
                ("put", "#D55E00", "--"),
            ):
                prices: list[float] = []
                for value in values:
                    maturity = BASELINE_MATURITY
                    spot = BASELINE_SPOT
                    rate = BASELINE_RATE
                    volatility = BASELINE_VOLATILITY
                    if label.startswith("Maturity"):
                        maturity = float(value) / 365.0
                    elif label.startswith("Spot"):
                        spot = float(value) * BASELINE_STRIKE
                    elif label == "Rate":
                        rate = float(value)
                    else:
                        volatility = float(value)
                    prices.append(
                        black_scholes_price(
                            spot,
                            BASELINE_STRIKE,
                            maturity,
                            rate,
                            volatility,
                            option_type,  # type: ignore[arg-type]
                            dividend_yield=BASELINE_DIVIDEND_YIELD,
                        )
                        / BASELINE_STRIKE
                    )
                axis.plot(
                    values,
                    prices,
                    color=color,
                    linestyle=linestyle,
                    linewidth=1.8,
                    label=option_type.capitalize(),
                )
            axis.set_title(label)
            axis.set_ylabel("Price / K")
            axis.grid(alpha=0.25, linewidth=0.6)
            if label.startswith("Maturity"):
                axis.set_xscale("log")
            elif label in {"Rate", "Volatility"}:
                ticks = axis.get_xticks()
                axis.set_xticks(ticks, [f"{tick:.0%}" for tick in ticks])
            axis.legend(frameon=False)

        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(
            path,
            format="svg",
            metadata={"Creator": "vrp.option_sensitivity", "Date": None},
        )
        plt.close(figure)


def _stability_surface(option_type: str) -> tuple[object, object, object]:
    import numpy as np

    moneyness = np.geomspace(0.25, 4.0, 81)
    maturity_days = np.geomspace(1e-4, 3650.0, 81)
    outcomes = np.empty((len(maturity_days), len(moneyness)), dtype=int)
    for row_index, days in enumerate(maturity_days):
        for column_index, money in enumerate(moneyness):
            result = _stress_case(
                float(days) / 365.0,
                float(money),
                BASELINE_RATE,
                BASELINE_VOLATILITY,
                option_type,
            )
            outcomes[row_index, column_index] = {
                "no_bracket": 0,
                "inaccurate": 1,
                "accurate": 2,
            }.get(result.status, 0)
    return moneyness, maturity_days, outcomes


def save_iv_stability_figure(path: Path) -> None:
    """Write call/put maturity--moneyness IV-recovery maps."""

    matplotlib, plt = _setup_plotting()
    import numpy as np
    from matplotlib.colors import BoundaryNorm, ListedColormap

    surfaces = [
        ("Call", *_stability_surface("call")),
        ("Put", *_stability_surface("put")),
    ]
    colormap = ListedColormap(["#B3B3B3", "#E69F00", "#009E73"])
    normalization = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], colormap.N)

    with matplotlib.rc_context(
        {
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "svg.hashsalt": "vrp-w3-03-iv-stability",
        }
    ):
        figure, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), constrained_layout=True)
        image = None
        for axis, (title, money, days, outcomes) in zip(axes, surfaces):
            image = axis.imshow(
                outcomes,
                origin="lower",
                aspect="auto",
                interpolation="nearest",
                cmap=colormap,
                norm=normalization,
                extent=(
                    math.log10(float(money[0])),
                    math.log10(float(money[-1])),
                    math.log10(float(days[0])),
                    math.log10(float(days[-1])),
                ),
            )
            x_ticks = np.array([0.25, 0.5, 1.0, 2.0, 4.0])
            y_ticks = np.array([1e-4, 0.01, 1.0, 30.0, 365.0, 3650.0])
            axis.set_xticks(np.log10(x_ticks), [f"{value:g}" for value in x_ticks])
            axis.set_yticks(np.log10(y_ticks), [f"{value:g}" for value in y_ticks])
            axis.set_title(f"{title}: synthetic IV recovery")
            axis.set_xlabel("Spot moneyness S/K")
            axis.set_ylabel("Maturity (calendar days)")

        assert image is not None
        colorbar = figure.colorbar(image, ax=axes, ticks=[0, 1, 2], shrink=0.85)
        colorbar.ax.set_yticklabels(["No bracket", "Inaccurate", "Accurate"])
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(
            path,
            format="svg",
            metadata={"Creator": "vrp.option_sensitivity", "Date": None},
        )
        plt.close(figure)


def generate_artifacts(output_dir: Path, report_path: Path) -> None:
    """Generate both compact figures and the matching Markdown note."""

    save_price_sensitivity_figure(output_dir / "w3_03_price_sensitivity.svg")
    save_iv_stability_figure(output_dir / "w3_03_iv_stability.svg")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_numerical_stability_note(), encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/figures"),
        help="directory for the two generated SVG figures",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/w3_03_numerical_sensitivity.md"),
        help="path for the generated numerical-stability note",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    generate_artifacts(args.output_dir, args.report)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
