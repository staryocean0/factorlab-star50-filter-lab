"""Isolated ledger correction: matching states are at anchor minute minus two.

Identified during execution before reviewing market results. The frozen V2
forecast estimators/labels/scores are untouched; original ledger remains intact.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import seconds_v2 as v


def lagged_anchor_table(f, symbol):
    q=f.copy()
    cols=['log_rv30','log_rv480']
    q[cols]=q.groupby('session',sort=False)[cols].shift(2)
    a=v.anchor_table(q,symbol)
    a['matching_state_minute']=a.minute-2
    a['matching_state_lag_minutes']=2
    return a


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();root=args.root.resolve();out=args.out.resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError('immutable outputs')
    out.mkdir(parents=True,exist_ok=True)
    v.validate_inputs(root,out)
    import sys
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    minute={}
    for s in v.SYMBOLS:
        x=load_market_data(s,'1m','2021-01-01','2025-12-31',root=root)
        minute[s]=v.g.minute_panel(x,s)
    common=set(minute[v.SYMBOLS[0]].session)&set(minute[v.SYMBOLS[1]].session)
    for s in v.SYMBOLS:minute[s]=minute[s][minute[s].session.isin(common)].reset_index(drop=True)
    if not minute[v.SYMBOLS[0]][['session','minute']].equals(minute[v.SYMBOLS[1]][['session','minute']]):
        raise ValueError('unpaired minute grids')
    joint=np.isfinite(minute[v.SYMBOLS[0]].return_bp)&np.isfinite(minute[v.SYMBOLS[1]].return_bp)
    receipts=[]
    for s in v.SYMBOLS:
        minute[s].loc[~joint,'return_bp']=np.nan
        f=v.aligned_targets(v.g.make_features(minute[s]))
        old=v.anchor_table(f,s);a=lagged_anchor_table(f,s)
        a.to_csv(out/f'{s}_anchors_lag2.csv',index=False)
        changes=old[['anchor_id','session']].merge(a[['anchor_id','session']],on='anchor_id',suffixes=('_old','_new'))
        summary=[];paths=[];source=[]
        for year in range(2021,2026):
            raw,audit=v.read_seconds(root,s,year);source.append(audit)
            groups={name:z for name,z in raw.groupby('session',sort=False)}
            for session,anchors in a[a.year==year].groupby('session',sort=False):
                z=groups.get(session)
                if z is None:t=np.array([]);price=np.array([]);row=np.array([],int)
                else:t=z.second.to_numpy(float);price=z.price.to_numpy(float);row=z.row_index.to_numpy()
                for anchor in anchors.to_dict('records'):
                    desc,path=v.path_summary(t,price,row,anchor);summary.append(desc);paths.append(path)
            print('LEDGER_LAG2',s,year,flush=True)
        pd.DataFrame(summary).to_csv(out/f'{s}_path_ledger_lag2.csv',index=False)
        pd.concat(paths,ignore_index=True).to_csv(out/f'{s}_paths_lag2.csv.gz',index=False,
                    compression={'method':'gzip','mtime':0})
        receipts.append({'symbol':s,'anchors':len(a),'events':int((a.kind=='event').sum()),
             'controls':int((a.kind=='control').sum()),
             'changed_control_sessions':int((changes.session_old!=changes.session_new).sum()),'source':source})
    v.write_json(out/'ledger_correction_receipt.json',{'status':'completed descriptive ledger lag correction',
        'execution_location':'GitHub Actions','run_id':os.getenv('GITHUB_RUN_ID'),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'fixed_forecast_code_sha256':hashlib.sha256(Path(v.__file__).read_bytes()).hexdigest(),
        'matching_state':'anchor minus2 minutes, before earliest event-minute onset',
        'forecast_refit':False,'old_outputs_overwritten':False,'results':receipts,
        'fresh_oos':False,'production_authority':False})


if __name__=='__main__':main()
