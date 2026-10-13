"""Deterministic tests for the W3-03 numerical sensitivity artifacts."""

from __future__ import annotations

import math
from pathlib import Path

from black_scholes import black_scholes_price
from vrp.option_sensitivity import (
    BASELINE_MATURITY,
    BASELINE_RATE,
    BASELINE_VOLATILITY,
    STRESS_MATURITIES,
    STRESS_MONEYNESS,
    STRESS_RATES,
    STRESS_VOLATILITIES,
    generate_artifacts,
    render_numerical_stability_note,
    stress_grid_results,
)


def _price(
    spot: float,
    maturity: float,
    rate: float,
    volatility: float,
    option_type: str,
) -> float:
    return black_scholes_price(
        spot,
        100.0,
        maturity,
        rate,
        volatility,
        option_type,  # type: ignore[arg-type]
    )


def test_one_factor_sensitivity_has_expected_directions() -> None:
    call_low_money = _price(
        90.0, BASELINE_MATURITY, BASELINE_RATE, BASELINE_VOLATILITY, "call"
    )
    call_high_money = _price(
        110.0, BASELINE_MATURITY, BASELINE_RATE, BASELINE_VOLATILITY, "call"
    )
    put_low_money = _price(
        90.0, BASELINE_MATURITY, BASELINE_RATE, BASELINE_VOLATILITY, "put"
    )
    put_high_money = _price(
        110.0, BASELINE_MATURITY, BASELINE_RATE, BASELINE_VOLATILITY, "put"
    )
    assert call_high_money > call_low_money
    assert put_high_money < put_low_money

    call_low_rate = _price(
        100.0, BASELINE_MATURITY, -0.02, BASELINE_VOLATILITY, "call"
    )
    call_high_rate = _price(
        100.0, BASELINE_MATURITY, 0.08, BASELINE_VOLATILITY, "call"
    )
    put_low_rate = _price(
        100.0, BASELINE_MATURITY, -0.02, BASELINE_VOLATILITY, "put"
    )
    put_high_rate = _price(
        100.0, BASELINE_MATURITY, 0.08, BASELINE_VOLATILITY, "put"
    )
    assert call_high_rate > call_low_rate
    assert put_high_rate < put_low_rate

    for option_type in ("call", "put"):
        low_vol = _price(100.0, BASELINE_MATURITY, BASELINE_RATE, 0.10, option_type)
        high_vol = _price(100.0, BASELINE_MATURITY, BASELINE_RATE, 0.40, option_type)
        assert high_vol > low_vol


def test_stress_grid_is_complete_and_all_prices_respect_bounds() -> None:
    rows = stress_grid_results()
    expected = (
        len(STRESS_MATURITIES)
        * len(STRESS_MONEYNESS)
        * len(STRESS_RATES)
        * len(STRESS_VOLATILITIES)
        * 2
    )

    assert len(rows) == expected == 12_800
    assert all(math.isfinite(row.price) for row in rows)
    assert all(row.price_within_bounds for row in rows)
    assert {row.status for row in rows} == {
        "accurate",
        "inaccurate",
        "no_bracket",
    }


def test_stress_grid_records_success_and_both_bound_collapse_regions() -> None:
    rows = stress_grid_results()

    assert any(
        row.maturity == 1.0
        and row.moneyness == 1.0
        and row.rate == 0.05
        and row.volatility == 0.20
        and row.status == "accurate"
        for row in rows
    )
    no_bracket_regions = {
        row.failure_region for row in rows if row.status == "no_bracket"
    }
    assert no_bracket_regions == {
        "lower_bound_collapse",
        "upper_bound_collapse",
    }
    assert any(row.status == "inaccurate" for row in rows)


def test_note_documents_scope_grid_failures_and_safeguards() -> None:
    report = render_numerical_stability_note()

    assert "## Compact sensitivity plots" in report
    assert "## Full-factorial stability audit" in report
    assert "### Failure regions by maturity" in report
    assert "### Failure regions by moneyness" in report
    assert "### Failure regions by rate" in report
    assert "### Failure regions by volatility" in report
    assert "## Operational safeguards" in report
    assert "12,800 cases" in report
    assert "no_bracket" in report
    assert "VIX remains the model-free SPX option-strip index" in report


def test_artifact_generator_writes_two_svgs_and_current_report(
    tmp_path: Path,
) -> None:
    figure_dir = tmp_path / "figures"
    report_path = tmp_path / "note.md"
    generate_artifacts(figure_dir, report_path)

    first_outputs: dict[str, bytes] = {}
    for name in ("w3_03_price_sensitivity.svg", "w3_03_iv_stability.svg"):
        output_path = figure_dir / name
        content = output_path.read_text(encoding="utf-8")
        assert content.startswith("<?xml")
        assert "<svg" in content
        assert len(content) > 10_000
        first_outputs[name] = output_path.read_bytes()
    assert report_path.read_text(encoding="utf-8") == render_numerical_stability_note()

    second_figure_dir = tmp_path / "figures-second-run"
    second_report_path = tmp_path / "note-second-run.md"
    generate_artifacts(second_figure_dir, second_report_path)
    for name, first_content in first_outputs.items():
        assert (second_figure_dir / name).read_bytes() == first_content
    assert second_report_path.read_bytes() == report_path.read_bytes()


def test_committed_stability_note_is_current() -> None:
    report_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "w3_03_numerical_sensitivity.md"
    )
    assert report_path.read_text(encoding="utf-8") == render_numerical_stability_note()
