"""Fixed severity uncertainty and independent publication/input crosschecks."""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from vrp.quant_failure import ROOT, OUT, load_inputs, partitions, bootstrap_counts, interval
from vrp.quant_extension import checked_hash, sha, persist, csv_immutable, implementation, budget_alerts


def main():
    code=implementation(['scripts/quant_failure_final_checks.py'])
    x=json.loads((OUT/'results.json').read_bytes()); audit=json.loads((OUT/'independent_audit.json').read_bytes())
    h6,panel,meta,spy,source,logs=load_inputs()
    if source!=meta['h8']['source']: raise ValueError('SPY source metadata differs from frozen H8 v2')
    checked_hash(ROOT/source['path'],'25b45ed25d1c6c09d337d277518e9710fbdcbfc62f691d7971231a6a3d7c5b44')
    masks=partitions(panel); counts=bootstrap_counts(len(panel),63); y=h6.y.to_numpy(); rows=[]
    quantities={'mean_ratio':panel.y.to_numpy()/panel.vix.to_numpy(),
                'mean_realized_vol':np.sqrt(panel.y.to_numpy()),'mean_origin_ivol':np.sqrt(panel.vix.to_numpy())}
    for m in 'ABCD':
        for policy,alert in [('original_full_budget',budget_alerts(h6[m].to_numpy())),
                             ('saved_train_quantile',h6[m].to_numpy()>=h6[f'{m}_alert_threshold'].to_numpy())]:
            for g,mask in masks.items():
                for classification,subset in [('false_negative',mask&(y==1)&(~alert)),('true_positive',mask&(y==1)&alert)]:
                    c=counts[:,subset]; denom=c.sum(axis=1)
                    for metric,values in quantities.items():
                        with np.errstate(divide='ignore',invalid='ignore'): draws=(c@values[subset])/denom
                        rows.append({'group':g,'model':m,'policy':policy,'classification':classification,
                                     'n':int(subset.sum()),'metric':metric,
                                     'estimate':float(values[subset].mean()) if subset.any() else None,**interval(draws)})
    # Compensation-check each primary identity again from sanitized scalar records.
    errors=[]
    for row in x['h6']['scores']:
        if row.get('model') is None: continue
        errors += [abs(row['brier']-math.fsum([row['reliability'],-row['resolution'],row['uncertainty'],row['within_bin_residual']])),
                   abs(row['brier']-row['event_contribution']-row['nonevent_contribution'])]
    for row in x['h7']['scores']:
        if row.get('model') is None: continue
        errors += [abs(row['mse']-row['bias_squared']-row['centered_error_variance']),
                   abs(row['mse']-row['calibration_mse']-row['residual_mse']-row['cross_term'])]
    for row in audit['split_bridge']['bridge']:
        keys=['calibration','forecast_residual','constraint','instrument_return_convention',
              'horizon_dynamic_exposure_mean_sample_bridge','implementation_trade_timing_dividend_bridge','transaction_cost_variance_effect']
        errors.append(abs(row['variance_minus_target']-math.fsum(row[k] for k in keys)))
    if max(errors)>1e-12: raise ValueError('Independent sanitized identity check')
    if not all(r['difference']<0 for r in x['h7']['leave_year_out'] if r['baseline']=='trailing' and r['loss']=='qlike'):
        raise ValueError('Publication claim: trailing leave-year-out')
    # Every Markdown table must remain structurally valid.
    links=0; table_rows=0
    import re
    for name in ['h6_failure_analysis.md','h7_failure_analysis.md','h8_failure_analysis.md','quant_failure_mechanisms.md']:
        text=(ROOT/'docs'/name).read_text(encoding='utf-8'); width=None
        for line in text.splitlines():
            if line.startswith('| '):
                w=line.count('|')
                if width is None: width=w
                elif w!=width: raise ValueError('Malformed Markdown table '+name)
                table_rows+=1
            else: width=None
        for dest in re.findall(r'\]\(([^)]+)\)',text):
            if not dest.startswith('http'):
                if not (ROOT/'docs'/dest).exists(): raise ValueError('Broken report link '+dest)
                links+=1
    for name,digest in x['input_sha256'].items(): checked_hash(ROOT/name,digest)
    digest=csv_immutable(OUT/'false_negative_severity_uncertainty.csv',pd.DataFrame(rows))
    result={'implementation':code,'status':'PASSED_INPUT_PUBLICATION_AND_SEVERITY_AUDIT',
            'source_metadata_exactly_matches_v2':True,'max_identity_error':max(errors),
            'markdown_table_rows_checked':table_rows,'local_report_links_checked':links,
            'severity_uncertainty_scope':'Fixed original OOS allocations; budget is not reselected in this conditional severity diagnostic. Full chronology bootstrap then FN/TP subset; block63,1000 draws,seed1729.',
            'severity_uncertainty':rows,'table_sha256':digest}
    persist(OUT/'final_checks.json',result);persist(ROOT/'data/manifests/quant_failure_final_checks_v1.json',result)
    print(result['status'],flush=True)


if __name__=='__main__': main()
