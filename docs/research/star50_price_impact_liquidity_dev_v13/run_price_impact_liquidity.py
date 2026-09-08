from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2021-01-01'; END='2023-12-31'; YEARS=(2021,2022,2023)
SYMBOL='000688.SH'; IMPACT_THRESHOLD=1.0
VIEWS=('all','ImpactAmplified','ImpactDamped')


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def build_minute(root:Path)->pd.DataFrame:
    v12=load_module(root/'docs/research/star50_turnover_pressure_dev_v12/run_turnover_pressure.py','v13_v12')
    return v12.build_minute(root)


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
        for i in range(34,len(z)):
            if state[i]!='HighVol' or state[i-1]!='NormalVol': continue
            raw_onsets+=1
            recent_r=r[i-4:i+1]; recent_a=activity[i-4:i+1]
            prior_r=r[i-34:i-4]; prior_a=activity[i-34:i-4]
            if len(recent_r)!=5 or len(prior_r)!=30 or not np.isfinite(recent_r).all() or not np.isfinite(prior_r).all() or not np.isfinite(recent_a).all() or not np.isfinite(prior_a).all(): continue
            recent_amt=float(recent_a.sum()); prior_amt=float(prior_a.sum())
            if recent_amt<=0 or prior_amt<=0: continue
            recent_impact=float(np.abs(recent_r).sum()/recent_amt)
            prior_impact=float(np.abs(prior_r).sum()/prior_amt)
            if not np.isfinite(prior_impact) or prior_impact<=0: continue
            impact_ratio=float(recent_impact/prior_impact)
            net5=float(recent_r.sum()); sign=1 if net5>0 else (-1 if net5<0 else 0)
            if sign==0: continue
            en=i+1; ex=en+3
            if en<next_allowed_entry: continue
            if ex>=len(z) or not valid[en:ex+1].all(): continue
            if not(np.isfinite(opened[en]) and np.isfinite(opened[ex]) and opened[en]>0 and opened[ex]>0): continue
            raw=float(np.log(opened[ex]/opened[en])*1e4)
            impact_state='ImpactAmplified' if impact_ratio>=IMPACT_THRESHOLD else 'ImpactDamped'
            rows.append({'year':int(z.year.iloc[i]),'trading_day':str(z.trading_day.iloc[i]),'session':str(session),'minute':int(z.minute.iloc[i]),
                'impact_ratio':impact_ratio,'impact_state':impact_state,'net5_bp':net5,'recent5_direction':'up' if sign>0 else 'down',
                'future_raw_3m_bp':raw,'continuation_3m_bp':float(sign*raw),'reversal_3m_bp':float(-sign*raw),'abs_3m_displacement_bp':abs(raw)})
            next_allowed_entry=ex
    return pd.DataFrame(rows),raw_onsets


def stats(z:pd.DataFrame)->dict:
    c=pd.to_numeric(z.continuation_3m_bp,errors='coerce').dropna(); r=pd.to_numeric(z.reversal_3m_bp,errors='coerce').dropna(); a=pd.to_numeric(z.abs_3m_displacement_bp,errors='coerce').dropna(); ir=pd.to_numeric(z.impact_ratio,errors='coerce').dropna()
    n=len(c); mc=float(c.mean()) if n else np.nan; mr=float(r.mean()) if n else np.nan
    return {'n':int(n),'mean_impact_ratio':float(ir.mean()) if len(ir) else np.nan,'mean_continuation_3m_bp':mc,'median_continuation_3m_bp':float(c.median()) if n else np.nan,'continuation_hit':float((c>0).mean()) if n else np.nan,
        'continuation_net_1bp_per_leg':mc-2 if n else np.nan,'continuation_one_way_break_even_bp':mc/2 if n else np.nan,
        'mean_reversal_3m_bp':mr,'median_reversal_3m_bp':float(r.median()) if n else np.nan,'reversal_hit':float((r>0).mean()) if n else np.nan,
        'reversal_net_1bp_per_leg':mr-2 if n else np.nan,'reversal_one_way_break_even_bp':mr/2 if n else np.nan,'mean_abs_3m_displacement_bp':float(a.mean()) if len(a) else np.nan}


def run(root:Path,out:Path):
    minute=build_minute(root); events,raw_onsets=build_events(minute); rows=[]; promising=[]
    for view in VIEWS:
        z=events if view=='all' else events[events.impact_state==view]; annual=[]
        for y in YEARS:
            q=stats(z[z.year==y]); annual.append(q); rows.append({'view':view,'year':y,**q})
        rows.append({'view':view,'year':'pooled',**stats(z)})
        a=pd.DataFrame(annual)
        if len(a)==3 and bool((a.n>=15).all()):
            cont=bool((a.continuation_net_1bp_per_leg>0).all()); rev=bool((a.reversal_net_1bp_per_leg>0).all())
            if cont or rev: promising.append({'view':view,'direction':'continuation' if cont else 'reversal'})
    summary={'schema':'star50_price_impact_liquidity_dev_v13','development_only':True,'validation_queried':False,'blackbox_queried':False,'candidate_nominated':False,
        'symbol':SYMBOL,'impact_threshold':IMPACT_THRESHOLD,'views':list(VIEWS),'raw_onset_count':int(raw_onsets),'event_count':int(len(events)),
        'impact_state_counts':{str(k):int(v) for k,v in events.impact_state.value_counts().to_dict().items()},'mechanism_promising_views':promising}
    out.mkdir(parents=True,exist_ok=True); events.to_csv(out/'events.csv',index=False); pd.DataFrame(rows).to_csv(out/'summary.csv',index=False); (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary)); print(pd.DataFrame(rows).to_csv(index=False))


def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',required=True); p.add_argument('--out',required=True); a=p.parse_args(); run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=='__main__': main()
