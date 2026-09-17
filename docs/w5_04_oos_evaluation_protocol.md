# W5-04 — Out-of-sample evaluation protocol

**Status:** frozen implementation specification before forecast comparison  
**Authoritative source:** `paper/method_protocol.md`, version 1.0.1  
**Substantive lock:** 2026-08-26  
**Technical sample-tail amendment:** 2026-08-27

This note operationalizes the locked protocol; it does not modify it. No
forecast ranking, test-period loss, or empirical target was inspected to make
these choices.

## Split and information set

- The initial estimation sample contains every valid S&P 500 return from the
  first valid sample observation through the last exchange session of 2006.
- Candidate evaluation origins begin on the first S&P 500 exchange session of
  2007 and cannot extend beyond 2025-12-31.
- A primary evaluation origin is eligible only if its complete interval through
  `t + 30 calendar days` is observed. S&P 500 observations through 2026-02-02
  may support late-2025 targets but can never become forecast origins.
- The origin is end of day. A predictor at `t` may use the return ending at
  `t`, but no observation dated after `t`. Every target return ends strictly
  after `t`.
- The first evaluation origin and last eligible origin are derived from the
  cleaned exchange-session sequence, not hard-coded as assumed weekdays.

The date split is constructed before model availability is considered. Formal
loss comparisons then apply the common mask described below.

## Estimation windows

The primary GARCH(1,1) window is expanding. At origin `t`, it contains every
valid return in the locked sample through and including `t`. The initial
through-2006 sample is therefore the seed, and each origin adds only information
then available.

The mandatory robustness window is five calendar years, defined exactly as

\[
(t-5\text{ calendar years},t].
\]

The left endpoint is excluded and the origin is included. For a February 29
origin whose five-year-prior year is not a leap year, the cutoff maps to
February 28. Both windows are re-created at every origin; neither model
parameters nor window length may be chosen using evaluation-period losses.

## Benchmarks and horizon matching

The primary naive benchmark is fixed before comparison:

\[
\widehat{GVAR}^{Naive}_{t,30c}
=
\frac{365}{30}
\sum_{d:t-30c<d\le t}r_d^2.
\]

It is a trailing exact-calendar window, uses decimal returns, produces
annualized decimal variance, excludes the left boundary, includes information
at the origin, and returns missing when the complete trailing interval is not
supported. It is compared with `IVAR_t` and the primary GARCH forecast against
the same forward 30-calendar-day realized-variance target.

For the mandatory fixed-21 analysis, the corresponding naive benchmark is the
sum of the last 21 returns through `t`, annualized by `252/21`. It remains a
robustness benchmark and cannot replace the primary calendar-matched benchmark.

## Common evaluation mask

The formal three-model comparison is restricted to the single intersection of:

1. eligible primary evaluation origins;
2. non-missing forward realized variance;
3. non-missing VIX implied variance;
4. non-missing expanding-window GARCH variance; and
5. non-missing naive variance.

RMSE, MAE, squared-error loss differentials, and encompassing analysis must all
use this same set of origins for a given formal comparison. Invalid negative or
infinite variance values are errors, not observations to silently drop. The
rolling-window and Student-t analyses are separately labelled robustness
comparisons and each uses its own explicitly reported common intersection.

## Test-period firewall

The 2007–2025 period may update recursively available model inputs and
estimation observations. It may not be used to select:

- the split date or forecast-origin cutoff;
- expanding versus rolling as the primary design;
- rolling-window length;
- GARCH order or primary innovation distribution;
- benchmark formula;
- target horizon, annualization, or loss function;
- missing-value treatment; or
- a subset of dates on which a preferred model ranks better.

Convergence failures and missing forecasts are recorded and passed to the
common-mask rule. They do not authorize specification changes. Any future
departure requires the protocol-deviation process and cannot displace the
locked confirmatory result.

## Deterministic implementation checks

`src/vrp/evaluation.py` implements the split, windows, benchmarks, and common
mask without reading market data or calculating forecast rankings. Unit tests
establish the 2006/2007 boundary, complete-target requirement, 2026
target-support restriction, exact endpoint conventions, annualization,
common-mask intersection, and leakage invariant that changing a post-origin
return cannot alter a predictor at `t`.
