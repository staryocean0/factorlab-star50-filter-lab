from __future__ import annotations
import argparse,importlib.util,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
START='2021-01-01';END='2023-12-31';YEARS=(2021,2022,2023);COSTS=(.5,1.,1.5,2.)
CANDIDATE={'direction':'long','slow30_sign':'positive','net5_sign':'positive','efficiency5_min':.60,'tail2_share_min':.60,'tail1_condition':None,'hold_min':3}

def load_module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def select(events):
 z=events[(events.direction=='up')&(events.slow_aligned==True)&(events.accel_high==True)&(events.efficient_high==True)&np.isfinite(events.signed_3m_bp)].copy()
 z=z.sort_values(['session','onset_row'],kind='stable');rows=[]
 for _,g in z.groupby('session',sort=False):
  nxt=-1
  for _,r in g.iterrows():
   i=int(r.onset_row)
   if i<nxt:continue
   rows.append(r);nxt=i+1+3
 q=pd.DataFrame(rows)
 if len(q):q=q.copy();q['gross_bp']=q.signed_3m_bp
 return q

def metrics(z):
 n=len(z);mean=float(z.gross_bp.mean()) if n else np.nan
 q={'trades':n,'mean_gross_bp':mean,'median_gross_bp':float(z.gross_bp.median()) if n else np.nan,'hit_rate':float((z.gross_bp>0).mean()) if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan}
 for c in COSTS:q[f'mean_net_{c:g}bp_per_leg']=mean-2*c if n else np.nan
 return q

def run(root,out):
 mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','upmech');minute=mech.build_minute(root);events=mech.build_events(minute);sel=select(events)
 annual=pd.DataFrame([{'year':y,**metrics(sel[sel.year==y])} for y in YEARS]);pooled=metrics(sel)
 accept={'pooled_trades_ge_60':bool(pooled['trades']>=60),'each_year_trades_ge_15':bool((annual.trades>=15).all()),'each_year_net1_positive':bool((annual.mean_net_1bp_per_leg>0).all()),'pooled_net1_positive':bool(pooled['mean_net_1bp_per_leg']>0),'pooled_break_even_gt_1bp':bool(pooled['one_way_break_even_bp']>1)};accept['all_primary_pass']=bool(all(accept.values()))
 candidate_bytes=(json.dumps(CANDIDATE,sort_keys=True,separators=(',',':'))+'\n').encode();cand_hash=hashlib.sha256(candidate_bytes).hexdigest()
 meta={'schema':'star50_up_aligned_accel_dev_v6','development_only':True,'validation_queried':False,'blackbox_queried':False,'validation_informed_hypothesis':True,'candidate':CANDIDATE,'candidate_identity_sha256':cand_hash,'acceptance':accept,'pooled':pooled}
 out.mkdir(parents=True,exist_ok=True);sel.to_csv(out/'dev_trades.csv',index=False);annual.to_csv(out/'annual.csv',index=False);pd.DataFrame([pooled]).to_csv(out/'pooled.csv',index=False);(out/'candidate_identity.json').write_bytes(candidate_bytes);(out/'summary.json').write_text(json.dumps(meta,indent=2,default=str)+'\n');print(json.dumps(meta,default=str));print(annual.to_csv(index=False))

def main():
 a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
