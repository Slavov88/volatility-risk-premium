# H9 options-trading data feasibility

**EXPLORATORY — POST H1–H5 RESULT SELECTION — PENDING INDEPENDENT REVIEW**

Status: **BLOCKED_AT_FEASIBILITY — NO OPTIONS STRATEGY RUN**. No historical executable SPX quotes, consistent contract surface, broker funding/margin history or trade records have been acquired. VIX levels and ex-post variance differences cannot provide executable option P&L.

Primary provider pages verified2026-10-13:

| Provider | Observable offering and coverage | Expense/licensing boundary |
|---|---|---|
| [Cboe DataShop Option Quotes](https://datashop.cboe.com/option-quote-intervals) | NBBO bid/ask and sizes, expiration/strike/type/root, interval OHLC/volume, optional Greeks; historical interval product advertises January2012 onward. | Selection-dependent order quote required; no evaluated order, no purchase. Product page states SPX underlying bid/ask/current underlying inclusion may require active CGIF licensing, fees starting$1000/month. This is a conditional index-feed license cost, **not** the cost of the full historical option dataset. Full-market historical orders have separate underlying-data exceptions. |
| [Algoseek pricing](https://algoseek.com/pricing/) and [options package](https://console.algoseek.com/marketplace/data-packages/equity_options) | Multiple historical options datasets; general pricing page mentions history from2014, specific trade/top-of-book package lists2017-02-01 onward. | Exact symbol/date/product license and expense require a tailored quote; estimated dataset dollar expense **UNKNOWN**, not zero. No account/payment/license obtained. |
| [Cboe SPX contract fact sheet](https://res-certification.cboe.com/resources/spx/spx-fact-sheet.pdf) | Contract multiplier$100, expiration/settlement distinctions between traditional SPX and SPXW. | Reference terms alone do not resolve historical listed-series changes, stale/crossed quotes, assignment/settlement cash flows, liquidity, funding or margin. |

Next feasible study would require an approved licensed sample, contracts aligned to timestamps/settlement, tradable-side fills with sizes, explicit slippage/hedging, cash collateral and broker-specific financing/margin rules. Historical bid/ask are executable proxies with fill uncertainty, not guaranteed prices. No messages were sent to providers and no data expense incurred. H6–H8 completion does not depend on H9. No synthetic variance-premium profits are reported.
