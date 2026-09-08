from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2021-01-01'; END='2023-12-31'; YEARS=(2021,2022,2023)
SYMBOL='000688.SH'; ACTIVITY_FIELD='amount'
VIEWS=('all','TurnoverSupported','TurnoverOpposed')


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def build_minute(root:Path)->pd.DataFrame:
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','v12reg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','v12orig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','v12fg')
    native=orig.load_native(root,SYMBOL).copy()
    native['trading_day']=native.trading_day.astype(str).str[:10]
    native=native[native.trading_day<=END].copy()
    if ACTIVITY_FIELD not in native.columns: raise KeyError(ACTIVITY_FIELD)
    state=reg.build_continuous_state(native,SYMBOL)
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),SYMBOL).reset_index(drop=True)
    a=native[['trading_day','ts',ACTIVITY_FIELD]].copy().rename(columns={'ts':'timestamp',ACTIVITY_FIELD:'activity'})
    a['activity']=pd.to_numeric(a.activity,errors='coerce')
    minute=minute.merge(a,on=['trading_day','timestamp'],how='left',sort=False,validate='one_to_one')
    minute.loc[~minute.valid.astype(bool),'activity']=np.nan
    minute.loc[~(np.isfinite(minute.activity)&(minute.activity>0)),'activity']=np.nan
    minute['trading_day']=minute.trading_day.astype(str).str[:10]
    return minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)


def build_events(minute:pd.DataFrame)->tuple[pd.DataFrame,int]:
    rows=[]; raw_onsets=0
    for session,z0 in minute.groupby('session',sort=False):
        z=z0.sort_values('minute').reset_index(drop=True)
        state=z.route_state.to_numpy(object); close=z.close.to_numpy(float); opened=z.open.to_numpy(float)
        activity=z.activity.to_numpy(float); valid=z.valid.to_numpy(bool)
        r=np.full(len(z),np.nan)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(close[i]) and np.isfinite(close[i-1]) and close[i]>0 and close[i-1]>0:
                r[i]=np.log(close[i]/close[i-1])*1e4
        next_allowed_entry=0
        for i in range(4,len(z)):
            if state[i]!='HighVol' or state[i-1]!='NormalVol': continue
            raw_onsets+=1
            rr=r[i-4:i+1]; aa=activity[i-4:i+1]
            if len(rr)!=5 or len(aa)!=5 or not np.isfinite(rr).all() or not np.isfinite(aa).all(): continue
            net5=float(rr.sum()); denom=float(aa.sum())
            if denom<=0: continue
            pressure=float(np.sum(rr*aa)/denom)
            psign=1 if pressure>0 else (-1 if pressure<0 else 0)
            nsign=1 if net5>0 else (-1 if net5<0 else 0)
            if psign==0 or nsign==0: continue
            en=i+1; ex=en+3
            if en<next_allowed_entry: continue
            if ex>=len(z) or not valid[en:ex+1].all(): continue
            if not(np.isfinite(opened[en]) and np.isfinite(opened[ex]) and opened[en]>0 and opened[ex]>0): continue
            raw=float(np.log(opened[ex]/opened[en])*1e4)
            pressure_state='TurnoverSupported' if psign==nsign else 'TurnoverOpposed'
            rows.append({
                'year':int(z.year.iloc[i]),'trading_day':str(z.trading_day.iloc[i]),'session':str(session),'minute':int(z.minute.iloc[i]),
                'pressure_state':pressure_state,'net5_bp':net5,'turnover_weighted_pressure_bp':pressure,
                'recent5_direction':'up' if nsign>0 else 'down','pressure_direction':'up' if psign>0 else 'down',
                'future_raw_3m_bp':raw,'continuation_3m_bp':float(nsign*raw),'reversal_3m_bp':float(-nsign*raw),
                'abs_3m_displacement_bp':abs(raw),
            })
            next_allowed_entry=ex
    return pd.DataFrame(rows),raw_onsets


def stats(z:pd.DataFrame)->dict:
    c=pd.to_numeric(z.continuation_3m_bp,errors='coerce').dropna(); r=pd.to_numeric(z.reversal_3m_bp,errors='coerce').dropna(); a=pd.to_numeric(z.abs_3m_displacement_bp,errors='coerce').dropna()
    n=len(c); mc=float(c.mean()) if n else np.nan; mr=float(r.mean()) if n else np.nan
    return {'n':int(n),'mean_continuation_3m_bp':mc,'median_continuation_3m_bp':float(c.median()) if n else np.nan,'continuation_hit':float((c>0).mean()) if n else np.nan,
        'continuation_net_1bp_per_leg':mc-2 if n else np.nan,'continuation_one_way_break_even_bp':mc/2 if n else np.nan,
        'mean_reversal_3m_bp':mr,'median_reversal_3m_bp':float(r.median()) if n else np.nan,'reversal_hit':float((r>0).mean()) if n else np.nan,
        'reversal_net_1bp_per_leg':mr-2 if n else np.nan,'reversal_one_way_break_even_bp':mr/2 if n else np.nan,
        'mean_abs_3m_displacement_bp':float(a.mean()) if len(a) else np.nan}


def run(root:Path,out:Path):
    minute=build_minute(root); events,raw_onsets=build_events(minute); rows=[]; promising=[]
    for view in VIEWS:
        z=events if view=='all' else events[events.pressure_state==view]; annual=[]
        for y in YEARS:
            q=stats(z[z.year==y]); annual.append(q); rows.append({'view':view,'year':y,**q})
        rows.append({'view':view,'year':'pooled',**stats(z)})
        a=pd.DataFrame(annual)
        if len(a)==3 and bool((a.n>=15).all()):
            cont=bool((a.continuation_net_1bp_per_leg>0).all()); rev=bool((a.reversal_net_1bp_per_leg>0).all())
            if cont or rev: promising.append({'view':view,'direction':'continuation' if cont else 'reversal'})
    summary={'schema':'star50_turnover_pressure_dev_v12','development_only':True,'validation_queried':False,'blackbox_queried':False,'candidate_nominated':False,
        'symbol':SYMBOL,'activity_field':ACTIVITY_FIELD,'views':list(VIEWS),'raw_onset_count':int(raw_onsets),'event_count':int(len(events)),
        'pressure_state_counts':{str(k):int(v) for k,v in events.pressure_state.value_counts().to_dict().items()},'mechanism_promising_views':promising}
    out.mkdir(parents=True,exist_ok=True); events.to_csv(out/'events.csv',index=False); pd.DataFrame(rows).to_csv(out/'summary.csv',index=False); (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary)); print(pd.DataFrame(rows).to_csv(index=False))


def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',required=True); p.add_argument('--out',required=True); a=p.parse_args(); run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=='__main__': main()
