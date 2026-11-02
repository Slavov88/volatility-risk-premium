# Econometrics integration audit

All results remain provisional pending independent coauthor review. The base
protocol 1.1.0 and the dated deviation allowing provisional execution before
freeze acceptance were read before numerical work. No main checkout changes,
new model substitutions, or significance-driven specifications were made.

## Recovered observations and independent inference

The provenance reconstruction recovered source bytes and exactly reproduced
all three frozen panel CSV hashes. Original source manifests are unavailable;
full production `verify_interim` replay is not claimed. The Python 3.12.12
reconstructed daily and target files differ from historical Python 3.11.5
bytes; comparison below is numerical, not byte-exact target replay.

Independent NumPy code reconstructs all six forward targets from the complete
canonical SPX history, with no removal of returns on missing-VIX dates. Maximum
absolute differences are 7.7e-15 for CC and 2.3e-16 for range targets. It verifies
IVAR units, implied-minus-realized sign, and derives L0=21 from explicit forward
return-date-set intersections on the 9,064 eligible origins. HAC uses Bartlett
weights, n/(n-k) correction, asymptotic normal two-sided inference, and chi-square
Wald tests. Primary coefficients and SEs agree with committed outputs to 1.8e-15.

| Test | Independently computed result |
|---|---|
| H1 | mean 0.01134891365950679; SE 0.002102594258336352; p 6.754702197666798e-8 |
| H2 | alpha -0.005364684998275593; beta 0.8637143195852902; joint Wald 42.50628357836643; p 5.886779893371189e-10 |
| H5 | recession difference -0.004222432516914858; SE 0.017152255870103227; p 0.8055478536096974 |

H5 uses 752 recession and 8,312 expansion origins under the locked peak-exclusive,
trough-inclusive NBER monthly chronology. Original NBER HTML bytes were not
recovered, so its source snapshot replay is not claimed. The independent receipt
also contains 66 robustness cells across periods, estimators, horizons, HAC
sensitivities, and deterministic nonoverlapping samples.

## Forecast reproduction status

Three fresh corrected-calendar cold-start GARCH runs completed on all 4,780
OOS origins each, with zero reported failures, using the locked Gaussian expanding,
Student-t expanding, and Gaussian rolling-five-year variants. These use no historical caches. Their
forecast schedule excludes future ad hoc closures while their target outcome
sets retain actual realized closures. Producer inference routines independently
check their HAC sandwiches and preserve the fixed Holm secondary-test family.

Fifteen newly fitted anchor cases repeat exactly in this runtime after every
post-origin return is perturbed; the training vectors and forecasts are unchanged.
That anchor replay is distinct from a full historical deterministic replay.
Historical forecast JSON/SQLite caches are not recovered, so the original
cache-correction replay script cannot honestly be run against them.

The fresh-versus-committed comparison covers all 72 combinations of three model
variants, two horizons, three estimators, two periods, and overlapping versus
nonoverlapping masks. All 72 mask hashes and counts match; the committed manifest
contains hashes rather than origin lists, so direct list comparison is unavailable.
No recorded p-value changes its 5% classification. The largest absolute difference
among recorded numeric fields is 0.0000950907 (an H4 design condition number);
the largest p-value difference is 0.0000112951. These are observed differences,
not a claim that a pre-specified numerical tolerance was met. The receipt records
every numeric difference by field and cell. This is a fresh numerical comparison,
not historical cache or byte replay.

For the primary 30-calendar-day CC full-period overlapping comparison (n=4,780),
VIX, expanding Gaussian GARCH, and naive RMSEs are 0.06863567, 0.07212622, and
0.08422313. The mean VIX-minus-GARCH squared-loss difference is -0.00049134
(HAC SE 0.00053841, p=0.36147); this does not establish equal forecast accuracy.
H4 estimates for VIX and GARCH are 0.67946 (p=0.0001193) and 0.20569
(p=0.32268), respectively. The rolling Gaussian GARCH coefficient is 0.29063
(p=0.04846), while Student-t expanding is 0.06863 (p=0.67030); these sensitivity
results should be reported rather than selected by significance. Independent NumPy
H3/H4 score-sandwich calculations from the new per-origin records agree with the
new producer to maximum absolute difference 6.0e-15 across those reported
coefficients, standard errors, and p-values. This independently checks inference,
not the GARCH fitting implementation.

Portable scripts and receipts are in `econ-delivery/`. New private per-origin
fit data are in `econ-fresh/` and are not part of the portable delivery.

## GARCH fit and residual diagnostics supplement

The 14,340 new cold-start fits all report convergence flag zero. Across the
4,780 expanding Gaussian fits, median (minimum–maximum) persistence is 0.98937
(0.98351–0.99584); for expanding Student-t it is 0.99659 (0.99470–0.99965);
and for rolling Gaussian it is 0.98039 (0.87964–1.0000000000000004). Two rolling
values are numerically at or above one; the excess above one is at floating-point
scale. High persistence and boundary estimates are findings, not grounds for
substituting a model. The accompanying parameter summary reports mu, omega,
alpha, beta, Student-t nu, persistence and log likelihood across every fit;
log likelihoods across expanding windows have different observation counts.

Fresh residual-diagnostic refits at the protocol-fixed first and final eligible
origin of each year 2007–2025 yielded 38 anchors per variant, all converged. Their
training hashes match and their fitted parameters equal the corresponding fresh
checkpoint values in this runtime. At a descriptive 5% threshold, ARCH-LM(10)
p-values are below 0.05 in 2/38 Gaussian expanding, 10/38 Student-t expanding,
and 8/38 Gaussian rolling anchors; squared-residual Ljung–Box(21) gives 0/38,
0/38 and 2/38 respectively. These are repeated, dependent diagnostic tests and
are not multiplicity-adjusted. The complete individual diagnostic statistics
and p-values appear in the receipt and CSV; they do not establish diagnostics at
all 4,780 origins. These are newly generated computations, not recovered historical
fit or diagnostic records.
