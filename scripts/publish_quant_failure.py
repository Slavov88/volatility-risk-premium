"""Generate evidence-linked diagnostic reports/tables and deterministic figures."""
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from vrp.quant_failure import OUT, ROOT, load_inputs, partitions
from vrp.quant_extension import sha, persist, implementation

DOC=ROOT/'docs'; FIG=DOC/'figures/quant_failure'; TABLE=DOC/'tables/quant_failure'
STATUS='EXPLORATORY DIAGNOSTICS — PENDING INDEPENDENT COAUTHOR REVIEW'


def fmt(x):
    if x is None: return '—'
    if isinstance(x,(int,np.integer)): return str(x)
    if isinstance(x,(float,np.floating)): return f'{x:.9g}'
    if isinstance(x,(list,dict)): return json.dumps(x,sort_keys=True)
    return str(x).replace('|',' / ')


def table(rows,columns):
    return '\n'+'| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+''.join('| '+' | '.join(fmt(r.get(k)) for k in columns)+' |\n' for r in rows)+'\n'


def one(rows,**criteria):
    return next(r for r in rows if all(r.get(k)==v for k,v in criteria.items()))


def savefig(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight',metadata={'Software':'Matplotlib'})
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
    plt.close(fig)


def publish():
    code=implementation(['scripts/publish_quant_failure.py'])
    x=json.loads((OUT/'results.json').read_bytes()); audit=json.loads((OUT/'independent_audit.json').read_bytes())
    if audit['primary_results_sha256']!=sha(OUT/'results.json'): raise ValueError('Audit parent mismatch')
    h6,panel,meta,spy,_,logs=load_inputs()
    FIG.mkdir(parents=True,exist_ok=True); TABLE.mkdir(parents=True,exist_ok=True)
    for source in OUT.glob('*.csv'):
        # Derived numerical tables only: no vendor prices or raw source rows.
        shutil.copyfile(source,TABLE/source.name)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'ps.fonttype':42,'axes.grid':True,'grid.alpha':.2})
    colors={'A':'#707070','B':'#9467bd','C':'#0072b2','D':'#d55e00',
            'vix':'#0072b2','garch':'#009e73','trailing':'#777777','combined':'#d55e00'}
    # Annual prevalence/prediction drift, all years retained.
    years=list(range(2012,2026)); fig,ax=plt.subplots(figsize=(8,3.6))
    actual=[one(x['h6']['scores'],group=f'year_{y}',model='C')['prevalence'] for y in years]
    ax.plot(years,np.array(actual)*100,'ko-',label='Event prevalence')
    for m in 'ACD':
        p=[one(x['h6']['scores'],group=f'year_{y}',model=m)['mean_probability']*100 for y in years]
        ax.plot(years,p,color=colors[m],label=f'{m} mean probability')
    ax.set(xlabel='Forecast-origin year',ylabel='Probability / prevalence (%)',xticks=years[::2]); ax.legend(ncol=2,fontsize=9)
    savefig(fig,'h6_probability_drift')
    sel=panel.origin.between('2020-01-01','2020-06-30'); dates=pd.to_datetime(panel.origin[sel])
    fig,ax=plt.subplots(figsize=(8,3.6))
    for m in 'ABC': ax.plot(dates,h6.loc[sel,m]*100,color=colors[m],label=f'Model {m}')
    ev=sel&(h6.y==1); ax.scatter(pd.to_datetime(panel.origin[ev]),np.repeat(98,ev.sum()),marker='|',color='black',label='Forward event origins')
    ax.axvline(pd.Timestamp('2020-02-19'),color='grey',ls=':',lw=1);ax.axvline(pd.Timestamp('2020-03-24'),color='grey',ls=':',lw=1)
    ax.set(xlabel='Origin (label matures 30 calendar days later)',ylabel='Predicted probability (%)',ylim=(0,104));ax.legend(ncol=2,fontsize=9)
    fig.autofmt_xdate(); savefig(fig,'h6_2020_chronology')
    fig,ax=plt.subplots(figsize=(8,3.6))
    y=panel.y.to_numpy(); c=panel.combined.to_numpy(); v=panel.vix.to_numpy()
    differential=y/c-np.log(y/c)-1-(y/v-np.log(y/v)-1)
    ax.plot(pd.to_datetime(panel.origin),np.cumsum(differential),color=colors['combined'])
    ax.axhline(0,color='black',lw=.7);ax.set(xlabel='Forecast origin',ylabel='Cumulative QLIKE: combined − VIX')
    savefig(fig,'h7_cumulative_loss')
    fig,ax=plt.subplots(figsize=(8,3.6))
    fits=meta['h7']['fits']; dates=pd.to_datetime([f['as_of'] for f in fits])
    for j,m in enumerate(['vix','garch','trailing']): ax.plot(dates,[f['combined']['raw_coefficients'][j] for f in fits],color=colors[m],label=m)
    ax.set(xlabel='Chronological monthly refit',ylabel='Raw variance coefficient (not convex weight)');ax.legend(ncol=3,fontsize=9)
    savefig(fig,'h7_coefficient_drift')
    r=one(audit['split_bridge']['bridge'],strategy='combined')
    keys=['calibration','forecast_residual','constraint','instrument_return_convention',
          'horizon_dynamic_exposure_mean_sample_bridge','implementation_trade_timing_dividend_bridge','transaction_cost_variance_effect']
    labels=['OOS calibration projection','Forecast residual','100% cap constraint','SPX/SPY & return units',
            'Horizon & changing-exposure bridge','Trade timing / dividend bridge','Gross/net fee effect']
    fig,ax=plt.subplots(figsize=(9,4.2)); vals=np.array([r[k] for k in keys])*10000
    ax.barh(labels,vals,color=['#0072b2' if z<0 else '#d55e00' for z in vals]);ax.invert_yaxis();ax.axvline(0,color='black',lw=.7)
    ax.set(xlabel='Annual variance contribution × 10,000 (additive identity)');savefig(fig,'h8_variance_bridge')
    preamble=f'**{STATUS}**\n\nFixed plan committed as `7ad9187` before computations. Original v2 models, parameters, source data and reported findings remain unchanged. Evaluation: 3520 origins2012–2025,168 monthly refits. All rates are decimals unless marked percent. New diagnostics use full-chronology circular block63 bootstrap,1000 draws,seed1729; fixed blocks21/126 sensitivities are retained. Historical resampling, overlapping labels and sparse stress cells do not establish causality or independent scientific acceptance.\n\n'
    provenance=f'Primary result SHA `{sha(OUT/"results.json")}`; independent audit SHA `{sha(OUT/"independent_audit.json")}`. Full provenance, all input hashes and exact tables are in [results](../data/manifests/quant_failure_results_v1.json) and [audit](../data/manifests/quant_failure_independent_audit_v1.json). Reproduction and interpretation limits: [synthesis](quant_failure_mechanisms.md).\n'
    # H6 exact decomposition and competing explanations.
    scores=x['h6']['scores']; full=[r for r in scores if r['group']=='full']; A=one(full,model='A'); C=one(full,model='C')
    event_gain=C['event_contribution']-A['event_contribution']; nonevent=C['nonevent_contribution']-A['nonevent_contribution']
    live=[r for r in x['h6']['alerts'] if r['group']=='full']; rank=[r for r in audit['score_uncertainty']['ranking'] if r['group']=='full']
    text='# H6 failure analysis\n\n'+preamble
    text+=f'C’s excess Brier loss is exactly {fmt(event_gain)} from event days plus {fmt(nonevent)} from non-event days = {fmt(C["brier"]-A["brier"])}. It improves the event contribution but raises the much more numerous non-event contribution. This supports over-warning / calibration cost under imbalance; it contradicts an explanation that C never learns anything about events. The all-zero probability diagnostic has Brier244/3520 = {fmt(244/3520)}, worse than A and C; prevalence imbalance alone therefore does not explain the advanced model’s excess loss. The hindsight constant prevalence achieves p(1−p), an oracle diagnostic and never an executable replacement.\n'
    text+=table(full,['model','prevalence','mean_probability','brier','event_contribution','nonevent_contribution','reliability','resolution','within_bin_residual'])
    text+='Brier = fixed-bin reliability − resolution + prevalence uncertainty + within-bin residual. Keeping the residual makes the identity exact; reliability cannot be read as the whole loss. All ten bins, including empty bins, are retained. Probability calibration errors here are OOS diagnostics, never probability transformations.\n\n'
    text+=table(rank,['model','metric','estimate','ci95','valid_draws'])
    text+='C’s whole-sample ROC-AUC is approximately chance and AP is close to prevalence. Its stronger ranking than A/B does not establish useful absolute discrimination. Mean probabilities exceed full-sample event rates; period-specific calibration reverses during the shock. Both ranking and calibration fail, with wide dependence-aware intervals.\n\n'
    text+=table(live,['model','policy','alerts','tp','fp','fn','precision','recall','recall_ci_low','recall_ci_high'])
    text+='The retrospective budget selects ceil(.1N) high scores using future evaluation ranks. Subgroup budgets in the complete tables re-rank within that hindsight subgroup and are a different descriptive allocation; the false-negative table also retains the original whole-sample budget. The saved monthly training-90th-percentile rule is executable but uses varying alert fractions. A alerts everywhere because of ties, so its100% recall has no selectivity. No new threshold was introduced. Zero-event group recall retains the original utility’s zero convention; it is undefined for interpretation and its uncertainty is null.\n\n'
    groups=['vix_low','vix_mid','vix_high','shock_down','shock_stable','shock_up','2020_pre','2020_onset','2020_normalize','2020_late']
    text+=table([r for r in scores if r['model']=='C' and r['group'] in groups],['group','n','events','prevalence','prevalence_ci_low','prevalence_ci_high','mean_probability','brier','brier_ci_low','brier_ci_high'])
    text+='Low-IVAR origins have121/1432 events (8.450%), versus19/382 (4.974%) in VIX>=25. This supports selection by the relative-event denominator: high implied risk raises the required realized variance. It does not prove low IVAR causes shocks, and104 events occur at intermediate VIX. Rising VIX origins have39/346 events (11.272%), falling VIX6/191 (3.141%); these are current five-session movements, not future shock predictors. Ratio>3 and realized-volatility false-negative summaries are fully retained in the linked tables.\n\n'
    text+='The2020 pre window contains15 forward events among32 origins; onset contains17/24, while normalization and late2020 contain no events under this ratio definition. Those labels include the NEXT30 days: an origin before Feb19 can contain March stress in its target. This is target chronology, not advance knowledge of a crisis. C’s onset mean probability24.046% substantially undershoots70.833% event prevalence, but its Brier0.507941 beats A0.594255. Saved C alerts catch12/17 onset events (17 alerts) versus7/15 pre events (18 alerts); warnings improve after volatility has risen. Contradicting a blanket shock-failure explanation, C improves2020 loss versus A; the decline in event prevalence during high-IVAR normalization also makes high risk and ratio events different concepts. Tiny overlapping shock groups produce very broad intervals; do not count17 events as17 independent shocks.\n\n'
    coef=x['coefficients']['h6']; drift=[]
    for m in 'BCD':
        for feature in dict.fromkeys(r['feature'] for r in coef if r['model']==m):
            sub=[r for r in coef if r['model']==m and r['feature']==feature]; key='importance' if m=='D' else 'standardized_coefficient'; vals=np.array([r[key] for r in sub])
            drift.append({'model':m,'feature':feature,'min':float(vals.min()),'median':float(np.median(vals)), 'max':float(vals.max()),'first':float(vals[0]),'last':float(vals[-1]),'sign_changes':int(np.sum(np.sign(vals[1:])!=np.sign(vals[:-1])))})
    text+=table(drift,['model','feature','min','median','max','first','last','sign_changes'])
    text+='These are the168 original refits; coefficient ranges are descriptive, not confidence intervals for independent estimates. Standardized coefficients change with training scales; raw coefficients and every scaler/intercept are retained. C’s IVAR coefficient remains negative and GARCH positive, while trailing21 changes sign, supporting changing conditional association and correlated-feature allocation. Stable signs contradict a universal coefficient-instability explanation. No coefficient is changed.\n\n'
    text+='![Annual probability drift](figures/quant_failure/h6_probability_drift.png)\n\nAnnual prevalence and predicted rates; all years shown, association only.\n\n![2020 prediction chronology](figures/quant_failure/h6_2020_chronology.png)\n\nEvent marks denote origins of future30-day outcomes; they are not events known at origin.\n\n'
    text+=table(scores,['group','model','n','events','brier','mean_probability','roc_auc','average_precision'])
    text+='Full uncertainty and false-negative severity: [score table](tables/quant_failure/h6_scores.csv), [alerts](tables/quant_failure/h6_alerts.csv), [severity](tables/quant_failure/h6_false_negatives.csv), [paired losses](tables/quant_failure/h6_contrasts.csv), [reliability bins](tables/quant_failure/h6_bins.csv), [ranking intervals](tables/quant_failure/score_ranking.csv), [calibration intervals](tables/quant_failure/score_calibration.csv).\n\n'+provenance
    (DOC/'h6_failure_analysis.md').write_text(text,encoding='utf-8',newline='\n')
    # H7 all loss dimensions and fixed partitions.
    text='# H7 failure analysis\n\n'+preamble
    text+='The combination improves the weak trailing constituent but supplies no reliable QLIKE improvement over VIX/GARCH. Its lower MAE than VIX coexists with higher RMSE and QLIKE: ordinary absolute errors improve while rare large errors and relative underprediction drive other objectives. This is a loss-function mismatch, not evidence that one metric is intrinsically correct.\n'
    text+=table([r for r in x['h7']['scores'] if r['group']=='full'],['model','mean_target','forecast','bias','bias_ci_low','bias_ci_high','qlike','rmse','mae','intercept','slope','bias_squared','centered_error_variance'])
    text+='MSE=bias²+centered error variance exactly. OOS y=a+b*f+u gives y−f=(a+(b−1)f)+u; calibration MSE, residual MSE and twice their covariance are retained. The OOS projection is a descriptive decomposition using outcomes; its fitted values are never submitted as forecasts. Calibration intervals appear in the complete audit. Most squared loss is centered error, so mean bias alone is insufficient.\n\n'
    text+=table([r for r in x['h7']['contrasts'] if r['group']=='full'],['baseline','loss','difference','ci_low','ci_high'])
    text+='Negative differences favor combination; new intervals are absolute loss differences, whereas original v2 reports also contain relative-reduction intervals. No original inference or Holm family is replaced.\n\n'
    corr=x['h7']['predictor_correlations'];text+=f'Pairwise correlations: IVAR/GARCH {fmt(corr["vix"]["garch"])}, GARCH/trailing {fmt(corr["garch"]["trailing"])}, IVAR/trailing {fmt(corr["vix"]["trailing"])}; standardized predictor condition number {fmt(x["h7"]["standardized_condition_number"])}. This supports overlapping information, but correlation alone cannot identify absence of incremental signal or a causal reason for failure; the trailing comparison shows some useful combination behavior.\n\n'
    coef=x['coefficients']['h7']; drift=[]
    for m in ['combined','har']:
        for feature in dict.fromkeys(r['feature'] for r in coef if r['model']==m):
            sub=[r for r in coef if r['model']==m and r['feature']==feature]; vals=np.array([r['coefficient'] for r in sub]);drift.append({'model':m,'feature':feature,'min':float(vals.min()),'median':float(np.median(vals)),'max':float(vals.max()),'first':float(vals[0]),'last':float(vals[-1])})
    text+=table(drift,['model','feature','min','median','max','first','last'])
    text+='All168 intercepts/scalers and HAR smearing factors are retained. Raw coefficients are not convex weights; their sum need not equal1 and intercept contributions matter. IVAR’s raw coefficient rises0.207835→0.679896, GARCH falls0.528882→0.204844, trailing ends at0. Early coefficients plus shock errors are consistent with too little implied-volatility responsiveness, but no coefficient intervention was tested; changing collinearity, the fitted intercept and outcome unpredictability also explain these associations. Strong historical IVAR calibration does not prove a coefficient of1 would improve the combination.\n\n'
    text+=table([r for r in x['h7']['contrasts'] if r['group'] in groups+['2012_2016','2017_2021','2022_2025'] and r['loss']=='qlike'],['group','baseline','n','difference','ci_low','ci_high'])
    text+='In2020 onset combined-minus-VIX QLIKE is+2.10704, versus−0.808314 against GARCH; it still beats trailing by−1.95456. Falling-VIX origins give+0.0230347 against trailing, contradicting a universal combination improvement. High and low VIX panels both have positive VIX-relative mean loss, but uncertainty spans zero. Pre/onset versus normalization are fixed descriptive calendar windows; their targets overlap across windows and do not isolate independent episodes.\n\n'
    conc=[{k:v for k,v in r.items() if k!='origins'} for r in x['h7']['concentration'] if r['model']=='combined']
    text+=table(conc,['loss','fraction','n','share_of_total_loss'])
    text+='The largest36 combined MSE losses supply82.910% of its squared loss; the largest36 QLIKE losses supply28.097%. This explains sensitivity of RMSE without treating outcome-selected loss ranks as predictors. All constituent concentration summaries and exact contributing origins are retained.\n\n'
    text+=table([r for r in x['h7']['leave_year_out'] if r['baseline']=='vix' and r['loss']=='qlike'],['omitted_year','difference'])
    text+='Leaving2020 out changes VIX-relative QLIKE from+0.00218021 to−0.0180181; leaving2018 out also changes the sign. These are sensitivity calculations on frozen forecasts, not retraining or evidence for deleting crisis years. The trailing-relative mean remains negative in every leave-year-out panel, contradicting a claim that its aggregate benefit depends entirely on one year.\n\n'
    text+='![Cumulative paired loss](figures/quant_failure/h7_cumulative_loss.png)\n\nUpward segments mean greater combined QLIKE loss.\n\n![Original monthly coefficient drift](figures/quant_failure/h7_coefficient_drift.png)\n\nRaw-unit slopes; not portfolio allocation weights.\n\n'
    text+=table(x['h7']['scores'],['group','model','n','qlike','rmse','mae','bias'])
    text+='Full results: [scores and exact decomposition](tables/quant_failure/h7_scores.csv), [all paired contrasts](tables/quant_failure/h7_contrasts.csv), [168 fit coefficients](tables/quant_failure/coefficients_h7.csv), [forecast contribution shares](tables/quant_failure/coefficients_contributions.csv), [concentration](tables/quant_failure/h7_concentration.csv), [all leave-year-out results](tables/quant_failure/h7_leave_year_out.csv), [blocks21/63/126](tables/quant_failure/sensitivities.csv).\n\n'+provenance
    (DOC/'h7_failure_analysis.md').write_text(text,encoding='utf-8',newline='\n')
    # H8 exact identities and limits of attribution.
    text='# H8 failure analysis\n\n'+preamble
    text+='The combined strategy’s8.438% realized volatility is lower than trailing’s10.140%, but its rolling21 target RMSE3.028% is worse than trailing2.960% and GARCH2.685%. Target tracking is distinct from risk reduction. Gross combined CAGR8.230% versus trailing9.999% already shows a return disadvantage; fees are not its sole cause.\n'
    text+=table([r for r in x['h8']['summary'] if r['cost_bps']==5],['strategy','annual_vol','rolling21_target_rmse','cagr','max_drawdown','mean_cash_fraction','cap_fraction_earned','annual_turnover_nav','gross_minus_net_cagr'])
    text+='Saved weights remain clip(.1/sqrt(f),0,1). Of3519 earned combined signals,2.671% have100% equity exposure, compared with31.941% for trailing. Combined keeps34.178% mean cash versus trailing22.595%. The cap DOES prevent the ex-ante forecast-implied10% target when f<.01: w²f=min(f,.01). It is not a bound on future realized volatility: a surprise can still yield much higher realized risk. The constraint reduces combined mean proxy variance by0.0000222402, only about0.772% of its absolute full-sample net variance gap0.00287939. For trailing the term is−0.00111577 yet aggregate volatility slightly exceeds target, contradicting cap binding as a sufficient explanation of aggregate undershooting. Low-VIX cap fractions/shortfalls and uncertainty are retained for every strategy.\n\n'
    text+='For each origin, **w²y−.01=w²(y−f)+(w²f−.01)**, in annual decimal variance. Split y−f into the descriptive OOS calibration projection and residual. Mean only3519 earned origins; terminal forecast earns no return. Separately use actual next30-calendar-day SPY cash-dividend simple squared returns to identify the SPX/log-versus-SPY/simple instrument convention difference. A saved-weight close-to-close algebraic return proxy then separates horizon/aggregation/changing-exposure differences from actual old-share overnight versus new-share intraday timing. This proxy is never run as an alternative strategy. Every covariance and denominator effect is retained; the horizon bridge remains unexplained economically.\n\n'
    text+=table(audit['split_bridge']['bridge'],['strategy','variance_minus_target','calibration','forecast_residual','constraint','instrument_return_convention','horizon_dynamic_exposure_mean_sample_bridge','implementation_trade_timing_dividend_bridge','transaction_cost_variance_effect','arithmetic_residual'])
    text+='These terms add exactly to net sample annual variance minus.01. Calibration and forecasting residual are a projection-dependent allocation, not independent causal effects. The combined largest term is the horizon/dynamic-exposure bridge−0.00202096; instrument convention is−0.0000932212, timing/dividend bridge+0.0000635053 and fee variance effect+0.000000792230. The cap is a small contributor. No unique explanation for the largest bridge is identified: averaging forward overlapping30-day variance at origin weights differs from full-sample variance under changing next-open exposures and rolling21 tracking. Labeling that whole bridge “model error” would be false precision. Arithmetic residual zero does not imply no scientifically unexplained difference.\n\n'
    text+='Independently reconstructed daily return = [old shares × (open−previous close) + old shares × dividend + new shares × (close−open) − fee] / previous NAV. First row starts in cash at open; final row has overnight only. Every one of25 ledgers passes share/cash/cost/return recurrence and covariance accounting. Full symmetric covariance tables sum to portfolio variance; diagonal component variances alone would omit cross terms.\n\n'
    text+=table(audit['portfolio_uncertainty']['paired_combined_minus_trailing'],['block','metric','estimate','ci95','valid_draws'])
    text+='Across all three fixed block lengths the risk-error difference remains uncertain and CAGR disadvantage intervals stay negative. Group volatility/exposure/cap intervals resample full chronology before selecting memberships. Group rolling intervals resample the original complete-window losses; the full paired intervals recompute rolling windows on resampled returns. Neither estimates independent crisis replication.\n\n'
    regimes=[r for r in x['h8']['regimes'] if r['group'] in ['vix_low','vix_mid','vix_high','shock_down','shock_stable','shock_up','2020_pre','2020_onset','2020_normalize','2020_late']]
    text+=table(regimes,['group','strategy','n','mean_weight','cap_fraction','annual_vol','rolling_target_rmse','variance_contribution','total_log_return','turnover_sum'])
    text+='Regimes are indexed by signal origin, with their realized next-open ledger row. Variance contributions are sums of (r−full mean)²×252/(N−1); the disjoint VIX and shock-direction families each sum exactly to full-sample variance. Calendar windows/outcome groups overlap and must not be summed together. Annual volatility within a group is not its contribution to full variance. Fragmented subgroup log returns and drawdowns are descriptive stitched observations, not an executable strategy. Rising-VIX and normalization panels expose changing weights and foregone equity returns; low cash-weight exposure both protects drawdowns and sacrifices upside. The2022 fixed panel shows why reduced exposure can help in a falling market, contradicting a universal economic inefficiency claim.\n\n'
    text+=table(x['h8']['summary'],['strategy','cost_bps','annual_vol','rolling21_target_rmse','cagr','max_drawdown','annual_turnover_nav','cost_initial_nav','gross_minus_net_total_log_return','gross_minus_net_cagr'])
    text+='Fees are cost-rate × traded notional, never cost-rate × NAV. Exact gross/net compounded log-return drag is sum log(1+r_gross)−sum log(1+r_net); it includes compounding and self-financing wealth effects. Total fee dollars / initial NAV is a different quantity. No dividends, costs, leverage constraints, parameters or cash-interest assumptions changed. Fractional shares, next-open fills, zero cash interest, ex-date rather than pay-date dividend cash and lack of independent SPY provider confirmation limit external validity.\n\n'
    text+='![Combined annual variance bridge](figures/quant_failure/h8_variance_bridge.png)\n\nAdditive accounting identity, not causal attribution; the largest horizon/changing-exposure term remains economically unresolved.\n\n'
    text+='Full tables: [all regimes](tables/quant_failure/h8_regimes.csv), [variance covariances](tables/quant_failure/h8_variance_components.csv), [daily return components](tables/quant_failure/h8_daily_components.csv), [split bridge](tables/quant_failure/split_bridge.csv), [bridge daily proxies](tables/quant_failure/split_daily_bridge.csv), [group uncertainties](tables/quant_failure/portfolio_groups.csv).\n\n'+provenance
    (DOC/'h8_failure_analysis.md').write_text(text,encoding='utf-8',newline='\n')
    # Synthesis: no causal claim; exactly one future hypothesis, not executed.
    text='# Quantitative failure mechanisms\n\n'+preamble
    text+='The results support specific diagnostic associations, not a causal explanation of sophisticated-model failure. H6’s event-loss gain is outweighed by extra non-event probability loss; its near-chance ranking limits calibration-only remedies. H7’s highly correlated predictors and changing coefficients coincide with episode-dependent incremental loss; better MAE does not imply better tail-sensitive variance scoring. H8’s combined cap term is too small to explain its risk undershoot; the main unresolved difference connects the forward variance objective to realized risk under changing exposures. No existing practical gate changes and no new hypothesis was executed.\n\n'
    explanations=[
        {'explanation':'H6 non-event calibration cost under imbalance','support':'C−A event contribution −0.00178893, non-event +0.00428618; mean probability9.427% vs prevalence6.932%','contrary':'C improves onset Brier vs A and event-day loss; zero predictor is worse','status':'Exact loss identity, descriptive explanation; not class imbalance alone'},
        {'explanation':'H6 poor ranking / temporal prevalence drift','support':'C ROC0.5084; low-IVAR event prevalence8.450%; sharp2020 forward event cluster','contrary':'Saved C threshold catches12/17 onset events; large uncertainty and overlapping targets','status':'Association, no demonstrated useful tail-warning mechanism'},
        {'explanation':'H7 redundant predictors / coefficient allocation','support':'GARCH/trailing correlation0.9258; IVAR slope0.2078→0.6799; onset VIX loss +2.1070','contrary':'Combination beats trailing in every leave-year-out mean; no weight intervention tested','status':'Consistent with limited increment, not causal identification'},
        {'explanation':'H7 rare-episode / scoring sensitivity','support':'Top1% MSE share82.910%; excluding2020 flips VIX QLIKE comparison','contrary':'Trailing gain is not dependent solely on2020; full VIX comparison uncertain','status':'Verified sensitivity; exclusions are not proposed improvements'},
        {'explanation':'H8 cap causes aggregate undershoot','support':'Binding forecast state forces w²f<.01; combined cap fraction2.671%','contrary':'Constraint only0.772% of combined gap; trailing often capped yet reaches10.14%','status':'Local algebra true; principal aggregate explanation rejected'},
        {'explanation':'H8 fee drag causes failure','support':'Combined5bps CAGR drag0.2908pp and higher turnover than trailing','contrary':'Gross CAGR disadvantage1.7690pp; risk-error difference remains uncertain','status':'Contributes to returns, cannot explain whole failure'},
        {'explanation':'H8 forecast-to-exposure objective mismatch','support':'Combined horizon/changing-exposure bridge−0.00202096 dominates its variance gap','contrary':'Bridge mixes overlap, horizon, means and exposures; GARCH tracks better without a new objective','status':'Testable question, economically unresolved mechanism'}]
    text+=table(explanations,['explanation','support','contrary','status'])
    text+='One future hypothesis is justified as a question about the decision layer, not a discovered remedy: **matching the forecast’s instrument and horizon to executable SPY21-session risk improves risk targeting beyond the current GARCH and trailing strategies without material return sacrifice.** Candidate to preregister before any future outcome: monthly expanding nonnegative ridge(alpha1, unpenalized intercept, nonnegative slope, floor1e−8) mapping the unchanged combination forecast to next21-observed-session SPY cash-dividend simple-return variance annualized252; scale feature using matured training only, minimum500 labels, no parameter search. Target maturity requires all21 actual returns observed; forecasts need no future closure knowledge. Translate this one forecast using the unchanged10%/100%-cap next-open policy at5bps. This is a proposed future experiment only; no such forecast, mapping or portfolio is calculated here.\n\n'
    text+='Baselines: unchanged combined, GARCH and trailing policies on identical prospective dates. Success must reduce rolling21 tracking RMSE by >=0.005 annual volatility versus BOTH GARCH and trailing and lose <=0.005 CAGR versus each, with paired block63 intervals supporting the directions; preserve gross and1/10/25bps sensitivities. Freeze source/implementation/calibration rule and independent review before collecting evaluation data. Evaluate once after504 matured prospective origins strictly after that future registration; an independent coauthor holds the evaluation outcomes. No interim tuning/stopping, no historical crisis deletion, no retroactive confirmatory label. Pre-existing warm-up may be used for the frozen mapping but never for choosing coefficients/criteria after prospective inspection. The bridge is not causal proof and may reflect unavoidable dynamic exposure rather than a remediable mismatch, so failure is a plausible outcome. No future H6 hypothesis is promoted: the present discrimination evidence is too weak to support a practically useful calibration-only claim.\n\n'
    text+='Reports: [H6](h6_failure_analysis.md), [H7](h7_failure_analysis.md), [H8](h8_failure_analysis.md). Plan: [fixed registration](../paper/quant_failure_diagnostic_plan.md). Original [v2 synthesis](quant_extension_summary.md) and [Task1 correction](h3_h4_calendar_correction.md) remain immutable.\n\n'
    text+='Reproduce from this checkout and the pinned local source artifacts with `.venv/Scripts/python.exe scripts/run_quant_failure.py`, then `scripts/run_quant_failure_audit.py`, then `scripts/publish_quant_failure.py`. Producers require committed source. Immutable result replay at a later Git head uses `scripts/replay_quant_failure.py` to compare numerical content and original source hashes while preserving the producer commit. Exact Python/package versions are captured in the execution manifest. Missing original artifacts cause failure, not synthetic data substitution; provider-price files remain excluded from Git.\n\n'
    text+='Verification: independent compensated-sum Brier/QLIKE/RMSE checks, tie-aware ROC/AP against sklearn, moment-versus-linear-system calibration, raw coefficient replay, every25-ledger share/cash return and covariance identity, preserved inputs before/after computations, deterministic numerical and publication replay, adversarial boundaries/terminal/cap/dividend/fee tests and full pytest/compileall/diff-check. These qualify the implementation; independent coauthor acceptance remains pending. The full execution manifest records actual final check results.\n\n'+provenance
    (DOC/'quant_failure_mechanisms.md').write_text(text,encoding='utf-8',newline='\n')
    files={p.relative_to(ROOT).as_posix():sha(p) for folder in [FIG,TABLE] for p in sorted(folder.glob('*'))}
    for name in ['h6_failure_analysis.md','h7_failure_analysis.md','h8_failure_analysis.md','quant_failure_mechanisms.md']: files['docs/'+name]=sha(DOC/name)
    publication={'implementation':code,'results_sha256':sha(OUT/'results.json'),'audit_sha256':sha(OUT/'independent_audit.json'),'files_sha256':files}
    persist(OUT/'publication.json',publication);persist(ROOT/'data/manifests/quant_failure_publication_v1.json',publication)
    print('Published reports, tables and five PNG/PDF figures',flush=True)
    return publication


if __name__=='__main__': publish()
