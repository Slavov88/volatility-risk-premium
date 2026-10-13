# Regime Definitions

**Decision date:** 2026-09-17

**Status:** frozen before regime-output inspection

**Tracker task:** W4-06

**Authoritative protocol:** `paper/method_protocol.md`

**Protocol version at freeze:** 1.0.1  
**Current execution protocol:** 1.1.0; the 2026-10-13 refinement makes H5's regression/null explicit without changing these frozen regime dates.

At this freeze, no regime-specific premium, forecast-loss, or forecast-ranking
output had been inspected. These definitions use only calendar dates and
external event chronology; no VIX, realized-variance, `VRP_X`, or model-loss
series was used to choose a boundary.

## Formal regime chronology

The formal recession/non-recession classification is the **NBER U.S. Business Cycle Dating Committee monthly chronology**.

Under protocol 1.1.0, the confirmatory test is `VRP_X = alpha + delta * recession + u` with a two-sided test of `delta=0` and the primary overlap-derived HAC rule. The calendar-year crisis windows below remain descriptive case studies and do not replace that test.

Daily mapping rule:

- each eligible forecast origin inherits the NBER status of its calendar month;
- under the NBER duration convention, the first recession month is the month after the business-cycle peak and the last recession month is the trough month;
- the regime label is used ex post for classification/interpretation only;
- the regime label is never an input to a VIX, GARCH, or naive forecast.

Authoritative chronology source:
https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions

The downloaded chronology version/retrieval date and its hash must be recorded before H5 is run.

## Case-study windows

The three case studies use a common, outcome-independent rule: the window is
the named Gregorian calendar year, from January 1 through December 31,
inclusive. This symmetric rule was selected before inspecting regime results
and deliberately avoids selecting market peaks, volatility thresholds, or
model-dependent break dates.

Window membership is assigned by **forecast-origin date**:

\[
\text{case}_{y,t}=\mathbf{1}\{y\text{-01-01}\le t\le y\text{-12-31}\},
\qquad y\in\{2008,2020,2022\}.
\]

- Only otherwise eligible forecast origins on the common evaluation mask are
  included. A weekend or exchange holiday at a calendar boundary does not move
  the boundary; it simply contributes no origin.
- The complete forward target attached to an included origin remains attached
  even when its outcome dates extend beyond December 31. The case-study label
  is not assigned from target-return dates.
- Case-study labels are descriptive and are never predictors.
- The windows do not replace or modify the formal NBER monthly regime
  classification. An origin may carry both a case-study label and its
  independently assigned NBER label.

### 2008 / Global Financial Crisis

- Start date: **2008-01-01**
- End date: **2008-12-31**, inclusive
- Boundary rule: all eligible forecast origins in calendar year 2008.
- External economic/event rationale: 2008 is the named annual case study. It
  lies within the NBER-dated 2007--09 recession and contains the acute
  financial-crisis events surrounding Bear Stearns, Lehman Brothers, and AIG.
- Boundary source: the calendar-year rule above; boundaries are not estimated
  from economic or market outcomes.
- Episode-context sources:
  - NBER, [US Business Cycle Expansions and Contractions](https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions)
  - Federal Reserve History, [Support for Specific Institutions](https://www.federalreservehistory.org/essays/support-for-specific-institutions)

### 2020 / COVID-19 shock

- Start date: **2020-01-01**
- End date: **2020-12-31**, inclusive
- Boundary rule: all eligible forecast origins in calendar year 2020.
- External economic/event rationale: 2020 is the named annual case study. The
  NBER identifies a February 2020 peak and April 2020 trough and attributes the
  unusually sharp downturn to the pandemic and public-health response.
- Boundary source: the calendar-year rule above; boundaries are not estimated
  from economic or market outcomes.
- Episode-context sources:
  - NBER, [Business Cycle Dating Committee Announcement, June 8, 2020](https://www.nber.org/news/business-cycle-dating-committee-announcement-june-8-2020)
  - NBER, [Business Cycle Dating Committee Announcement, July 19, 2021](https://www.nber.org/news/business-cycle-dating-committee-announcement-july-19-2021)

### 2022 / inflation and monetary-tightening stress

- Start date: **2022-01-01**
- End date: **2022-12-31**, inclusive
- Boundary rule: all eligible forecast origins in calendar year 2022.
- External economic/event rationale: 2022 is the named annual case study. The
  Federal Reserve documented elevated inflation and began raising the federal
  funds target range in March, followed by further increases during the year.
- Boundary source: the calendar-year rule above; boundaries are not estimated
  from economic or market outcomes.
- Episode-context sources:
  - Federal Reserve Board, [FOMC statement, March 16, 2022](https://www.federalreserve.gov/newsevents/pressreleases/monetary20220316a.htm)
  - Federal Reserve Board, [Monetary Policy Report, June 17, 2022](https://www.federalreserve.gov/monetarypolicy/files/20220617_mprfullreport.pdf)

## Lock rule

The dates above are frozen as of 2026-09-17. They cannot be moved because the
resulting premium or forecast output looks stronger or weaker. Any later
alternative window is exploratory, must be identified as post-freeze, and must
be reported alongside rather than in place of these pre-specified windows.

## 2026-10-13 chronology snapshot frozen before H5 computation

Official NBER chronology downloaded with default verified TLS at the retrieval
time in data/manifests/2026-10-13_nber_chronology.json. Original HTML SHA-256:
99401340ae9b97310803cdcd0db0731ba4b4739f5425a83c370d268e3fa5795d.
Parser uses monthly turning points, not quarter labels (February 2020 is
labelled 2019Q4 by NBER but remains February 2020 for monthly mapping).
1990-2025: 432 monthly flags, 36 recession months; peak month excluded,
trough included. Episodes: July 1990/March 1991, March/November 2001,
December 2007/June 2009, February/April 2020. Current-vintage labels are
ex-post classifications; later vintage revisions require preserved baseline
and versioned re-execution. Existing 2008/2020/2022 calendar-year boundaries
remain unchanged. H5 outcome not yet examined at this snapshot freeze.
