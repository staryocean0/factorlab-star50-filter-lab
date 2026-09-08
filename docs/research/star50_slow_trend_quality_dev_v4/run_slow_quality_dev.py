from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2021-01-01'; END='2023-12-31'; YEARS=(2021,2022,2023)
EFF_BINS=(-np.inf,0.20,0.40,0.60,np.inf)
EFF_LABELS=('eff_lt_0.20','eff_0.20_0.40','eff_0.40_0.60','eff_ge_0.60')
UP_BINS=(-np.inf,0.55,0.60,0.65,np.inf)
UP_LABELS=('up_lt_0.55','up_0.55_0.60','up_0.60_0.65','up_ge_0.65')
EFF_THRESHOLDS=(0.20,0.40,0.60)


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def build_base(root:Path)->pd.DataFrame:
    mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','slowq_mech')
    minute=mech.build_minute(root)
    e=mech.build_events(minute).copy()
    m=(e.direction.eq('down') & (~e.slow_aligned.astype(bool)) & e.efficient_high.astype(bool)
       & np.isfinite(e.signed_3m_bp) & (e.slow30_net_bp>0) & (e.net5_bp<0))
    e=e.loc[m].copy()
    sess={k:z.sort_values('minute').reset_index(drop=True) for k,z in minute.groupby('session',sort=False)}
    eff=[]; up=[]
    for r in e.itertuples(index=False):
        z=sess[str(r.session)]; i=int(r.onset_row)
        c=z.close.to_numpy(float); valid=z.valid.to_numpy(bool)
        rr=np.full(len(z),np.nan)
        for j in range(1,len(z)):
            if valid[j] and valid[j-1] and np.isfinite(c[j]) and np.isfinite(c[j-1]) and c[j]>0 and c[j-1]>0:
                rr[j]=np.log(c[j]/c[j-1])*1e4
        a=rr[i-34:i-4]
        if len(a)!=30 or not np.isfinite(a).all():
            eff.append(np.nan); up.append(np.nan); continue
        tv=float(np.abs(a).sum()); net=float(a.sum())
        eff.append(net/tv if tv>0 else np.nan)
        up.append(float((a>0).mean()))
    e['slow30_efficiency']=eff; e['slow30_up_share']=up
    e=e[np.isfinite(e.slow30_efficiency)&np.isfinite(e.slow30_up_share)].copy()
    e['eff_band']=pd.cut(e.slow30_efficiency,bins=EFF_BINS,labels=EFF_LABELS,right=False)
    e['up_band']=pd.cut(e.slow30_up_share,bins=UP_BINS,labels=UP_LABELS,right=False)
    return e.reset_index(drop=True)


def nonoverlap(e:pd.DataFrame,hold:int=3)->pd.DataFrame:
    if e.empty:return e.copy()
    z=e.sort_values(['session','onset_row'],kind='stable'); rows=[]
    for _,g in z.groupby('session',sort=False):
        nxt=-1
        for _,r in g.iterrows():
            i=int(r.onset_row)
            if i<nxt:continue
            rows.append(r); nxt=i+1+hold
    return pd.DataFrame(rows).reset_index(drop=True)


def stats(z:pd.DataFrame)->dict:
    q=pd.to_numeric(z.signed_3m_bp,errors='coerce').dropna(); n=len(q); mean=float(q.mean()) if n else np.nan
    return {'trades':int(n),'mean_gross_bp':mean,'median_gross_bp':float(q.median()) if n else np.nan,
            'hit_rate':float((q>0).mean()) if n else np.nan,
            'mean_net_1bp_per_leg':mean-2 if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan}


def summarize(n:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for col,labels in [('eff_band',EFF_LABELS),('up_band',UP_LABELS)]:
        for lab in labels:
            z=n[n[col].astype(str)==lab]
            for y in ('pooled',*YEARS):
                q=z if y=='pooled' else z[z.year==y]
                rows.append({'feature':col,'subset':lab,'year':y,**stats(q)})
    for t in EFF_THRESHOLDS:
        z=n[n.slow30_efficiency>=t]
        for y in ('pooled',*YEARS):
            q=z if y=='pooled' else z[z.year==y]
            rows.append({'feature':'eff_threshold','subset':f'eff_ge_{t:g}','year':y,**stats(q)})
    return pd.DataFrame(rows)


def gate(n:pd.DataFrame,t:float)->dict:
    z=n[n.slow30_efficiency>=t]
    annual=pd.DataFrame([{'year':y,**stats(z[z.year==y])} for y in YEARS]); p=stats(z)
    a={'pooled_trades_ge_60':bool(p['trades']>=60),'each_year_trades_ge_15':bool((annual.trades>=15).all()),
       'each_year_net1_positive':bool((annual.mean_net_1bp_per_leg>0).all()),'pooled_net1_positive':bool(p['mean_net_1bp_per_leg']>0),
       'pooled_break_even_gt_1bp':bool(p['one_way_break_even_bp']>1)}
    a['all_primary_pass']=bool(all(a.values()))
    return {'threshold':t,'annual':annual.to_dict(orient='records'),'pooled':p,'acceptance':a}


def run(root:Path,out:Path):
    e=build_base(root); n=nonoverlap(e,3); s=summarize(n); gates=[gate(n,t) for t in EFF_THRESHOLDS]
    passing=[g for g in gates if g['acceptance']['all_primary_pass']]
    nomination=float(sorted(passing,key=lambda x:x['threshold'])[0]['threshold']) if passing else None
    meta={'schema':'star50_slow_trend_quality_dev_v4','development_only':True,'validation_queried':False,'blackbox_queried':False,
          'development_start':START,'development_end':END,
          'base':{'direction':'down','slow30_sign':'positive','net5_sign':'negative','efficiency5_min':0.60},
          'efficiency_thresholds':list(EFF_THRESHOLDS),'candidate_nominated':nomination is not None,'nominated_efficiency_threshold':nomination,
          'base_event_count':int(len(e)),'nonoverlap_event_count':int(len(n)),'threshold_gates':gates}
    out.mkdir(parents=True,exist_ok=True);e.to_csv(out/'base_events.csv',index=False);n.to_csv(out/'nonoverlap_events.csv',index=False);s.to_csv(out/'summary.csv',index=False)
    (out/'summary.json').write_text(json.dumps(meta,indent=2,default=str)+'\n')
    print(json.dumps(meta,default=str))
    print(s[(s.feature=='eff_threshold')].to_csv(index=False))


def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))

if __name__=='__main__':main()
