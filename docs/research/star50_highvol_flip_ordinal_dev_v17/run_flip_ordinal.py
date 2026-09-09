from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2021-01-01'
END='2023-12-31'
YEARS=(2021,2022,2023)
SYMBOL='000688.SH'
VIEWS=('all','FirstUpToDown','RepeatUpToDown')


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_events(minute:pd.DataFrame)->tuple[pd.DataFrame,int]:
    rows=[]
    raw_up_to_down=0
    for session,z0 in minute.groupby('session',sort=False):
        z=z0.sort_values('minute').reset_index(drop=True)
        state=z.route_state.to_numpy(object)
        close=z.close.to_numpy(float)
        opened=z.open.to_numpy(float)
        valid=z.valid.to_numpy(bool)
        r=np.full(len(z),np.nan)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(close[i]) and np.isfinite(close[i-1]) and close[i]>0 and close[i-1]>0:
                r[i]=np.log(close[i]/close[i-1])*1e4
        net5=np.full(len(z),np.nan)
        for i in range(4,len(z)):
            q=r[i-4:i+1]
            if len(q)==5 and np.isfinite(q).all():
                net5[i]=float(q.sum())
        episode_id=-1
        up_to_down_ordinal=0
        next_entry=0
        for i in range(len(z)):
            if state[i]=='HighVol' and (i==0 or state[i-1]!='HighVol'):
                episode_id+=1
                up_to_down_ordinal=0
            if i<5 or state[i]!='HighVol' or state[i-1]!='HighVol':
                continue
            a=net5[i-1]
            b=net5[i]
            if not(np.isfinite(a) and np.isfinite(b)) or a<=0 or b>=0:
                continue
            raw_up_to_down+=1
            up_to_down_ordinal+=1
            ordinal=up_to_down_ordinal
            en=i+1
            ex=en+3
            if en<next_entry or ex>=len(z) or not valid[en:ex+1].all():
                continue
            if not(np.isfinite(opened[en]) and np.isfinite(opened[ex]) and opened[en]>0 and opened[ex]>0):
                continue
            fut=float(np.log(opened[ex]/opened[en])*1e4)
            rows.append({
                'year':int(z.year.iloc[i]),
                'trading_day':str(z.trading_day.iloc[i]),
                'session':str(session),
                'minute':int(z.minute.iloc[i]),
                'episode_id':int(episode_id),
                'up_to_down_ordinal':int(ordinal),
                'ordinal_state':'FirstUpToDown' if ordinal==1 else 'RepeatUpToDown',
                'old_net5_bp':float(a),
                'new_net5_bp':float(b),
                'future_raw_3m_bp':fut,
                'new_direction_continuation_3m_bp':float(-fut),
                'old_direction_reversal_3m_bp':float(fut),
                'abs_3m_displacement_bp':abs(fut),
            })
            next_entry=ex
    return pd.DataFrame(rows),raw_up_to_down


def run(root:Path,out:Path):
    v15=load_module(root/'docs/research/star50_highvol_sign_flip_dev_v15/run_highvol_sign_flip.py','v17_v15')
    minute=v15.build_minute(root)
    minute['trading_day']=minute.trading_day.astype(str).str[:10]
    minute=minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)
    events,raw=build_events(minute)
    rows=[]
    promising=[]
    for view in VIEWS:
        z=events if view=='all' else events[events.ordinal_state==view]
        annual=[]
        for year in YEARS:
            q=v15.stats(z[z.year==year])
            annual.append(q)
            rows.append({'view':view,'year':year,**q})
        rows.append({'view':view,'year':'pooled',**v15.stats(z)})
        a=pd.DataFrame(annual)
        if len(a)==3 and bool((a.n>=15).all()) and bool((a.mean_continuation_3m_bp>2.0).all()):
            promising.append({'view':view,'direction':'new_down_direction_continuation'})
    summary={
        'schema':'star50_highvol_flip_ordinal_dev_v17',
        'development_only':True,
        'validation_queried':False,
        'blackbox_queried':False,
        'candidate_nominated':False,
        'symbol':SYMBOL,
        'views':list(VIEWS),
        'raw_up_to_down_flip_count':int(raw),
        'event_count':int(len(events)),
        'ordinal_state_counts':{str(k):int(v) for k,v in events.ordinal_state.value_counts().to_dict().items()},
        'mechanism_promising_views':promising
    }
    out.mkdir(parents=True,exist_ok=True)
    events.to_csv(out/'events.csv',index=False)
    pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
    print(pd.DataFrame(rows).to_csv(index=False))
    return summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=='__main__':
    main()
