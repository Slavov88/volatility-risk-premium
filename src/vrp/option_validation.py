"""Deterministic Track A validation against QuantLib and real SPX quotes.

This module keeps single-option Black--Scholes validation separate from the
Track B VIX objects.  It contains only six limited example rows from a public
historical-options sample; the full market dataset remains outside the
repository.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal, Sequence

from black_scholes import black_scholes_price, implied_volatility

OptionType = Literal["call", "put"]

QUOTE_SOURCE_URL = "https://historicaldata.net/file/options_sample_2022H2.zip"
QUOTE_SOURCE_PAGE = "https://historicaldata.net/options.html"
QUOTE_DATE = date(2022, 9, 15)
EXPIRATION_DATE = date(2022, 10, 21)
SPX_CLOSE = 3901.35
RATE_CURVE_PERCENT = (2.76, 3.22, 4.00, 3.87, 3.66, 3.45, 3.48)
RATE_TENORS_YEARS = (1.0 / 12.0, 0.25, 1.0, 2.0, 5.0, 10.0, 30.0)


@dataclass(frozen=True)
class ReferenceCase:
    """A deterministic Black--Scholes--Merton reference-library case."""

    case_id: str
    option_type: OptionType
    spot: float
    strike: float
    time_to_maturity: float
    rate: float
    volatility: float
    dividend_yield: float


@dataclass(frozen=True)
class MarketQuote:
    """One limited example row from the fixed 2022 SPX quote sample."""

    contract: str
    option_type: OptionType
    strike: float
    bid: float
    ask: float
    published_mid_iv: float


REFERENCE_CASES = (
    ReferenceCase("atm_1y", "call", 100.0, 100.0, 1.0, 0.05, 0.20, 0.00),
    ReferenceCase("atm_1y", "put", 100.0, 100.0, 1.0, 0.05, 0.20, 0.00),
    ReferenceCase("dividend_otm", "call", 80.0, 100.0, 0.25, 0.01, 0.35, 0.02),
    ReferenceCase("negative_rate", "put", 110.0, 100.0, 2.0, -0.01, 0.15, 0.03),
    ReferenceCase("short_dated", "call", 100.0, 105.0, 7.0 / 365.0, 0.04, 0.50, 0.01),
    ReferenceCase("long_dated", "put", 200.0, 150.0, 3.0, 0.06, 0.10, 0.04),
)

# Limited example rows are permitted by the sample license.  All are
# European, cash-settled, AM-settled SPX contracts quoted on 2022-09-15.
MARKET_QUOTES = (
    MarketQuote("SPX221021C03850000", "call", 3850.0, 154.9, 156.0, 0.250087),
    MarketQuote("SPX221021P03850000", "put", 3850.0, 89.2, 89.9, 0.250122),
    MarketQuote("SPX221021C03900000", "call", 3900.0, 124.4, 125.4, 0.242425),
    MarketQuote("SPX221021P03900000", "put", 3900.0, 108.5, 109.2, 0.242425),
    MarketQuote("SPX221021C03950000", "call", 3950.0, 96.9, 97.8, 0.234189),
    MarketQuote("SPX221021P03950000", "put", 3950.0, 130.7, 131.6, 0.234156),
)


def _quantlib() -> Any:
    try:
        import QuantLib as ql
    except ImportError as exc:  # pragma: no cover - depends on local extras
        raise RuntimeError(
            "QuantLib is required for Track A reference validation; "
            "install the validation or dev extra"
        ) from exc
    return ql


def _absolute_relative_error(actual: float, reference: float) -> tuple[float, float]:
    absolute = abs(actual - reference)
    relative = absolute / abs(reference) if reference != 0.0 else math.nan
    return absolute, relative


def _quantlib_price(case: ReferenceCase) -> float:
    """Price with QuantLib's BlackCalculator in forward form."""

    ql = _quantlib()
    ql_type = ql.Option.Call if case.option_type == "call" else ql.Option.Put
    forward = case.spot * math.exp(
        (case.rate - case.dividend_yield) * case.time_to_maturity
    )
    discount = math.exp(-case.rate * case.time_to_maturity)
    std_dev = case.volatility * math.sqrt(case.time_to_maturity)
    payoff = ql.PlainVanillaPayoff(ql_type, case.strike)
    return float(ql.BlackCalculator(payoff, forward, std_dev, discount).value())


def _quantlib_implied_volatility(case: ReferenceCase, price: float) -> float:
    """Invert a price with QuantLib's independent implied-std-dev solver."""

    ql = _quantlib()
    ql_type = ql.Option.Call if case.option_type == "call" else ql.Option.Put
    forward = case.spot * math.exp(
        (case.rate - case.dividend_yield) * case.time_to_maturity
    )
    discount = math.exp(-case.rate * case.time_to_maturity)
    std_dev = ql.blackFormulaImpliedStdDev(
        ql_type,
        case.strike,
        forward,
        price,
        discount,
        0.0,
        case.volatility * math.sqrt(case.time_to_maturity),
        1e-12,
        100,
    )
    return float(std_dev / math.sqrt(case.time_to_maturity))


def reference_validation_rows() -> list[dict[str, float | str]]:
    """Return pricer and IV errors against QuantLib for fixed cases."""

    rows: list[dict[str, float | str]] = []
    for case in REFERENCE_CASES:
        reference_price = _quantlib_price(case)
        our_price = black_scholes_price(
            case.spot,
            case.strike,
            case.time_to_maturity,
            case.rate,
            case.volatility,
            case.option_type,
            dividend_yield=case.dividend_yield,
        )
        price_abs_error, price_rel_error = _absolute_relative_error(
            our_price, reference_price
        )

        our_iv = implied_volatility(
            case.spot,
            case.strike,
            case.time_to_maturity,
            case.rate,
            reference_price,
            case.option_type,
            dividend_yield=case.dividend_yield,
        )
        reference_iv = _quantlib_implied_volatility(case, reference_price)
        iv_abs_error, iv_rel_error = _absolute_relative_error(our_iv, reference_iv)
        rows.append(
            {
                "case_id": case.case_id,
                "option_type": case.option_type,
                "our_price": our_price,
                "reference_price": reference_price,
                "price_abs_error": price_abs_error,
                "price_rel_error": price_rel_error,
                "our_iv": our_iv,
                "reference_iv": reference_iv,
                "iv_abs_error": iv_abs_error,
                "iv_rel_error": iv_rel_error,
            }
        )
    return rows


def _linear_rate(time_to_maturity: float) -> float:
    """Interpolate the published Treasury par curve, returning a decimal rate."""

    if time_to_maturity <= RATE_TENORS_YEARS[0]:
        return RATE_CURVE_PERCENT[0] / 100.0
    for left in range(len(RATE_TENORS_YEARS) - 1):
        right = left + 1
        if time_to_maturity <= RATE_TENORS_YEARS[right]:
            weight = (
                (time_to_maturity - RATE_TENORS_YEARS[left])
                / (RATE_TENORS_YEARS[right] - RATE_TENORS_YEARS[left])
            )
            rate_percent = RATE_CURVE_PERCENT[left] + weight * (
                RATE_CURVE_PERCENT[right] - RATE_CURVE_PERCENT[left]
            )
            return rate_percent / 100.0
    return RATE_CURVE_PERCENT[-1] / 100.0


def market_quote_inputs() -> dict[str, float]:
    """Derive the documented maturity, rate, forward, and effective yield."""

    # The source convention subtracts one calendar day for AM settlement.
    maturity_days = (EXPIRATION_DATE - QUOTE_DATE).days - 1
    time_to_maturity = maturity_days / 365.0
    rate = _linear_rate(time_to_maturity)

    parity_quotes = [
        quote for quote in MARKET_QUOTES if quote.strike == 3900.0
    ]
    call = next(quote for quote in parity_quotes if quote.option_type == "call")
    put = next(quote for quote in parity_quotes if quote.option_type == "put")
    call_mid = (call.bid + call.ask) / 2.0
    put_mid = (put.bid + put.ask) / 2.0
    forward = call.strike + math.exp(rate * time_to_maturity) * (call_mid - put_mid)
    effective_dividend_yield = rate - math.log(forward / SPX_CLOSE) / time_to_maturity
    return {
        "maturity_days": float(maturity_days),
        "time_to_maturity": time_to_maturity,
        "rate": rate,
        "forward": forward,
        "dividend_yield": effective_dividend_yield,
    }


def market_quote_validation_rows() -> list[dict[str, float | str | bool]]:
    """Validate the authors' pricer and IV solver on six real SPX quotes."""

    inputs = market_quote_inputs()
    rows: list[dict[str, float | str | bool]] = []
    for quote in MARKET_QUOTES:
        midpoint = (quote.bid + quote.ask) / 2.0
        our_iv = implied_volatility(
            SPX_CLOSE,
            quote.strike,
            inputs["time_to_maturity"],
            inputs["rate"],
            midpoint,
            quote.option_type,
            dividend_yield=inputs["dividend_yield"],
        )
        iv_abs_error, iv_rel_error = _absolute_relative_error(
            our_iv, quote.published_mid_iv
        )
        repriced = black_scholes_price(
            SPX_CLOSE,
            quote.strike,
            inputs["time_to_maturity"],
            inputs["rate"],
            quote.published_mid_iv,
            quote.option_type,
            dividend_yield=inputs["dividend_yield"],
        )
        price_abs_error, price_rel_error = _absolute_relative_error(repriced, midpoint)
        rows.append(
            {
                "contract": quote.contract,
                "option_type": quote.option_type,
                "strike": quote.strike,
                "bid": quote.bid,
                "ask": quote.ask,
                "midpoint": midpoint,
                "published_mid_iv": quote.published_mid_iv,
                "our_iv": our_iv,
                "iv_abs_error": iv_abs_error,
                "iv_rel_error": iv_rel_error,
                "repriced": repriced,
                "price_abs_error": price_abs_error,
                "price_rel_error": price_rel_error,
                "inside_bid_ask": quote.bid <= repriced <= quote.ask,
            }
        )
    return rows


def _scientific(value: float) -> str:
    return f"{value:.3e}"


def render_validation_report() -> str:
    """Render the complete W3-02 validation table and discrepancy discussion."""

    ql = _quantlib()
    reference_rows = reference_validation_rows()
    market_rows = market_quote_validation_rows()
    inputs = market_quote_inputs()

    reference_table = [
        "| Case | Type | Our price | QuantLib price | Price abs. error | Price rel. error | Our IV | QuantLib IV | IV abs. error | IV rel. error |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in reference_rows:
        display = {
            **row,
            "price_abs_error": _scientific(float(row["price_abs_error"])),
            "price_rel_error": _scientific(float(row["price_rel_error"])),
            "iv_abs_error": _scientific(float(row["iv_abs_error"])),
            "iv_rel_error": _scientific(float(row["iv_rel_error"])),
        }
        reference_table.append(
            "| {case_id} | {option_type} | {our_price:.10f} | "
            "{reference_price:.10f} | {price_abs_error} | {price_rel_error} | "
            "{our_iv:.10f} | {reference_iv:.10f} | {iv_abs_error} | "
            "{iv_rel_error} |".format(**display)
        )

    market_table = [
        "| Contract | Type | K | Bid--ask | Mid | Published IV | Our IV | IV abs. error | IV rel. error | Price at published IV | Price abs. error | Price rel. error | In spread |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in market_rows:
        display = {
            **row,
            "iv_abs_error": _scientific(float(row["iv_abs_error"])),
            "iv_rel_error": _scientific(float(row["iv_rel_error"])),
            "price_abs_error": _scientific(float(row["price_abs_error"])),
            "price_rel_error": _scientific(float(row["price_rel_error"])),
            "inside_bid_ask": "yes" if row["inside_bid_ask"] else "no",
        }
        market_table.append(
            "| {contract} | {option_type} | {strike:.0f} | {bid:.2f}--{ask:.2f} | "
            "{midpoint:.3f} | {published_mid_iv:.6f} | {our_iv:.9f} | "
            "{iv_abs_error} | {iv_rel_error} | {repriced:.9f} | "
            "{price_abs_error} | {price_rel_error} | {inside_bid_ask} |".format(
                **display
            )
        )

    max_reference_price = max(float(row["price_abs_error"]) for row in reference_rows)
    max_reference_iv = max(float(row["iv_abs_error"]) for row in reference_rows)
    max_market_price = max(float(row["price_abs_error"]) for row in market_rows)
    max_market_iv = max(float(row["iv_abs_error"]) for row in market_rows)

    return f"""# W3-02 Pricer and Implied-Volatility Validation

This report validates the authors' European Black--Scholes--Merton pricer and
Brent implied-volatility solver. These are single-option Track A quantities;
they do not define or approximate VIX, and they do not alter any locked Track B
choice.

## Independent library validation

Reference implementation: QuantLib {ql.__version__}. QuantLib's
`BlackCalculator` supplies prices in forward form, and
`blackFormulaImpliedStdDev` independently inverts the same reference prices.
Inputs use continuous rates and dividend yields, calendar-year maturity, and
annualized decimal volatility.

{chr(10).join(reference_table)}

The maximum absolute price error is {_scientific(max_reference_price)} price
units and the maximum absolute IV error is {_scientific(max_reference_iv)}.
The residuals are at floating-point and solver-tolerance scale; there is no
economically material library discrepancy in these cases.

## Fixed real-quote validation

Source: [HistoricalData.net free options sample]({QUOTE_SOURCE_PAGE}), file
`2022-09-15_options.csv`. The six limited example rows are European,
cash-settled, AM-settled SPX options expiring 2022-10-21. Prices are index
points and IV is annualized decimal volatility. The quote source computes its
published IV with Black-76, a Treasury-curve rate, and a put--call-parity
forward.

To match those documented conventions, maturity is
{int(inputs["maturity_days"])} / 365 = {inputs["time_to_maturity"]:.12f}: the
36 calendar dates to expiration less one day for AM settlement. Linear
interpolation of the source's 1-month 2.76% and 3-month 3.22% Treasury par
yields gives r = {inputs["rate"]:.12f}. The nearest-strike K=3900 call/put
midpoints imply F = {inputs["forward"]:.9f}; with the reported SPX close
S = {SPX_CLOSE:.2f}, the equivalent continuous carry input is
q = {inputs["dividend_yield"]:.12f}.

{chr(10).join(market_table)}

The authors' solver differs from the published midpoint IV by at most
{_scientific(max_market_iv)} in annualized decimal volatility. Repricing the
published six-decimal IV differs from the quote midpoint by at most
{_scientific(max_market_price)} index points, and every repriced value lies
inside its bid--ask spread.

## Explanation of discrepancies and scope

- The real-quote residuals are principally rounding: the source publishes IV
  to six decimals and documents a Brent tolerance of 1e-6. The much smaller
  QuantLib residuals use unrounded deterministic inputs.
- The Treasury inputs are par yields, not continuously compounded zero rates.
  Using the same decimal rate reproduces the source calculation, but it is an
  approximation to the economically ideal discount curve.
- SPX pays discrete dividends. Put--call parity absorbs expected dividends
  into an effective continuous carry rather than modelling each cash payment.
  Here q is negative ({inputs["dividend_yield"]:.4%}), so it should not be read
  as a literal dividend yield.
- The archive has no quote timestamps for 2022. Its underlying value is the
  official 16:00 ET SPX close, while index-option quotes can update later and
  call and put sides need not be synchronized. That timing mismatch can explain
  the unusual parity-implied carry and is not numerical solver error.
- Midpoints are not executable prices, and bid--ask width is a more relevant
  market-fit tolerance than machine precision. This six-contract check
  establishes implementation consistency only; it does not validate
  Black--Scholes as a complete model of the SPX volatility smile.

## Reproduction and provenance

Run `vrp-validate-options --output docs/w3_02_pricer_iv_validation.md` after
installing `.[validation]` or `.[dev]`. The source ZIP and full quote chain are
not committed. Artifact hashes, retrieval details, the fixed selection rule,
and licensing note are recorded in
`data/manifests/w3_02_option_quote_sample.json`.
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="write the Markdown report to this path; otherwise print it",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = render_validation_report()
    if args.output is None:
        print(report)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
