from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2021-01-01'; END='2023-12-31'; YEARS=(2021,2022,2023)
RUN_BANDS=('run_1','run_2_3','run_4_6','run_ge_7')


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def build_minute(root:Path)->pd.DataFrame:
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','exitreg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','exitorig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','exitfg')
    native=orig.load_native(root,'000688.SH').copy()
    native['trading_day']=native.trading_day.astype(str).str[:10]
    native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,'000688.SH')
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000688.SH').reset_index(drop=True)
    return minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)


def run_band(n:int)->str:
    if n==1:return 'run_1'
    if 2<=n<=3:return 'run_2_3'
    if 4<=n<=6:return 'run_4_6'
    return 'run_ge_7'


def build_exits(minute:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for session,z0 in minute.groupby('session',sort=False):
        z=z0.sort_values('minute').reset_index(drop=True)
        state=z.route_state.to_numpy(object); c=z.close.to_numpy(float); op=z.open.to_numpy(float); valid=z.valid.to_numpy(bool)
        r=np.full(len(z),np.nan)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(c[i]) and np.isfinite(c[i-1]) and c[i]>0 and c[i-1]>0:
                r[i]=np.log(c[i]/c[i-1])*1e4
        for i in range(4,len(z)):
            if state[i]!='NormalVol' or state[i-1]!='HighVol':continue
            k=i-1; run=0
            while k>=0 and state[k]=='HighVol':
                run+=1; k-=1
            recent=r[i-4:i+1]
            if len(recent)!=5 or not np.isfinite(recent).all():continue
            net5=float(recent.sum())
            sign=1 if net5>0 else (-1 if net5<0 else 0)
            if sign==0:continue
            en=i+1; ex=en+3
            if ex>=len(z) or not valid[en:ex+1].all():continue
            if not(np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en]>0 and op[ex]>0):continue
            raw=float(np.log(op[ex]/op[en])*1e4)
            rows.append({
                'year':int(z.year.iloc[0]),'trading_day':str(z.trading_day.iloc[0]),'session':str(session),
                'exit_minute':int(z.minute.iloc[i]),'run_length':int(run),'run_band':run_band(run),
                'net5_bp':net5,'net5_direction':'up' if sign>0 else 'down',
                'continuation_3m_bp':float(sign*raw),'reversal_3m_bp':float(-sign*raw),
                'abs_3m_displacement_bp':abs(raw),
                'exit_vol_ratio':float(z.recovery_ratio.iloc[i]) if np.isfinite(z.recovery_ratio.iloc[i]) else np.nan,
            })
    return pd.DataFrame(rows)


def stats(z:pd.DataFrame)->dict:
    c=pd.to_numeric(z.continuation_3m_bp,errors='coerce').dropna()
    r=pd.to_numeric(z.reversal_3m_bp,errors='coerce').dropna()
    a=pd.to_numeric(z.abs_3m_displacement_bp,errors='coerce').dropna()
    n=len(r); mr=float(r.mean()) if n else np.nan
    return {
        'n':int(n),
        'mean_continuation_3m_bp':float(c.mean()) if len(c) else np.nan,
        'median_continuation_3m_bp':float(c.median()) if len(c) else np.nan,
        'mean_reversal_3m_bp':mr,
        'median_reversal_3m_bp':float(r.median()) if n else np.nan,
        'reversal_hit':float((r>0).mean()) if n else np.nan,
        'reversal_net_1bp_per_leg':mr-2 if n else np.nan,
        'reversal_one_way_break_even_bp':mr/2 if n else np.nan,
        'mean_abs_3m_displacement_bp':float(a.mean()) if len(a) else np.nan,
    }


def run(root:Path,out:Path):
    minute=build_minute(root); events=build_exits(minute)
    views=[('all_exits',events)]+[(b,events[events.run_band==b]) for b in RUN_BANDS]
    rows=[]; promising=[]
    for name,z in views:
        annual=[]
        for y in YEARS:
            q=stats(z[z.year==y]); annual.append(q)
            rows.append({'view':name,'year':y,**q})
        rows.append({'view':name,'year':'pooled',**stats(z)})
        a=pd.DataFrame(annual)
        if len(a)==3 and bool((a.n>=15).all() and (a.reversal_net_1bp_per_leg>0).all()):
            promising.append(name)
    meta={
        'schema':'star50_highvol_exit_reversal_dev_v9','development_only':True,
        'validation_queried':False,'blackbox_queried':False,'candidate_nominated':False,
        'run_bands':list(RUN_BANDS),'event_count':int(len(events)),
        'mechanism_promising_views':promising,
    }
    out.mkdir(parents=True,exist_ok=True)
    events.to_csv(out/'exit_events.csv',index=False)
    pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
    (out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta))
    print(pd.DataFrame(rows).to_csv(index=False))


def main():
    a=argparse.ArgumentParser(); a.add_argument('--repo-root',required=True); a.add_argument('--out',required=True)
    x=a.parse_args(); run(Path(x.repo_root).resolve(),Path(x.out))

if __name__=='__main__':main()
