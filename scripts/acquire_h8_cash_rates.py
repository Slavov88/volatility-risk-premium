"""Freeze public FRED histories and ALFRED initial-release observations."""
from datetime import datetime, timezone
from io import BytesIO, StringIO
import json
import re
import zipfile
import requests
import pandas as pd
from bs4 import BeautifulSoup
from vrp.quant_extension import ROOT, sha, persist, implementation, checked_hash, csv_immutable
from vrp.data import write_immutable


def request(session,url,directory,name,method='GET',data=None):
    r=session.request(method,url,data=data,timeout=90)
    r.raise_for_status()
    path=directory/name;write_immutable(path,r.content)
    return r,{'url':url,'method':method,'parameters':data,'status':r.status_code,
              'retrieved_utc':datetime.now(timezone.utc).isoformat(),'bytes':len(r.content),
              'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),
              'content_type':r.headers.get('Content-Type'),'tls':'normal certificate validation'}


def acquire():
    pointer=ROOT/'data/manifests/h8_cash_rate_source_v1.json'
    if pointer.exists():
        meta=json.loads(pointer.read_bytes())
        for record in meta['downloads']: checked_hash(ROOT/record['path'],record['sha256'])
        print('Reused immutable cash-rate source',flush=True);return meta
    code=implementation(['scripts/acquire_h8_cash_rates.py','paper/h8_cash_yield_plan.md'])
    directory=ROOT/'data/raw'/datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')/'h8_cash_rates'
    directory.mkdir(parents=True,exist_ok=True); session=requests.Session(); downloads=[]; series={}
    for identifier in ['DGS1MO','DTB4WK','DTB3','SOFR']:
        url=f'https://alfred.stlouisfed.org/series/downloaddata?seid={identifier}'
        response,record=request(session,url,directory,identifier+'_download_form.html');downloads.append(record)
        soup=BeautifulSoup(response.text,'html.parser')
        start=soup.select_one('#form_obs_start_date')['value']; end=soup.select_one('#form_obs_end_date')['value']
        series[identifier]={'coverage_start_from_provider_form':start,'coverage_end_from_provider_form':end}
        response,record=request(session,f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={identifier}&cosd=2011-12-01&coed=2026-01-02',directory,identifier+'_current.csv')
        downloads.append(record);current=pd.read_csv(StringIO(response.text))
        if current.columns.tolist()!=['observation_date',identifier]: raise ValueError('FRED schema changed')
        finite=current.dropna(subset=[identifier])
        series[identifier].update({'current_path':record['path'],'current_sha256':record['sha256'],
                                  'current_n_finite':len(finite),'current_first':finite.observation_date.iloc[0],
                                  'current_last':finite.observation_date.iloc[-1]})
        if identifier not in ['DGS1MO','DTB4WK']: continue
        vintages=[o['value'] for o in soup.select('#form_selected_vintage_dates option')]
        selected=[v for v in vintages if '2011-11-01'<=v<='2026-01-05']
        if not selected or any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}',v) for v in selected): raise ValueError('Invalid vintage list')
        pieces=[]
        # Provider explicitly limits daily downloads to450 vintage columns.
        for part,offset in enumerate(range(0,len(selected),400)):
            params=[('form[units]','lin'),('form[obs_start_date]','2011-12-01'),
                    ('form[obs_end_date]','2026-01-02'),('form[file_type]','4'),
                    ('form[file_format]','csv'),('form[download_data]','')]
            params += [('form[selected_vintage_dates][]',v) for v in selected[offset:offset+400]]
            response,record=request(session,url,directory,f'{identifier}_initial_{part:02}.zip','POST',params);downloads.append(record)
            if not response.content.startswith(b'PK'): raise ValueError('Expected ALFRED ZIP; no substitution')
            z=zipfile.ZipFile(BytesIO(response.content)); csvnames=[n for n in z.namelist() if n.endswith('.csv')]
            if len(csvnames)!=1:raise ValueError('Unexpected ALFRED archive')
            raw=z.read(csvnames[0]); frame=pd.read_csv(BytesIO(raw))
            if frame.columns.tolist()!=['period_start_date',identifier,'realtime_start_date']: raise ValueError('Initial release schema changed')
            pieces.append(frame)
            for basename,content in [(f'{identifier}_initial_{part:02}.csv',raw),
                                     (f'{identifier}_initial_{part:02}_README.txt',z.read('README.txt'))]:
                p=directory/basename;write_immutable(p,content)
                downloads.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'parent_zip_sha256':record['sha256']})
            print(identifier,'vintage chunk',part+1,'accepted',flush=True)
        frame=pd.concat(pieces,ignore_index=True).sort_values('period_start_date').reset_index(drop=True)
        path=directory/(identifier+'_initial.csv');csv_immutable(path,frame)
        downloads.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'derivation':'Concatenate all disjoint initial-release vintage batches; no value modifications.'})
        valid=frame.dropna(subset=[identifier]).copy()
        if len(valid)<3400 or valid.period_start_date.duplicated().any() or not valid.period_start_date.is_monotonic_increasing:
            raise ValueError('Incomplete/disordered initial-release history')
        if (valid.realtime_start_date<valid.period_start_date).any():raise ValueError('Impossible initial-release date')
        if not valid.period_start_date.iloc[0]<='2011-12-15' or valid.period_start_date.iloc[-1]<'2025-12-30': raise ValueError('Missing support')
        matched=valid.merge(current,on=None,left_on='period_start_date',right_on='observation_date',suffixes=('_first','_current'),validate='one_to_one')
        differences=matched.loc[matched[identifier+'_first'].ne(matched[identifier+'_current'])]
        series[identifier].update({'initial_path':path.relative_to(ROOT).as_posix(),'initial_sha256':sha(path),
            'n_vintages':len(selected),'initial_n_finite':len(valid),'initial_first':valid.period_start_date.iloc[0],
            'initial_last':valid.period_start_date.iloc[-1],'n_current_vs_initial_differences':len(differences),
            'differences':json.loads(differences.to_json(orient='records')),
            'release_lag_calendar_days_max':int((pd.to_datetime(valid.realtime_start_date)-pd.to_datetime(valid.period_start_date)).dt.days.max())})
        for vintage in ['2012-01-03','2018-04-05','2020-03-23','2022-11-04','2025-12-31']:
            start=(pd.Timestamp(vintage)-pd.Timedelta(days=20)).strftime('%Y-%m-%d')
            url=f'https://alfred.stlouisfed.org/graph/alfredgraph.csv?id={identifier}&cosd={start}&coed={vintage}&vintage_date={vintage}'
            _,record=request(session,url,directory,identifier+'_vintage_'+vintage+'.csv');downloads.append(record)
        print(identifier,series[identifier],flush=True)
    meta={'implementation':code,'created_utc':datetime.now(timezone.utc).isoformat(),
          'series':series,'downloads':downloads,'directory':directory.relative_to(ROOT).as_posix(),
          'selection':'Initial release only, each actual archived availability date, conservative next-calendar-day usability.',
          'no_invented_rates':True,'no_full_period_sofr_backfill':True}
    persist(directory/'source_manifest.json',meta);persist(pointer,meta)
    print('Frozen cash-rate source SHA '+sha(pointer),flush=True)
    return meta


if __name__=='__main__':acquire()
