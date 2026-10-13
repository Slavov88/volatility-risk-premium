"""W3-02 deterministic reference-library and real-quote validation."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

pytest.importorskip("QuantLib")

from vrp.option_validation import (  # noqa: E402
    MARKET_QUOTES,
    market_quote_inputs,
    market_quote_validation_rows,
    reference_validation_rows,
    render_validation_report,
)


def test_reference_prices_and_iv_match_quantlib() -> None:
    rows = reference_validation_rows()

    assert len(rows) == 6
    assert {row["option_type"] for row in rows} == {"call", "put"}
    assert max(float(row["price_abs_error"]) for row in rows) < 1e-12
    assert max(float(row["price_rel_error"]) for row in rows) < 1e-10
    assert max(float(row["iv_abs_error"]) for row in rows) < 1e-10
    assert max(float(row["iv_rel_error"]) for row in rows) < 1e-9


def test_market_inputs_reproduce_documented_conventions() -> None:
    inputs = market_quote_inputs()

    assert inputs["maturity_days"] == 35.0
    assert math.isclose(inputs["time_to_maturity"], 35.0 / 365.0)
    assert math.isclose(inputs["rate"], 0.027946575342465755)
    assert math.isclose(inputs["forward"], 3916.0930686099828)
    assert math.isclose(inputs["dividend_yield"], -0.011388364485305561)


def test_real_quote_iv_and_repricing_errors_are_small() -> None:
    rows = market_quote_validation_rows()

    assert len(rows) == len(MARKET_QUOTES) == 6
    assert all(bool(row["inside_bid_ask"]) for row in rows)
    assert max(float(row["iv_abs_error"]) for row in rows) < 1e-6
    assert max(float(row["iv_rel_error"]) for row in rows) < 5e-6
    assert max(float(row["price_abs_error"]) for row in rows) < 5e-4
    assert max(float(row["price_rel_error"]) for row in rows) < 5e-6


def test_real_quote_errors_are_absolute_and_relative() -> None:
    for row in market_quote_validation_rows():
        expected_iv_abs = abs(float(row["our_iv"]) - float(row["published_mid_iv"]))
        expected_iv_rel = expected_iv_abs / abs(float(row["published_mid_iv"]))
        expected_price_abs = abs(float(row["repriced"]) - float(row["midpoint"]))
        expected_price_rel = expected_price_abs / abs(float(row["midpoint"]))

        assert math.isclose(float(row["iv_abs_error"]), expected_iv_abs)
        assert math.isclose(float(row["iv_rel_error"]), expected_iv_rel)
        assert math.isclose(float(row["price_abs_error"]), expected_price_abs)
        assert math.isclose(float(row["price_rel_error"]), expected_price_rel)


def test_report_contains_tables_provenance_and_discrepancy_explanation() -> None:
    report = render_validation_report()

    assert "## Independent library validation" in report
    assert "## Fixed real-quote validation" in report
    assert "Price abs. error" in report
    assert "IV rel. error" in report
    assert "Explanation of discrepancies and scope" in report
    assert "SPX221021C03900000" in report
    assert "VIX" in report


def test_committed_report_is_current() -> None:
    report_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "w3_02_pricer_iv_validation.md"
    )
    assert report_path.read_text(encoding="utf-8") == render_validation_report()
