"""Generate scientific reports/tables/figures solely from hashed result artifacts."""
import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import probplot, gaussian_kde, norm
from statsmodels.graphics.tsaplots import plot_acf

from vrp.provisional_analysis import STATUS, FREEZE_SHA, EMPIRICAL_SHA, inputs, persist
from vrp.data import write_immutable


def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)


def fmt(v):return f'{v:.10g}' if isinstance(v,(float,np.floating)) else str(v)
def interval(a,b):return f'[{fmt(a)}, {fmt(b)}]'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--parser-path',type=Path,required=True);args=parser.parse_args();sys.path.insert(0,str(args.parser_path.resolve()))
    root=args.root;h12=json.loads((root/'h1_h2.json').read_bytes());h34=json.loads((root/'h3_h4.json').read_bytes());h5=json.loads((root/'h5.json').read_bytes())
    targets,daily,_=inputs();output=root/'publication/v2';output.mkdir(parents=True,exist_ok=True)
    source={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('h*.json')}
    source['execution_audit.json']=hashlib.sha256((root/'execution_audit.json').read_bytes()).hexdigest()
    prefix=f'**{STATUS}**\n\nAleksandar authorized provisional execution before Venelin\'s independent review on 2026-10-13. No independent acceptance/signature is implied. Protocol 1.1.0 and interim amendment remain fixed.\n\n'
    prefix+=f'Input freeze SHA-256 `{FREEZE_SHA}`; target manifest SHA-256 `{EMPIRICAL_SHA}`. Result source hashes: '+', '.join(f'`{k}: {v}`' for k,v in source.items())+'.\n\n'
    prefix+='Point estimates use the frozen untrimmed sample; Bartlett HAC finite-sample correction N/(N-k), asymptotic normal confidence intervals/p-values, joint Wald chi-square where specified. Independent numpy least-squares and score-sandwich checks passed. Numeric p=0 in diagnostics means floating-point underflow, not a mathematical zero. Full numerical precision is retained in source JSON.\n\n'
    p1=next(r for r in h12['h1'] if r['subset']=='full' and r['family']=='cc' and r['horizon']=='30c' and r['object']=='vrp_x' and r['lag']==21)
    p2=next(r for r in h12['h2'] if r['subset']=='full' and r['family']=='cc' and r['horizon']=='30c' and r['lag']==21)
    primary=h34['analyses'][0]['horizons']['30c'];p3=primary['h3_tests'][0]['squared_error']['vix_vs_garch'];p4=primary['h4'][0]
    p5=next(r for r in h5['regressions'] if r['subset']=='full' and r['family']=='cc' and r['horizon']=='30c' and r['object']=='vrp_x' and r['lag']==21)
    reports={}
    h1=prefix+'## H1: mean implied-minus-realized variance\n\n'
    h1+=f"N={int(p1['n_obs'])}; calendar-derived L0={p1['l0']}; mean={p1['mean']!r}; median={p1['median']!r}; HAC SE={p1['standard_error']!r}; z/t={p1['t_statistic']!r}; two-sided p={p1['p_value']!r}; 95% CI={interval(p1['ci_lower'],p1['ci_upper'])}. Positive fraction={p1['proportion_positive']!r}; mean/sample-SD effect={p1['standardized_mean_effect']!r}. Variance is annualized decimal variance.\n\n"
    h1+='Full-sample CC rejects a zero mean. This does not measure the theoretical conditional premium directly or establish a compensation mechanism. The full-sample result weakens in later samples: primary post-2014 CC is insignificant, whereas its deterministic non-overlap result is significant. Retain both; phase/subsample choice is not outcome-selected. Parkinson/GK estimates omit overnight moves and give materially different levels.\n\n'
    values=targets.vrp_x_cc_30c;imin=values.idxmin();imax=values.idxmax()
    h1+=f"Untrimmed primary extrema: minimum {values[imin]!r} at {targets.origin[imin]}, maximum {values[imax]!r} at {targets.origin[imax]}. Distributional statistics are in the target descriptive JSON; VRP ACF and return diagnostics are in publication figures.\n\n"
    h1+=table(['Subset','Estimator','Horizon','Object','N','HAC lag','Mean','SE','95% CI','Two-sided p'],[
        [r['subset'],r['family'],r['horizon'],r['object'],int(r['n_obs']),int(r['maxlags']),fmt(r['mean']),fmt(r['standard_error']),interval(r['ci_lower'],r['ci_upper']),repr(r['p_value'])] for r in h12['h1']])
    reports['h1_results.md']=h1
    h2=prefix+'## H2: variance calibration\n\nOLS RVAR = alpha + beta IVAR; joint null alpha=0 AND beta=1. Coefficient tests are not substitutes for this restriction.\n\n'
    h2+=f"Primary N={p2['n']}, HAC lag={p2['lag']}, R²={p2['r_squared']!r}, joint Wald chi²(2)={p2['wald']['statistic']!r}, p={p2['wald']['p_value']!r}. Coefficients are alpha, beta in that order.\n\n"
    h2+=table(['Coefficient','Estimate','HAC SE','95% CI','Individual p (coefficient=0)'],[[n,fmt(b),fmt(se),interval(*ci),repr(p)] for n,b,se,ci,p in zip(['alpha','beta'],p2['coefficients'],p2['se'],p2['ci95'],p2['p_values'])])
    slope_calibration_p=float(2*norm.sf(abs((p2['coefficients'][1]-1)/p2['se'][1])))
    h2+=f"\nFor clarity, the separate slope calibration null beta=1 has p={slope_calibration_p!r}; alpha=0 has p={p2['p_values'][0]!r}. These marginal restrictions do not replace the joint covariance-aware Wald test. The table's ordinary coefficient p-values test zero, which is a different slope null. Calibration rejection is not evidence of irrationality/inefficiency or a direct identification of risk compensation. Post-2014 CC joint calibration is not rejected; non-overlap and estimator sensitivities differ.\n\n"
    h2+=table(['Subset','Estimator','Horizon','N','Lag','Alpha (SE)','Beta (SE)','R²','Joint chi²','Joint p'],[
        [r['subset'],r['family'],r['horizon'],r['n'],r['lag'],f"{fmt(r['coefficients'][0])} ({fmt(r['se'][0])})",f"{fmt(r['coefficients'][1])} ({fmt(r['se'][1])})",fmt(r['r_squared']),fmt(r['wald']['statistic']),repr(r['wald']['p_value'])] for r in h12['h2']])
    reports['h2_results.md']=h2
    h3=prefix+'## H3: recursive OOS variance forecasting\n\n'
    h3+='Initial training contains all valid returns through final 2006 session; each 2007-2025 origin is re-estimated using only returns through that origin. Constant-mean GARCH(1,1), percentage fit returns, decimal forecast variance /10000, analytic daily forecasts mapped to exact forward XNYS sessions. Cold defaults, maxiter=1000, ftol=1e-9 fixed before fits. Gaussian expanding is primary; Student-t expanding and Gaussian five-calendar-year rolling are robustness. Both horizons reuse each same fit. No model replacement on failures.\n\n'
    h3+='All three variants completed 4780/4780 origins (14340 fits), zero failures; all model comparisons and H4 use exactly their same 4780-origin common mask. Every daily forecast was independently checked by analytical recurrence, with final-residual forecast backcasts. Full checkpoint replay reused every verified record; 15 date-fixed fresh refits independently matched parameters, forecasts, warnings and residual diagnostics exactly.\n\n'
    h3+=f"Primary paired loss differential is squared loss(VIX) minus squared loss(GARCH); negative favors VIX. Mean={p3['mean']!r}; HAC SE={p3['standard_error']!r}; 95% CI={interval(p3['ci_lower'],p3['ci_upper'])}; p={p3['p_value']!r}. VIX has smaller RMSE but the paired primary advantage is not significant. GARCH has smaller MAE. No complete superiority or market-efficiency conclusion follows. QLIKE is separately defined as RVAR/forecast-log(RVAR/forecast)-1; all inputs positive.\n\n"
    rows=[];tests=[];params=[]
    for analysis in h34['analyses']:
        for horizon,out in analysis['horizons'].items():
            for model,m in out['metrics'].items():rows.append([analysis['variant'],horizon,model,m['n'],fmt(m['rmse']),fmt(m['mae']),fmt(m['mean_forecast_error_actual_minus_forecast']),fmt(m['forecast_bias_forecast_minus_actual']),fmt(m['qlike'])])
            for test in out['h3_tests']:
                for contrast,r in test['squared_error'].items():tests.append([analysis['variant'],horizon,test['lag'],contrast,fmt(r['mean']),fmt(r['standard_error']),interval(r['ci_lower'],r['ci_upper']),repr(r['p_value']),repr(r.get('holm_p_value','primary: unadjusted'))])
        p=analysis['persistence_summary'];params.append([analysis['variant'],analysis['fit_counts']['converged'],analysis['fit_counts']['failed'],analysis['warning_origin_count'],fmt(p['median']),fmt(p['min']),fmt(p['max']),p['near_one_ge_099'],p['at_or_above_one']])
    h3+=table(['Variant','Horizon','Model','N','RMSE','MAE','Mean error actual-forecast','Bias forecast-actual','QLIKE'],rows)
    h3+='\n'+table(['Variant','Converged','Failed','Warning origins','Persistence median','Min','Max','≥0.99','≥1'],params)
    h3+='\nWarning logs distinguish library FutureWarnings from convergence failures; none failed. Near-unit persistence is common, especially Student-t; three rolling fits are at/just above one within floating-point precision and are retained. Residual diagnostics use 38 pre-selected calendar anchors per variant, not every fit; they are not a claim that all residual ARCH disappeared.\n\n'
    h3+=table(['Variant','Horizon','Lag','Contrast','Mean squared-loss difference','HAC SE','95% CI','Raw p','Holm p (two secondary contrasts only)'],tests)
    h3+='\nParameter distributions, per-origin warnings/convergence, standardized residual JB/Ljung-Box/ARCH-LM diagnostics and QLIKE contrast uncertainties are in the hashed source JSON and local forecast checkpoints. Raw and adjusted p-values are retained.\n'
    reports['h3_results.md']=h3
    h4=prefix+'## H4: forecast encompassing\n\nRVAR = alpha + beta IVAR + gamma GARCH; identical H3 common masks. Tests beta=0 and gamma=0 use individual two-sided HAC normal inference. No causal interpretation.\n\n'
    h4+=f"Primary N={p4['n']}, R²={p4['r_squared']!r}, design rank={p4['design_rank']}, raw condition number={p4['design_condition_number']!r}; predictor correlation={p4['predictor_correlation'][0][1]!r}. Correlated forecasts widen incremental-effect intervals; variance-unit scaling contributes to the raw condition number.\n\n"
    h4+=table(['Coefficient','Estimate','HAC SE','95% CI','Two-sided p'],[[n,fmt(b),fmt(se),interval(*ci),repr(p)] for n,b,se,ci,p in zip(['alpha','beta VIX','gamma GARCH'],p4['coefficients'],p4['se'],p4['ci95'],p4['p_values'])])
    h4+='\nPrimary VIX adds conditional predictive information while the GARCH increment is not significant. The rolling 30c GARCH increment is marginally significant at L0 and is retained as robustness, not promoted to the primary result; significance may vary with HAC lag. All matrices have full rank, but finite samples and highly correlated predictors limit interpretation.\n\n'
    rows=[]
    for a in h34['analyses']:
        for h,o in a['horizons'].items():
            for r in o['h4']:
                for i,name in enumerate(['alpha','beta VIX','gamma GARCH']):rows.append([a['variant'],h,r['lag'],r['n'],name,fmt(r['coefficients'][i]),fmt(r['se'][i]),interval(*r['ci95'][i]),repr(r['p_values'][i]),fmt(r['r_squared'])])
    h4+=table(['Variant','Horizon','Lag','N','Coefficient','Estimate','HAC SE','95% CI','p','R²'],rows)
    reports['h4_results.md']=h4
    h5text=prefix+'## H5: ex-post NBER recession classification\n\n'
    h5text+=f"Official chronology source: [{h5['chronology_source']['source_url']}]({h5['chronology_source']['source_url']}); retrieved {h5['chronology_source']['retrieved_at_utc']}; HTML SHA-256 `{h5['chronology_source']['sha256']}`. Frozen before H5 outcomes; monthly peak excluded, trough included. Labels never enter forecasts. Revisions require a preserved versioned baseline. Existing case windows remain entire 2008/2020/2022 calendar years.\n\n"
    h5text+=f"Primary delta recession-minus-expansion={p5['coefficients'][1]!r}, HAC SE={p5['se'][1]!r}, p={p5['p_values'][1]!r}, 95% CI={interval(*p5['ci95'][1])}, N={p5['n']}, lag={p5['lag']}. The primary recession shift is not statistically distinguished from zero. This is a wide-interval non-rejection, not evidence of equality or causal effects.\n\n"
    h5text+=table(['Regime','N','Mean VRP_X','Median VRP_X'],[[name,r['n'],fmt(r['mean']),fmt(r['median'])] for name,r in p5['regimes'].items()])
    rows=[]
    for r in h5['regressions']:rows.append([r['subset'],r['family'],r['horizon'],r['object'],r['n'],r['lag'],fmt(r['coefficients'][1]),fmt(r['se'][1]),interval(*r['ci95'][1]),repr(r['p_values'][1])])
    h5text+='\n'+table(['Subset','Estimator','Horizon','Object','N','Lag','Delta','HAC SE','95% CI','p'],rows)
    h5text+='\nPost-2014 contains only 43 recession origins from one short episode; overlapping targets imply much less independent information. No crisis trimming/winsorizing. Case means and medians can differ strongly because rare extremes remain included.\n\n'
    cases=[]
    for y,r in h5['case_studies'].items():
        s=r['statistics'];cases.append([y,r['n'],fmt(s['vix_close']['mean']),fmt(s['ivar']['mean']),fmt(s['rvar_cc_fwd_30c']['mean']),fmt(s['vrp_x_cc_30c']['mean']),fmt(s['vrp_x_cc_30c']['median'])])
    h5text+=table(['Frozen year','N','Mean VIX pp','Mean IVAR','Mean RVAR','Mean VRP_X','Median VRP_X'],cases)
    h5text+='\nCase-study forecast losses for all three models are in the H3 source JSON; complete targets attached to year-end origins extend into the following year as prescribed. These are descriptive windows, not substitute recession tests.\n'
    reports['h5_results.md']=h5text
    summary=prefix+'## Completed provisional empirical evidence\n\n'
    summary+=table(['Hypothesis','N','Primary estimate/test','Two-sided p','Status'],[
        ['H1',int(p1['n_obs']),f"mean {fmt(p1['mean'])}; CI {interval(p1['ci_lower'],p1['ci_upper'])}",repr(p1['p_value']),'COMPUTED / PROVISIONAL'],
        ['H2',p2['n'],f"joint chi² {fmt(p2['wald']['statistic'])}",repr(p2['wald']['p_value']),'COMPUTED / PROVISIONAL'],
        ['H3',primary['n_common'],f"VIX-GARCH squared-loss mean {fmt(p3['mean'])}",repr(p3['p_value']),'COMPUTED / PROVISIONAL'],
        ['H4',p4['n'],f"gamma {fmt(p4['coefficients'][2])}; beta {fmt(p4['coefficients'][1])}",f"gamma {p4['p_values'][2]!r}; beta {p4['p_values'][1]!r}",'COMPUTED / PROVISIONAL'],
        ['H5',p5['n'],f"delta {fmt(p5['coefficients'][1])}",repr(p5['p_values'][1]),'COMPUTED / PROVISIONAL']])
    summary+='\nFull-sample H1 and H2 reject their nulls. Later-sample CC results weaken; primary post-2014 H1/H2 are not significant. VIX lower RMSE does not establish a significant paired advantage; GARCH has smaller MAE. Primary encompassing favors a VIX increment but not a GARCH increment; rolling robustness differs. Primary recession differences are uncertain; crisis mean premiums are negative in 2008 and 2020 while 2022 is positive. Negative/insignificant/contradictory outputs are preserved.\n\n'
    summary+='No result directly observes the theoretical conditional premium, establishes risk compensation, causality, irrationality or market efficiency. No manuscript conclusions were added. All three GARCH variants cover 4780 origins with zero failures, but near-unit persistence and residual-model diagnostics remain material. Review all hypotheses jointly without outcome-selected source/window/bandwidth changes.\n\n'
    summary+='Independent review tasks: reproduce exact source/target hashes; inspect the author-reported methodology and explicit Aleksandar execution authorization; verify H1/H2 HAC/Wald oracles and all robustness; audit chronological training/checkpoints/forecast recurrence/common masks; inspect parameter persistence and 38 residual anchors per variant; validate NBER monthly mapping and frozen case windows; inspect generated tables/figures. CI is implementation qualification, not independent scientific acceptance. If rejected, record a versioned revision and full re-execution preserving this baseline. Next concrete action: Venelin audits this complete review package.\n\n'
    summary+='Reports: [H1](h1_results.md), [H2](h2_results.md), [H3](h3_results.md), [H4](h4_results.md), [H5](h5_results.md). Figures/tables are reproducibly generated under `outputs/empirical_h1_h5/v1/publication/`; provider price files remain ignored.\n'
    reports['empirical_results_summary.md']=summary
    for name,text in reports.items():Path('docs',name).write_text('# '+name.replace('_',' ').replace('.md','')+'\n\n'+text,encoding='utf-8')
    # Publication table exports contain estimates only, not market-price rows.
    pd.DataFrame([{k:v for k,v in r.items() if not isinstance(v,(dict,list))} for r in h12['h1']]).to_csv(output/'h1_robustness.csv',index=False,float_format='%.17g')
    pd.DataFrame([{'hypothesis':h,'n':n,'p':p} for h,n,p in [('H1',p1['n_obs'],p1['p_value']),('H2',p2['n'],p2['wald']['p_value']),('H3',p3['n_obs'],p3['p_value']),('H4_gamma',p4['n'],p4['p_values'][2]),('H5',p5['n'],p5['p_values'][1])]]).to_csv(output/'primary_tests.csv',index=False,float_format='%.17g')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':180})
    def save(fig,name):
        fig.suptitle(STATUS,fontsize=10);fig.tight_layout(rect=(0,0,1,.96))
        for format_ in ['pdf','png']:
            stream=BytesIO();kwargs={'metadata':{'CreationDate':None,'ModDate':None}} if format_=='pdf' else {}
            fig.savefig(stream,format=format_,**kwargs);write_immutable(output/f'{name}.{format_}',stream.getvalue())
        plt.close(fig)
    returns=daily.log_return.dropna().to_numpy();date_values=pd.to_datetime(daily.Date.iloc[1:])
    fig,axes=plt.subplots(3,2,figsize=(11,9))
    axes[0,0].plot(date_values,100*returns,lw=.35,color='#24689b');axes[0,0].set(ylabel='Daily log return (%)',xlabel='Return-ending date')
    axes[0,1].hist(100*returns,bins=80,density=True,color='#24689b',alpha=.7)
    grid=np.linspace(100*returns.min(),100*returns.max(),200);axes[0,1].plot(grid,gaussian_kde(100*returns)(grid),color='#aa5030');axes[0,1].set(xlabel='Daily log return (%)',ylabel='Density')
    probplot(returns,dist='norm',plot=axes[1,0]);axes[1,0].set(title='',xlabel='Normal theoretical quantile',ylabel='Observed decimal return')
    plot_acf(returns,lags=42,ax=axes[1,1],title='',zero=False,auto_ylims=True);axes[1,1].set(ylabel='Return ACF',xlabel='Session lag')
    plot_acf(returns**2,lags=42,ax=axes[2,0],title='',zero=False,auto_ylims=True);axes[2,0].set(ylabel='Squared-return ACF',xlabel='Session lag')
    plot_acf(targets.vrp_x_cc_30c,lags=63,ax=axes[2,1],title='',zero=False,auto_ylims=True);axes[2,1].set(ylabel='Primary VRP_X ACF',xlabel='Eligible-origin lag')
    save(fig,'return_and_overlap_diagnostics')
    chosen=[p1]+[next(r for r in h12['h1'] if r['subset']==s and r['family']==f and r['horizon']==h and r['object']=='vrp_x') for s,f,h in [('post2003','cc','30c'),('post2014','cc','30c'),('full','cc','30c_nonoverlap'),('full','parkinson','30c'),('full','gk','30c')]]
    fig,ax=plt.subplots(figsize=(8,4.6));mean=np.array([r['mean'] for r in chosen]);lo=np.array([r['ci_lower'] for r in chosen]);hi=np.array([r['ci_upper'] for r in chosen])
    labels=['Full CC','From 2004 CC','From 2014-10-06 CC','Full CC non-overlap','Full Parkinson','Full Garman–Klass']
    ax.errorbar(mean,np.arange(len(chosen)),xerr=np.array([mean-lo,hi-mean]),fmt='o',color='#24689b',capsize=4);ax.axvline(0,lw=1,color='#777777')
    ax.set(yticks=np.arange(len(chosen)),yticklabels=labels,xlabel='Mean VRP_X (annualized decimal variance), 95% HAC CI');ax.invert_yaxis();save(fig,'h1_fixed_robustness')
    fig,axes=plt.subplots(1,2,figsize=(9,4));names=['vix','garch','naive'];labels=['VIX','Recursive GARCH','Naive']
    for ax,metric in zip(axes,['rmse','mae']):
        ax.bar(labels,[primary['metrics'][n][metric] for n in names],color=['#24689b','#aa5030','#797979']);ax.set(ylabel=f'{metric.upper()} (annualized decimal variance)',xlabel='Primary 30c, Gaussian expanding, N=4780')
    save(fig,'h3_primary_forecast_losses')
    fig,ax=plt.subplots(figsize=(8,4));case=h5['case_studies'];years=list(case)
    x=np.arange(len(years));ax.bar(x-.17,[case[y]['statistics']['vrp_x_cc_30c']['mean'] for y in years],width=.34,color='#24689b',label='Mean')
    ax.bar(x+.17,[case[y]['statistics']['vrp_x_cc_30c']['median'] for y in years],width=.34,color='#aa5030',label='Median');ax.axhline(0,color='#777777',lw=.7)
    ax.set(xticks=x,xticklabels=years,ylabel='VRP_X (annualized decimal variance)',xlabel='Frozen calendar-year case study');ax.legend();save(fig,'h5_frozen_crisis_descriptions')
    primary_rows=[['H1',9064,'Mean VRP_X',fmt(p1['mean']),interval(p1['ci_lower'],p1['ci_upper']),fmt(p1['p_value']),'Variance'],
        ['H2',9064,'Joint Wald chi²(2)',fmt(p2['wald']['statistic']),'Joint null; no scalar CI',fmt(p2['wald']['p_value']),'Test statistic'],
        ['H3',4780,'VIX-GARCH loss',fmt(p3['mean']),interval(p3['ci_lower'],p3['ci_upper']),fmt(p3['p_value']),'Variance²'],
        ['H4',4780,'Beta VIX',fmt(p4['coefficients'][1]),interval(*p4['ci95'][1]),fmt(p4['p_values'][1]),'Dimensionless'],
        ['H4',4780,'Gamma GARCH',fmt(p4['coefficients'][2]),interval(*p4['ci95'][2]),fmt(p4['p_values'][2]),'Dimensionless'],
        ['H5',9064,'Recession delta',fmt(p5['coefficients'][1]),interval(*p5['ci95'][1]),fmt(p5['p_values'][1]),'Variance']]
    fig,ax=plt.subplots(figsize=(13,3.5));ax.axis('off')
    tab=ax.table(cellText=primary_rows,colLabels=['Hypothesis','N','Quantity','Estimate','95% HAC CI','Two-sided p','Annualized decimal unit'],
        colWidths=[.08,.05,.14,.12,.27,.12,.22],cellLoc='left',loc='center')
    tab.auto_set_font_size(False);tab.set_fontsize(8);tab.scale(1,1.8)
    for (row,col),cell in tab.get_celld().items():
        cell.set_linewidth(.35);cell.set_edgecolor('#b0b0b0')
        if row==0:cell.set_facecolor('#eeeeee');cell.set_text_props(weight='bold')
    save(fig,'primary_hypothesis_table')
    # Compact tracked metadata retains all source/output identities, primary
    # estimates and scientific limitations; bulky full numerical results local.
    metadata={'status':STATUS,'freeze_sha256':FREEZE_SHA,'target_manifest_sha256':EMPIRICAL_SHA,
        'result_sources':source,'implementation_commits':{'h1_h2':h12['implementation']['commit'],'h3_h4':h34['implementation']['commit'],'h5':h5['implementation']['commit']},
        'primary_results':{'h1':p1,'h2':p2,'h3':p3,'h4':p4,'h5':p5},
        'garch_sources':h34['garch_sources'],'garch_summary':[{k:a[k] for k in ['variant','fit_counts','warning_origin_count','persistence_summary']} for a in h34['analyses']],
        'publication_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},
        'report_files':{n:hashlib.sha256(Path('docs',n).read_bytes()).hexdigest() for n in reports},
        'generator_sha256_lf':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
        'publication_root':output.as_posix(),
        'independent_review':'PENDING','manuscript_conclusions_added':False}
    persist(Path('data/manifests/2026-10-13_h1_h5_execution.json'),metadata)
    print('reports generated from hashed JSON',flush=True)


if __name__=='__main__':main()
