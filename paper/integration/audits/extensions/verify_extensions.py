"""Replay supplementary identities from tracked Git blobs; no vendor files required."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import platform
import statistics
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

# Commits specify the source trees even when this file is run on an integration branch.
EXT = "2ac49b69d56db939d051849c6dbaf1c9eaa4ec12"
FAIL = "956a9d8aa9ebc05c55e71241aeffbc11d80e2a7e"
CASH = "0910d8e26355832bdbd63abbc10a65a70bbc4d77"
NDX = "27735e5653b5b778fb0e23ccc3e9079d4bdd6aa3"
checked = {}


def blob(commit, path, expected=None):
    b = subprocess.check_output(["git", "show", f"{commit}:{path}"])
    digest = hashlib.sha256(b).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError(f"Hash mismatch at {commit}:{path}")
    checked[f"{commit}:{path}"] = digest
    return b


def manifest(commit, name, expect=None):
    return json.loads(blob(commit, f"data/manifests/{name}.json", expect))


def rows(b):
    return list(csv.DictReader(io.StringIO(b.decode())))


def equal(a, b):
    if not math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError(f"Identity failed ({a} vs {b})")


def main():
    execution = manifest(EXT, "quant_extension_execution_v2")
    h6, h7, h8 = [manifest(EXT, f"quant_extension_{name}_v2", execution["result_sha256"][name])
                  for name in ("h6", "h7", "h8")]
    failure = manifest(FAIL, "quant_failure_results_v1",
                       "165ee888a84dd8df8a406490ac81b67667eee7906e0cb98c4c579cd6672ac80d")
    cash = manifest(CASH, "h8_cash_results_v2",
                    "849296a15472fb8f4902d275807c66f8b58af49de4cf5d182baec8da4ab884fd")
    ndx = manifest(NDX, "cross_market_execution_v1")
    for path, checksum in ndx['input_manifests'].items():
        blob(NDX, path, checksum)
    component = "data/manifests/h8_ledger_component_attribution_v1.json"
    blob(NDX, component, ndx["results"][component]["sha256"])
    # Source checks on executable producers, independent of the integration checkout.
    for result in (h6, h7, h8, failure, cash):
        impl = result["implementation"]
        for path, checksum in impl["sources_sha256_lf"].items():
            raw = blob(impl["commit"], path)
            if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != checksum:
                raise ValueError(f"Producer mismatch at {path}")

    def table(name):
        return rows(blob(FAIL, f"docs/tables/quant_failure/{name}.csv", failure['table_sha256'][name+'.csv']))

    equal(h6['n'], h7['n'])
    if h6['common_origin_sha256'] != h7['common_origin_sha256']:
        raise ValueError("Unequal H6/H7 evaluation masks")
    brier = {}
    for row in table('h6_scores'):
        if row['group'] == 'full':
            k = row['model']
            loss = float(row['event_contribution']) + float(row['nonevent_contribution'])
            equal(loss, h6['models'][k]['brier'])
            equal(float(row['events']) / float(row['n']), h6['prevalence'])
            brier[k] = loss

    qlike = {r['model']:float(r['qlike']) for r in table('h7_scores') if r['group']=='full'}
    for c in h7['comparisons']:
        equal(qlike[c['candidate']] - qlike[c['baseline']], c['hac63']['mean'])
    returns = defaultdict(list)
    for row in table('h8_daily_components'):
        r = math.fsum(float(row[k]) for k in ('overnight','dividend','intraday','negative_cost'))
        returns[row['strategy']].append((date.fromisoformat(row['Date']),r))
    portfolios = {}
    for k, series in sorted(returns.items()):
        dates, r = zip(*series)
        if sorted(set(dates)) != list(dates) or len(r) != h8['n_signals']:
            raise ValueError(f"Invalid dates in {k} components")
        years = (dates[-1]-dates[0]).days/365.25
        terminal = math.exp(math.fsum(math.log1p(x) for x in r))
        cagr = math.expm1(math.log(terminal)/years)
        vol = statistics.stdev(r)*math.sqrt(252)
        rmse = math.sqrt(statistics.mean((statistics.stdev(r[i-20:i+1])*math.sqrt(252)-.10)**2
                                         for i in range(20,len(r))))
        metrics = dict(terminal_nav=terminal,cagr=cagr,annual_vol=vol,rolling21_target_rmse=rmse)
        for key, value in metrics.items():
            equal(value,h8['models']['5'][k][key])
        portfolios[k] = metrics
    rates = {}
    for scenario in ['zero','dgs1mo_full']:
        rates[scenario] = {r['strategy']:r['cagr'] for r in cash['summary']
                           if r['scenario']==scenario and r['cost_bps']==5}
    for k in rates['zero']:
        equal(rates['zero'][k],portfolios[k]['cagr'])
    if sorted(rates['zero'],key=rates['zero'].get) != sorted(rates['dgs1mo_full'],key=rates['dgs1mo_full'].get):
        raise ValueError("Cash CAGR ordering changed")
    print(json.dumps(dict(scope='Committed-summary and daily-component replay, excluding raw refits',
                          python=platform.python_version(),hashes=checked,n=h7['n'],events=h6['events'],
                          h6_brier=brier,h7_qlike=qlike,h8_zero_five_bps=portfolios,
                          h8_cash_cagr=rates,
                          nasdaq_untracked_results=[p for p in ndx['results'] if p.startswith('outputs/')]),
                     indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
