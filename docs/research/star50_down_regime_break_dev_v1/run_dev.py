from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

START='2021-01-01';END='2023-12-31';YEARS=(2021,2022,2023);COSTS=(.5,1.,1.5,2.)

def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def select(events):
    z=events[(events.direction=='down')&(events.slow_aligned==False)&(events.accel_high==False)&(events.efficient_high==True)&np.isfinite(events.signed_5m_bp)].copy()
    z=z.sort_values(['session','onset_row'])
    rows=[]
    for session,g in z.groupby('session',sort=False):
        nxt=-1
        for _,r in g.iterrows():
            i=int(r.onset_row)
            if i<nxt:continue
            rows.append(r);nxt=i+1+5
    q=pd.DataFrame(rows)
    if len(q):q=q.copy();q['gross_bp']=q.signed_5m_bp
    return q

def metrics(z):
    n=len(z);mean=float(z.gross_bp.mean()) if n else np.nan
    q={'trades':n,'mean_gross_bp':mean,'hit_rate':float((z.gross_bp>0).mean()) if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan}
    for c in COSTS:q[f'mean_net_{c:g}bp_per_leg']=mean-2*c if n else np.nan
    return q

def run(root,out):
    mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','rbmech')
    minute=mech.build_minute(root);events=mech.build_events(minute);sel=select(events)
    annual=[]
    for y in YEARS:annual.append({'year':y,**metrics(sel[sel.year==y])})
    annual=pd.DataFrame(annual);pooled=metrics(sel)
    accept={
      'pooled_trades_ge_60':bool(pooled['trades']>=60),
      'each_year_trades_ge_15':bool((annual.trades>=15).all()),
      'each_year_net1_positive':bool((annual['mean_net_1bp_per_leg']>0).all()),
      'pooled_net1_positive':bool(pooled['mean_net_1bp_per_leg']>0),
      'pooled_break_even_gt_1bp':bool(pooled['one_way_break_even_bp']>1),
    };accept['all_primary_pass']=bool(all(accept.values()))
    out.mkdir(parents=True,exist_ok=True);sel.to_csv(out/'dev_trades.csv',index=False);annual.to_csv(out/'annual.csv',index=False);pd.DataFrame([pooled]).to_csv(out/'pooled.csv',index=False)
    meta={'schema':'star50_down_regime_break_dev_v1','development_only':True,'validation_queried':False,'blackbox_queried':False,
          'candidate':{'direction':'short','slow30_sign':'positive','net5_sign':'negative','efficiency5_min':.60,'tail2_share_max_exclusive':.60,'hold_min':5},
          'acceptance':accept,'pooled':pooled}
    (out/'summary.json').write_text(json.dumps(meta,indent=2,default=str)+'\n');print(json.dumps(meta,default=str))

def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
