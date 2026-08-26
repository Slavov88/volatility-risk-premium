# Regime Definitions

**Status:** pre-analysis template; formal chronology locked, case-study dates not yet frozen  
**Authoritative protocol:** `paper/method_protocol.md`

## Formal regime chronology

The formal recession/non-recession classification is the **NBER U.S. Business Cycle Dating Committee monthly chronology**.

Daily mapping rule:

- each eligible forecast origin inherits the NBER status of its calendar month;
- under the NBER duration convention, the first recession month is the month after the business-cycle peak and the last recession month is the trough month;
- the regime label is used ex post for classification/interpretation only;
- the regime label is never an input to a VIX, GARCH, or naive forecast.

Authoritative chronology source:
https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions

The downloaded chronology version/retrieval date and its hash must be recorded before H5 is run.

## Case-study windows

Exact windows for the three project case studies must be frozen **before any regime-specific premium or forecast output is inspected**.

### 2008 / Global Financial Crisis

- Start date: **TO BE LOCKED**
- End date: **TO BE LOCKED**
- External economic/event rationale: **TO BE RECORDED**
- Source defining the window: **TO BE RECORDED**

### 2020 / COVID-19 shock

- Start date: **TO BE LOCKED**
- End date: **TO BE LOCKED**
- External economic/event rationale: **TO BE RECORDED**
- Source defining the window: **TO BE RECORDED**

### 2022 / inflation and monetary-tightening stress

- Start date: **TO BE LOCKED**
- End date: **TO BE LOCKED**
- External economic/event rationale: **TO BE RECORDED**
- Source defining the window: **TO BE RECORDED**

## Lock rule

Once exact case-study dates are committed, they cannot be moved because the resulting VRP or forecast plots look stronger or weaker. A later alternative window is exploratory and must be reported alongside the original pre-specified window.
