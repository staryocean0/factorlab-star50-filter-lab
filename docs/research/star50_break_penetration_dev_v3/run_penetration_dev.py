from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2021-01-01'; END='2023-12-31'; YEARS=(2021,2022,2023)
BINS=(-np.inf,0.25,0.50,1.00,2.00,np.inf)
LABELS=('lt_0.25','0.25_0.50','0.50_1.00','1.00_2.00','ge_2.00')
THRESHOLDS=(0.50,1.00,2.00)


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def base_events(root:Path)->pd.DataFrame:
    mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','pen_mech')
    minute=mech.build_minute(root)
    e=mech.build_events(minute).copy()
    m=(e.direction.eq('down') & (~e.slow_aligned.astype(bool)) & e.efficient_high.astype(bool)
       & np.isfinite(e.signed_3m_bp) & (e.slow30_net_bp>0) & (e.net5_bp<0))
    e=e.loc[m].copy()
    e['break_penetration']=(-e.net5_bp/e.slow30_net_bp).astype(float)
    e['penetration_band']=pd.cut(e.break_penetration,bins=BINS,labels=LABELS,right=False)
    e['v2_tail2_ge50']=e.tail2_share.ge(0.50)
    return e.reset_index(drop=True)


def nonoverlap(e:pd.DataFrame,hold:int=3)->pd.DataFrame:
    if e.empty:return e.copy()
    z=e.sort_values(['session','onset_row'],kind='stable')
    rows=[]
    for _,g in z.groupby('session',sort=False):
        nxt=-1
        for _,r in g.iterrows():
            i=int(r.onset_row)
            if i<nxt:continue
            rows.append(r); nxt=i+1+hold
    return pd.DataFrame(rows).reset_index(drop=True)


def stats(z:pd.DataFrame)->dict:
    q=pd.to_numeric(z.signed_3m_bp,errors='coerce').dropna()
    n=len(q); mean=float(q.mean()) if n else np.nan
    return {
        'trades':int(n),
        'mean_gross_bp':mean,
        'median_gross_bp':float(q.median()) if n else np.nan,
        'hit_rate':float((q>0).mean()) if n else np.nan,
        'mean_net_1bp_per_leg':mean-2.0 if n else np.nan,
        'one_way_break_even_bp':mean/2.0 if n else np.nan,
    }


def rows_for_view(e:pd.DataFrame,view:str)->list[dict]:
    out=[]
    for band in LABELS:
        z=e[e.penetration_band.astype(str)==band]
        out.append({'view':view,'subset':band,'year':'pooled',**stats(z)})
        for y in YEARS:out.append({'view':view,'subset':band,'year':y,**stats(z[z.year==y])})
    for t in THRESHOLDS:
        name=f'ge_{t:g}'
        z=e[e.break_penetration>=t]
        out.append({'view':view,'subset':name,'year':'pooled',**stats(z)})
        for y in YEARS:out.append({'view':view,'subset':name,'year':y,**stats(z[z.year==y])})
    # Secondary cross-tab only; old tail2 rule is not part of the new base.
    for flag in (False,True):
        z=e[e.v2_tail2_ge50.eq(flag)]
        out.append({'view':view,'subset':f'v2_tail2_ge50={flag}','year':'pooled',**stats(z)})
        for y in YEARS:out.append({'view':view,'subset':f'v2_tail2_ge50={flag}','year':y,**stats(z[z.year==y])})
    return out


def gate_for_threshold(e_nonoverlap:pd.DataFrame,t:float)->dict:
    z=e_nonoverlap[e_nonoverlap.break_penetration>=t]
    annual=pd.DataFrame([{'year':y,**stats(z[z.year==y])} for y in YEARS])
    p=stats(z)
    gate={
      'pooled_trades_ge_60':bool(p['trades']>=60),
      'each_year_trades_ge_15':bool((annual.trades>=15).all()),
      'each_year_net1_positive':bool((annual.mean_net_1bp_per_leg>0).all()),
      'pooled_net1_positive':bool(p['mean_net_1bp_per_leg']>0),
      'pooled_break_even_gt_1bp':bool(p['one_way_break_even_bp']>1),
    }
    gate['all_primary_pass']=bool(all(gate.values()))
    return {'threshold':t,'annual':annual.to_dict(orient='records'),'pooled':p,'acceptance':gate}


def run(root:Path,out:Path):
    e=base_events(root); n=nonoverlap(e,3)
    summary=pd.DataFrame(rows_for_view(e,'all_events')+rows_for_view(n,'nonoverlap_3m'))
    gates=[gate_for_threshold(n,t) for t in THRESHOLDS]
    passing=[g for g in gates if g['acceptance']['all_primary_pass']]
    nomination=None
    if passing:
        # Prefer the least restrictive natural threshold that passes; no score ranking.
        nomination=float(sorted(passing,key=lambda x:x['threshold'])[0]['threshold'])
    meta={
      'schema':'star50_break_penetration_dev_v3',
      'development_start':START,'development_end':END,'development_only':True,
      'validation_queried':False,'blackbox_queried':False,
      'base':{'direction':'down','slow30_sign':'positive','net5_sign':'negative','efficiency5_min':0.60},
      'penetration_definition':'-net5_bp/slow30_net_bp',
      'natural_thresholds':list(THRESHOLDS),
      'candidate_nominated':nomination is not None,
      'nominated_threshold':nomination,
      'threshold_gates':gates,
      'base_event_count':int(len(e)),'nonoverlap_event_count':int(len(n)),
    }
    out.mkdir(parents=True,exist_ok=True)
    e.to_csv(out/'base_events.csv',index=False)
    n.to_csv(out/'nonoverlap_events.csv',index=False)
    summary.to_csv(out/'summary.csv',index=False)
    (out/'summary.json').write_text(json.dumps(meta,indent=2,default=str)+'\n')
    print(json.dumps(meta,default=str))
    print(summary[(summary.view=='nonoverlap_3m') & summary.subset.str.startswith('ge_')].to_csv(index=False))


def main():
    a=argparse.ArgumentParser(); a.add_argument('--repo-root',required=True); a.add_argument('--out',required=True)
    x=a.parse_args(); run(Path(x.repo_root).resolve(),Path(x.out))

if __name__=='__main__':main()
