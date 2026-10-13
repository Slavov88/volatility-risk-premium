"""Publish frozen cash-yield sensitivity results, tables and figures."""
import json
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from vrp.cash_yield import ROOT,OUT,MODELS,SCENARIOS
from vrp.quant_extension import sha,persist,implementation,checked_hash

DOC=ROOT/'docs';TABLE=DOC/'tables/h8_cash_yield';FIG=DOC/'figures/h8_cash_yield'


def fmt(v):
    if v is None:return '—'
    if isinstance(v,(float,np.floating)):return f'{v:.10g}'
    if isinstance(v,list):return ', '.join(map(fmt,v))
    return str(v).replace('|',' / ')


def table(rows,columns):
    return '\n| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+''.join('| '+' | '.join(fmt(r.get(k)) for k in columns)+' |\n' for r in rows)+'\n'


def get(rows,**filters):return next(r for r in rows if all(r.get(k)==v for k,v in filters.items()))


def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight',metadata={'Software':'Matplotlib'})
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)


def publish():
    code=implementation(['scripts/publish_h8_cash_yield.py'])
    x=json.loads((OUT/'results.json').read_bytes());audit=json.loads((OUT/'independent_audit.json').read_bytes())
    income=json.loads((OUT/'income_uncertainty.json').read_bytes())
    if audit['results_sha256']!=sha(OUT/'results.json') or income['primary_results_sha256']!=sha(OUT/'results.json'):raise ValueError('Parent result identity')
    for path,digest in x['input_sha256'].items():checked_hash(ROOT/path,digest)
    for folder in [TABLE,FIG]:folder.mkdir(parents=True,exist_ok=True)
    names=['summary','periods','attribution','uncertainty','ranking_uncertainty','DGS1MO_schedule','DTB4WK_schedule',
           'source_missing','vintage_checks','rankings','nominal_attribution','cash_income_uncertainty','annual_cash_credit']
    for name in names:
        source=OUT/(name+'.csv');target=TABLE/(name+'.csv')
        if not target.exists() or sha(target)!=sha(source):shutil.copyfile(source,target)
    rows=x['summary'];comparison=[]
    for m in MODELS:
        old=get(rows,scenario='zero',strategy=m,cost_bps=5);new=get(rows,scenario='dgs1mo_full',strategy=m,cost_bps=5)
        ci=get(x['uncertainty'],scenario='dgs1mo_full',candidate=m,cost_bps=5,block=63,comparison='cash_minus_zero',metric='cagr')['ci95']
        comparison.append({'strategy':m,'cash_calendar_%':100*new['mean_cash_fraction_calendar_weighted'],
             'zero_CAGR_%':100*old['cagr'],'DGS_CAGR_%':100*new['cagr'],'CAGR_change_pp':100*new['cash_income_cagr_increment'],
             'CAGR_change_CI_pp':[100*v for v in ci],'zero_Sharpe':old['sharpe_zero_reference'],'DGS_Sharpe':new['sharpe_zero_reference'],
             'zero_common_excess_Sharpe':old['sharpe_excess_common_dgs1mo'],'DGS_common_excess_Sharpe':new['sharpe_excess_common_dgs1mo'],
             'DGS_vol_%':100*new['annual_vol'],'DGS_tracking_RMSE_%':100*new['rolling21_target_rmse']})
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.2,'pdf.fonttype':42,'ps.fonttype':42})
    fig,ax=plt.subplots(figsize=(7.5,3.6)); y=np.arange(len(comparison));v=np.array([r['CAGR_change_pp'] for r in comparison]);ci=np.array([r['CAGR_change_CI_pp'] for r in comparison])
    ax.errorbar(v,y,xerr=np.vstack([v-ci[:,0],ci[:,1]-v]),fmt='o',color='#0072b2',capsize=3)
    ax.axvline(0,color='gray',lw=.8);ax.axvline(.5,color='#d55e00',ls=':',lw=1)
    ax.set(yticks=y,yticklabels=MODELS,xlabel='Net CAGR change vs zero cash interest (percentage points / year)');ax.invert_yaxis()
    save(fig,'cash_cagr_increment')
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),sharey=True);ticks=np.arange(len(MODELS));width=.34
    for ax,metric,title in [(axes[0],'sharpe_zero_reference','Zero reference'),(axes[1],'sharpe_excess_common_dgs1mo','Common DGS cash-proxy reference')]:
        zero=[get(rows,scenario='zero',strategy=m,cost_bps=5)[metric] for m in MODELS]
        full=[get(rows,scenario='dgs1mo_full',strategy=m,cost_bps=5)[metric] for m in MODELS]
        ax.bar(ticks-width/2,zero,width,label='Zero cash interest',color='#999999')
        ax.bar(ticks+width/2,full,width,label='Full DGS pass-through',color='#0072b2')
        ax.set(xticks=ticks,xticklabels=MODELS,title=title);ax.tick_params(axis='x',labelrotation=25)
    axes[0].set_ylabel('Sharpe (√252 annualization)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,1.12),ncol=2,frameon=False)
    save(fig,'cash_sharpe_references')
    fig,ax=plt.subplots(figsize=(8.5,3.6))
    colors={'trailing':'#777777','vix':'#0072b2','garch':'#009e73','combined':'#d55e00'}
    years=list(range(2012,2027))
    for m in MODELS[1:]:
        values=[get(income['annual_cash_credit'],scenario='dgs1mo_full',strategy=m,cash_credit_year=y)['cash_income_normalized_sum']*100 for y in years]
        ax.plot(years[:-1],values[:-1],'o-',lw=1.4,label=m,color=colors[m])
        ax.scatter([years[-1]],[values[-1]],facecolors='none',edgecolors=colors[m],s=30)
    ax.set(xlabel='Cash credit year (2026 is the terminal two-day stub)',ylabel='Sum of interest / prior NAV (%)',xticks=years[::2]);ax.legend(ncol=4,loc='lower center',bbox_to_anchor=(.5,1.02),frameon=False)
    save(fig,'annual_cash_income')
    preamble='**EXPLORATORY CASH-YIELD SENSITIVITY — PENDING INDEPENDENT COAUTHOR REVIEW**\n\nPlan committed as `669af87`, source-batching / common-Sharpe clarification `f952067`, before any portfolio comparisons. Corrected sensitivity v2 restores the original H8 execution-date period masks; v1 full-sample results are unchanged and preserved. Same3520 marks2012-01-04 open–2026-01-02 open,3519 trades/signals, five strategies and0/1/5/10/25bps costs. No model refit, exposure change, new strategy, threshold search or future-hypothesis execution.\n\n'
    source=x['rates'];coverage=[]
    for identifier in ['DGS1MO','DTB4WK','DTB3','SOFR']:
        s=source['series'][identifier]
        coverage.append({'series':identifier,'provider_coverage_start':s['coverage_start_from_provider_form'],
            'frozen_first':s['current_first'],'frozen_last':s['current_last'],
            'initial_release_n':s.get('initial_n_finite'),'role':'primary' if identifier=='DGS1MO' else 'fixed alternative' if identifier=='DTB4WK' else 'investigated, not executed'})
    provenance=f'Primary result SHA `{sha(OUT/"results.json")}`; rate-source manifest SHA `{x["rate_source_manifest_sha256"]}`; independent audit SHA `{sha(OUT/"independent_audit.json")}`. [Result manifest](../data/manifests/h8_cash_results_v2.json), [source provenance](../data/manifests/h8_cash_rate_source_v1.json), [independent audit](../data/manifests/h8_cash_independent_audit_v2.json), [fixed plan](../paper/h8_cash_yield_plan.md). Original [H8 zero-interest report](h8_portfolio_economic_value.md) is preserved.\n'
    text='# H8 cash-yield sensitivity\n\n'+preamble
    text+='**Answer: cash income materially changes return levels and some Sharpe rankings, but does not reverse the CAGR ranking or establish superiority of the sophisticated combined strategy.** Under full DGS pass-through at5bps, VIX CAGR rises0.643056pp and combined0.552976pp, exceeding the predeclared0.5pp descriptive materiality threshold at the point estimates. Their bootstrap lower bounds are below0.5pp: historical resampling does not establish that minimum effect prospectively. Full and half compensation are modeled assumptions, not observed broker credits.\n'
    text+=table(comparison,['strategy','cash_calendar_%','zero_CAGR_%','DGS_CAGR_%','CAGR_change_pp','CAGR_change_CI_pp','zero_Sharpe','DGS_Sharpe','zero_common_excess_Sharpe','DGS_common_excess_Sharpe','DGS_vol_%','DGS_tracking_RMSE_%'])
    text+='CAGR point ordering remains buyhold > trailing > GARCH > combined > VIX. The original zero-reference Sharpe ordering (trailing > GARCH > combined > VIX > buyhold) changes to VIX > GARCH > combined > trailing > buyhold at full pass-through. With a common DGS cash-proxy reference the full-interest ordering is trailing > GARCH > combined > VIX > buyhold. These small Sharpe separations are uncertain; a point-ranking reversal is not demonstrated alpha. Buyhold has zero uninvested cash and remains exactly unchanged in every cost/scenario.\n\n'
    text+='The combined-minus-trailing CAGR disadvantage narrows from1.821341pp to1.672469pp; the primary block63 interval for trailing-minus-combined is[0.559587,2.854898]pp. Combined rolling21 tracking RMSE is3.027755% versus trailing2.960578%, still worse at the point estimate; its difference interval spans zero. GARCH remains the best point tracker. The original joint H8 gate still fails: no >=0.005 tracking-RMSE reduction and combined loses more than0.005 CAGR against trailing. Every cash scenario retains that negative gate. Accounting for cash makes the zero-interest simplification economically meaningful, without changing the underlying variance forecasts or proving that low equity exposure is efficient for every investor.\n\n'
    text+='![CAGR cash-assumption effect](figures/h8_cash_yield/cash_cagr_increment.png)\n\nFull DGS pass-through versus frozen zero-interest counterpart at5bps; paired block63/1000 percentile95% intervals. The dotted line is the fixed0.5pp materiality descriptor, not a trading-success or hypothesis-test gate.\n\n![Sharpe reference comparison](figures/h8_cash_yield/cash_sharpe_references.png)\n\nIdentical portfolios under two clearly named references. The common benchmark is a modeled Treasury-based liquid cash account, not a traded overnight risk-free asset.\n\n'
    text+='## Source coverage, convention and availability\n\n'+table(coverage,['series','provider_coverage_start','frozen_first','frozen_last','initial_release_n','role'])
    text+='[DGS1MO](https://fred.stlouisfed.org/series/DGS1MO) is a one-month Treasury constant-maturity yield quoted on an investment basis in annual percent. It is interpolated from the Treasury curve and has full-period support; it is not a bill purchase price or guaranteed cash-account return. [DTB4WK](https://fred.stlouisfed.org/series/DTB4WK) and [DTB3](https://fred.stlouisfed.org/series/DTB3) are secondary-market bill quotes on bank discount basis (360-day quotation year). The latter longer maturity is documented but not selected after results. See [H15 definitions](https://www.federalreserve.gov/releases/h15/) and [Treasury methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology).\n\n'
    text+='For DTB4WK, d=quote_percent/100; fixed28-day price/face=1−d*28/360; ACT365 investment equivalent r=(d/360)/(1−d*28/360)*365. This preserves the discount-price denominator. Merely dividing the discount quote by100 would be incorrect. The28-day remaining maturity is an explicit standardized conversion, not a reconstructed held bill. DGS annual percent is divided by100 once. ACT/365F is the chosen modeled cash-account accrual convention; it is not asserted to be the legal coupon/day-count convention of a Treasury security. Negative quotes would remain negative rather than being clipped.\n\n'
    text+='Official [SOFR](https://www.newyorkfed.org/markets/reference-rates/additional-information-about-reference-rates) began with value date2018-04-02, first published2018-04-03. It measures secured overnight Treasury repo transactions and uses ACT360 money-market accrual; the next-business-day publication is after the transactions measured. The frozen FRED series starts2018-04-03. It lacks2012–2017, so no SOFR backcast, splice or full-period SOFR scenario is invented. A broker cash sweep need not receive SOFR or Treasury yields.\n\n'
    text+='Current FRED series can be revised. Primary and bill scenarios instead use the [ALFRED initial-release-only format](https://alfred.stlouisfed.org/help/downloaddata), with actual archived realtime_start dates. [ALFRED documentation](https://alfred.stlouisfed.org/help) explains archive vintage meaning and possible source-versus-FRED availability differences. The archive is date-granular: conservatively treat each value as usable only at00:00 New York on the next calendar date. Select the freshest initial observation available at the previous opening, lock it for that interval, and never use the ending-day quote. The [current H15 release](https://www.federalreserve.gov/releases/h15/) is at4:15pm; [historical2012 H15](https://www.federalreserve.gov/releases/h15/20120625/) had Monday releases with Tuesday–Friday updates. We do not invent historical intraday timestamps from the current schedule. First-release retention ignores later corrections even when they would subsequently be known, a documented conservative proxy policy.\n\n'
    text+=table([{'series':k,**v} for k,v in audit['rate_checks'].items()],['series','intervals','elapsed_days_total','multi_day_intervals','max_elapsed_days','max_quote_age_days','max_factor_error'])
    text+='Independent initial-release selection and ten actual vintage-snapshot checks pass. There are769 multiday intervals per rate source, with maximum5 calendar days (including exchange closures). All5112 calendar days accrue; leap day counts, DST clock hours do not alter ACT day counts. Maximum known-quote age is7 days, below the fixed15-day fail guard. Among finite initial observations, no differences versus current-history quotes were found. However, current history contains four finite cells absent/missing in the initial exports; they are explicitly not filled:\n'
    text+=table(audit['current_finite_but_initially_missing'],['series','observation_date','current_percent','initial_realtime_start_date','treatment'])
    text+='The initial download attempt exceeded the provider450-vintage limit and was rejected before any portfolio comparison. Accepted downloads use disjoint<=400-vintage batches, with ZIP/member/form/request/merged-data SHA-256 provenance and normal TLS verification. The only later execution stops were CSV integer-versus-float type inference and a disk-full duplicate-output write; exact value/byte controls and immutable hardlink reuse resolved them. No stopped process supplied a new scientific result.\n\n'
    text+='## Accrual and fixed execution\n\nInterest = actual prior-opening post-trade cash × historically known annual rate × elapsed calendar days /365. It is credited at the next open before the original ex-date dividend cash and rebalance. The opening-to-opening rate is locked across holidays/weekends; there is no invented holiday observation or rate update inside a locked interval. First funded opening earns no pre-inception interest. Terminal opening receives the final interval income and old-holding dividend, with no final trade or liquidation fee. Cash compounds through subsequent actual balances; no intra-interval compounding. The full path and all date/quote/release fields are retained in100 new ledgers. Dividend cash newly credited at an open cannot earn interest for the previous interval.\n\n'
    text+='Interest changes portfolio wealth, shares and trade notionals while preserving every target weight and rebalance date. Freezing dollar trades would break self-financing. Equity quote data, original fractional-share/open-fill/ex-date-dividend assumptions, cash liquidity, taxes excluded and flat traded-notional fees are preserved. No Treasury mark-to-market return, maturity roll, spread, sweep charge or actual broker contract is modeled. The50% pass-through case illustrates compensation sensitivity; it does not assert a particular broker historically paid half a Treasury quote.\n\n'
    text+='## Fixed alternatives, costs and uncertainty\n\n'
    text+=table([r for r in rows if r['cost_bps']==5],['scenario','strategy','cagr','sharpe_zero_reference','sharpe_excess_common_dgs1mo','annual_vol','rolling21_target_rmse','max_drawdown'])
    selected=[r for r in x['uncertainty'] if r['comparison']=='cash_minus_zero' and r['scenario']=='dgs1mo_full' and r['cost_bps']==5 and r['metric']=='cagr']
    text+=table(selected,['block','candidate','estimate','ci95'])
    text+='Paired circular blocks21/63/126,1000 draws,seed1729 preserve return/rate pairing; full sample metrics and rolling windows are recomputed. Cash-income/log-component streams are resampled with the same fixed design. These intervals condition on historical regimes and the chosen cash model, not future rates or broker compensation. Drawdown intervals are descriptive because resampled paths stitch regimes. No optimization, crisis deletion or new forecast family is selected. All100 scenario/cost/strategy summaries, all10 pair contrasts per scenario at5bps, rankings and ranking frequencies remain in the complete tables.\n\n'
    text+='Full tables: [summary](tables/h8_cash_yield/summary.csv), [all paired uncertainty](tables/h8_cash_yield/uncertainty.csv), [rank orders](tables/h8_cash_yield/rankings.csv), [bootstrap rank frequencies](tables/h8_cash_yield/ranking_uncertainty.csv), [DGS timing](tables/h8_cash_yield/DGS1MO_schedule.csv), [bill timing](tables/h8_cash_yield/DTB4WK_schedule.csv), [snapshot checks](tables/h8_cash_yield/vintage_checks.csv). [Economic attribution](h8_economic_attribution.md) gives units, income, fees, periods and exact identities.\n\n'+provenance
    (DOC/'h8_cash_yield_sensitivity.md').write_text(text,encoding='utf-8',newline='\n')
    text='# H8 economic attribution with cash income\n\n'+preamble
    text+='Cash yield is the sole changed economic assumption. CAGR order stays unchanged across all four scenarios at each fixed cost. Full pass-through reverses several zero-reference Sharpe point ranks, but no paired Sharpe separation establishes a superior strategy. The original combined practical gate remains failed, and comparison of portfolios with different realized risk cannot be interpreted as alpha.\n\n'
    text+='## Cash allocation and income units\n\nAll dollar quantities divide by initial NAV1. Calendar-weighted cash fraction averages post-trade opening cash fractions using actual interval days; session mean also includes the final drifted opening. Target weights are identical across scenarios, so calendar-weighted fractions are identical; income compounds the dollar base. Sum(I/previous NAV)/elapsed years is an annual normalized income measure, distinct from income dollars/initial NAV/year. CAGR increment compares fully self-financing interest-bearing and zero-interest NAV paths, and is not either of those annualized income measures. Elapsed CAGR length uses the original365.25 calendar-day year; interest accrual uses ACT/365F.\n'
    primary=[r for r in rows if r['scenario']=='dgs1mo_full' and r['cost_bps']==5]
    text+=table(primary,['strategy','mean_cash_fraction_calendar_weighted','mean_cash_fraction_session','cash_income_initial_nav','cash_income_initial_nav_per_year','annual_normalized_cash_income','cash_income_cagr_increment'])
    text+=table([r for r in income['uncertainty'] if r['scenario']=='dgs1mo_full' and r['block']==63 and r['metric']=='annual_normalized_cash_income'],['strategy','estimate','ci95'])
    text+='VIX holds approximately38.010% calendar-weighted cash, combined34.123%, GARCH27.066%, trailing22.724%. VIX therefore gains more cash income, but return/risk outcomes also depend on equity exposure and the timing of rates. A larger cash allocation does not alone imply better utility. Buyhold receives no cash income and is an exact control.\n\n'
    text+='![Calendar cash-income credits](figures/h8_cash_yield/annual_cash_income.png)\n\nSum of cash interest/prior NAV by credit year at5bps, full DGS proxy. The2026 point is the two-day terminal interval only, not a full-year estimate; original evaluation and final endpoint are unchanged.\n\n'
    text+='## Exact accounting and reinvestment\n\nDaily return = [old-share overnight P&L + old-share dividend + new-share intraday P&L + cash interest − fee] / previous NAV. First row starts in cash at open; final row has no intraday exposure. Interest uses the prior actual cash balance and is not earned on a newly received dividend. Cash/shares are solved after cost; fee equals cost-rate × absolute traded shares × opening price. All100 ledgers pass the independent Decimal rate/income and separate algebraic rebalance audit. Maximum independent economic/nominal residual is '+fmt(audit['max_independent_summary_error'])+'.\n\n'
    text+=table([r for r in audit['nominal_terminal_attribution'] if r['scenario']=='dgs1mo_full' and r['cost_bps']==5],['strategy','terminal_nav_change','cash_interest_initial_nav','changed_equity_pnl_initial_nav','changed_dividends_initial_nav','changed_negative_fees_initial_nav','residual'])
    text+='These dollar changes sum exactly to terminal NAV change. Interest dollars alone do not equal terminal wealth change: credited cash can subsequently fund equity/dividend returns and changes paid fees. The different balances are outcomes of the unchanged weight policy, not parameter changes.\n\n'
    text+='For normalized returns, delta r = direct I/previous cash-scenario NAV + changed normalized equity/dividend P&L + changed negative fee. Multiply each component by L=log((1+r_cash)/(1+r_zero))/(r_cash−r_zero), with the continuous limit1/(1+r_zero), to allocate incremental log wealth exactly. Apply one common total-growth-to-CAGR multiplier to allocate the net CAGR change. This is a fixed accounting allocation, not unique causal attribution. Indirect terms are small in normalized/log units because prior compounding increases both the invested-dollar base and the NAV denominator; nominal reinvestment contributions can still be substantial.\n'
    text+=table([r for r in x['attributions'] if r['scenario']=='dgs1mo_full' and r['cost_bps']==5],['strategy','incremental_log_growth','direct_interest_log_contribution','changed_equity_dividend_log_contribution','changed_fee_log_contribution','direct_interest_cagr_allocation','changed_equity_dividend_cagr_allocation','changed_fee_cagr_allocation','log_attribution_residual'])
    text+='## Fees, drawdown and target tracking\n\nLower volatility is not necessarily better target tracking. Cash interest moves combined annual volatility only from8.438373% to8.439011%; rolling RMSE moves3.028143%→3.027755%. It improves combined max drawdown from−13.270637% to−12.877033%, but leaves it slightly worse than trailing’s−12.814605%. These are historical path summaries, not independent crisis replications. Exact fee-dollar sums and gross/net CAGR/log-growth drag are separate: fees paid/initial NAV do not equal annual drag, and fee effects include changed notional and compounding. Higher-income VIX still has higher turnover and cost drag than combined/trailing.\n'
    text+=table(rows,['scenario','strategy','cost_bps','cagr','sharpe_zero_reference','sharpe_excess_common_dgs1mo','annual_vol','rolling21_target_rmse','max_drawdown','annual_turnover_nav','cost_initial_nav','gross_minus_net_cagr','gross_minus_net_log_growth'])
    text+='## Fixed periods and ranking limits\n\nPeriod masks use execution Date, exactly as original H8. All25 zero-interest fixed-period model summaries reproduce the original archived values exactly; period-local NAV starts1 as originally registered, while fee/income dollar sums retain full-run initial-NAV units. No new signal-date indexing is substituted. Crisis2020/2022 overlap the broader period panels and cannot be summed as disjoint observations.\n'
    text+=table(x['periods_5bps'],['scenario','strategy','period','n','cagr','annual_vol','rolling21_target_rmse','max_drawdown','cash_income_initial_nav'])
    text+='The main CAGR contrast favors trailing over combined after cash income, with block63 historical interval excluding zero, but their Sharpe differences remain uncertain. This reinforces that omitted cash income changes absolute economics and reference-dependent ranks; it does not show that a forecast combination beats strong simple controls. Half pass-through gives roughly half the CAGR benefit; the standardized bill alternative is close to the primary. No broker-specific compensation, spreads, taxes or cash-management friction is identified by these tests.\n\n'
    text+='## Preservation and reproduction\n\nThe corrected v2 sensitivity is current. V1 remains local and in its original manifest: its full-sample100 ledgers/results/inference are valid and identical; its new period summaries used signal origin instead of the original H8 execution Date and are superseded for comparison to original period results. V2 corrects only those period masks and adds an exact zero-period gate. A disk-full write interrupted the first v2 attempt; verified identical CSVs are reused as immutable hardlinks to v1, while distinct period/results/audit metadata remain separate. No original H8 or Task1/Task2 file was deleted or rewritten. All25 original zero ledgers reproduce numerical values AND original CSV bytes exactly; buyhold remains unchanged in20 scenario/cost controls. Cash simulations did not refit H7 or alter signals.\n\n'
    text+='Run committed producers against the frozen local data: `scripts/run_h8_cash_yield.py`, `scripts/audit_h8_cash_yield.py`, `scripts/h8_cash_income_uncertainty.py`, `scripts/publish_h8_cash_yield.py`. At a later Git head, use `scripts/replay_h8_cash_yield.py`: immutable producer commit identities are preserved and replay compares numerical fields/source hashes separately. Rate acquisition is `scripts/acquire_h8_cash_rates.py`; existing source pointers are checked and reused. Original SPY/vendor-price inputs and accepted raw ALFRED ZIP/form/member evidence remain local; new numerical tables and sanitized manifests are committed. No substitute data are silently generated when originals are missing.\n\n'
    text+='Full tables: [nominal attribution](tables/h8_cash_yield/nominal_attribution.csv), [log/CAGR allocation](tables/h8_cash_yield/attribution.csv), [income intervals](tables/h8_cash_yield/cash_income_uncertainty.csv), [complete annual credits](tables/h8_cash_yield/annual_cash_credit.csv), [all fixed periods](tables/h8_cash_yield/periods.csv). Full pytest, compileall, diff checks, original-source preservation and deterministic replay are recorded in the execution manifest. These validate implementation, not independent coauthor acceptance.\n\n'+provenance
    (DOC/'h8_economic_attribution.md').write_text(text,encoding='utf-8',newline='\n')
    files={(TABLE/(n+'.csv')).relative_to(ROOT).as_posix():sha(TABLE/(n+'.csv')) for n in names}
    files.update({p.relative_to(ROOT).as_posix():sha(p) for p in FIG.glob('*')})
    for n in ['h8_cash_yield_sensitivity.md','h8_economic_attribution.md']:files['docs/'+n]=sha(DOC/n)
    publication={'implementation':code,'results_sha256':sha(OUT/'results.json'),'audit_sha256':sha(OUT/'independent_audit.json'),'files_sha256':files}
    persist(OUT/'publication_p3.json',publication);persist(ROOT/'data/manifests/h8_cash_publication_v2p3.json',publication)
    print('Published two reports, full tables and three PNG/PDF figures',flush=True);return publication


if __name__=='__main__':publish()
