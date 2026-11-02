# W3-02 Pricer and Implied-Volatility Validation

This report validates the authors' European Black--Scholes--Merton pricer and
Brent implied-volatility solver. These are single-option Track A quantities;
they do not define or approximate VIX, and they do not alter any locked Track B
choice.

## Independent library validation

Reference implementation: QuantLib 1.43. QuantLib's
`BlackCalculator` supplies prices in forward form, and
`blackFormulaImpliedStdDev` independently inverts the same reference prices.
Inputs use continuous rates and dividend yields, calendar-year maturity, and
annualized decimal volatility.

| Case | Type | Our price | QuantLib price | Price abs. error | Price rel. error | Our IV | QuantLib IV | IV abs. error | IV rel. error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| atm_1y | call | 10.4505835722 | 10.4505835722 | 1.421e-14 | 1.360e-15 | 0.2000000000 | 0.2000000000 | 2.438e-13 | 1.219e-12 |
| atm_1y | put | 5.5735260223 | 5.5735260223 | 3.553e-15 | 6.374e-16 | 0.2000000000 | 0.2000000000 | 2.432e-13 | 1.216e-12 |
| dividend_otm | call | 0.7242082555 | 0.7242082555 | 7.994e-15 | 1.104e-14 | 0.3500000000 | 0.3500000000 | 1.288e-14 | 3.680e-14 |
| negative_rate | put | 7.9196599578 | 7.9196599578 | 3.553e-15 | 4.486e-16 | 0.1500000000 | 0.1500000000 | 0.000e+00 | 0.000e+00 |
| short_dated | call | 1.0192654416 | 1.0192654416 | 3.109e-15 | 3.050e-15 | 0.5000000000 | 0.5000000000 | 1.943e-15 | 3.886e-15 |
| long_dated | put | 0.2143306095 | 0.2143306095 | 1.862e-14 | 8.689e-14 | 0.1000000000 | 0.1000000000 | 3.065e-13 | 3.065e-12 |

The maximum absolute price error is 1.862e-14 price
units and the maximum absolute IV error is 3.065e-13.
The residuals are at floating-point and solver-tolerance scale; there is no
economically material library discrepancy in these cases.

## Fixed real-quote validation

Source: [HistoricalData.net free options sample](https://historicaldata.net/options.html), file
`2022-09-15_options.csv`. The six limited example rows are European,
cash-settled, AM-settled SPX options expiring 2022-10-21. Prices are index
points and IV is annualized decimal volatility. The quote source computes its
published IV with Black-76, a Treasury-curve rate, and a put--call-parity
forward.

To match those documented conventions, maturity is
35 / 365 = 0.095890410959: the
36 calendar dates to expiration less one day for AM settlement. Linear
interpolation of the source's 1-month 2.76% and 3-month 3.22% Treasury par
yields gives r = 0.027946575342. The nearest-strike K=3900 call/put
midpoints imply F = 3916.093068610; with the reported SPX close
S = 3901.35, the equivalent continuous carry input is
q = -0.011388364485.

| Contract | Type | K | Bid--ask | Mid | Published IV | Our IV | IV abs. error | IV rel. error | Price at published IV | Price abs. error | Price rel. error | In spread |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPX221021C03850000 | call | 3850 | 154.90--156.00 | 155.450 | 0.250087 | 0.250086565 | 4.355e-07 | 1.741e-06 | 155.450203203 | 2.032e-04 | 1.307e-06 | yes |
| SPX221021P03850000 | put | 3850 | 89.20--89.90 | 89.550 | 0.250122 | 0.250121258 | 7.424e-07 | 2.968e-06 | 89.550346447 | 3.464e-04 | 3.869e-06 | yes |
| SPX221021C03900000 | call | 3900 | 124.40--125.40 | 124.900 | 0.242425 | 0.242425104 | 1.043e-07 | 4.300e-07 | 124.899949915 | 5.009e-05 | 4.010e-07 | yes |
| SPX221021P03900000 | put | 3900 | 108.50--109.20 | 108.850 | 0.242425 | 0.242425104 | 1.043e-07 | 4.300e-07 | 108.849949915 | 5.009e-05 | 4.601e-07 | yes |
| SPX221021C03950000 | call | 3950 | 96.90--97.80 | 97.350 | 0.234189 | 0.234188807 | 1.926e-07 | 8.225e-07 | 97.350092616 | 9.262e-05 | 9.514e-07 | yes |
| SPX221021P03950000 | put | 3950 | 130.70--131.60 | 131.150 | 0.234156 | 0.234155140 | 8.604e-07 | 3.674e-06 | 131.150413710 | 4.137e-04 | 3.154e-06 | yes |

The authors' solver differs from the published midpoint IV by at most
8.604e-07 in annualized decimal volatility. Repricing the
published six-decimal IV differs from the quote midpoint by at most
4.137e-04 index points, and every repriced value lies
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
  Here q is negative (-1.1388%), so it should not be read
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
