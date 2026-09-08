from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
import numpy as np,pandas as pd
START='2021-01-01';END='2023-12-31';YEARS=(2021,2022,2023);Z_THRESHOLDS=(1.0,1.5,2.0,3.0)

def load_module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def build_base(root):
 mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','zmech');minute=mech.build_minute(root);e=mech.build_events(minute).copy()
 e=e[e.direction.eq('down') & (~e.slow_aligned.astype(bool)) & e.efficient_high.astype(bool) & np.isfinite(e.signed_3m_bp) & (e.slow30_net_bp>0) & (e.net5_bp<0)].copy()
 sess={k:z.sort_values('minute').reset_index(drop=True) for k,z in minute.groupby('session',sort=False)};zs=[]
 for r in e.itertuples(index=False):
  z=sess[str(r.session)];i=int(r.onset_row);c=z.close.to_numpy(float);valid=z.valid.to_numpy(bool);rr=np.full(len(z),np.nan)
  for j in range(1,len(z)):
   if valid[j] and valid[j-1] and np.isfinite(c[j]) and np.isfinite(c[j-1]) and c[j]>0 and c[j-1]>0:rr[j]=np.log(c[j]/c[j-1])*1e4
  a=rr[i-34:i-4];bg=float(np.sqrt(np.mean(a*a))) if len(a)==30 and np.isfinite(a).all() else np.nan
  zs.append(float(-r.net5_bp/(bg*np.sqrt(5))) if np.isfinite(bg) and bg>0 else np.nan)
 e['directional_shock_z']=zs;return e[np.isfinite(e.directional_shock_z)].reset_index(drop=True)

def nonoverlap(e,hold=3):
 rows=[]
 for _,g in e.sort_values(['session','onset_row']).groupby('session',sort=False):
  nxt=-1
  for _,r in g.iterrows():
   i=int(r.onset_row)
   if i<nxt:continue
   rows.append(r);nxt=i+1+hold
 return pd.DataFrame(rows).reset_index(drop=True) if rows else e.iloc[:0].copy()

def stats(z):
 q=pd.to_numeric(z.signed_3m_bp,errors='coerce').dropna();n=len(q);mean=float(q.mean()) if n else np.nan
 return {'trades':int(n),'mean_gross_bp':mean,'median_gross_bp':float(q.median()) if n else np.nan,'hit_rate':float((q>0).mean()) if n else np.nan,'mean_net_1bp_per_leg':mean-2 if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan}

def gate(n,t):
 z=n[n.directional_shock_z>=t];a=pd.DataFrame([{'year':y,**stats(z[z.year==y])} for y in YEARS]);p=stats(z);g={'pooled_trades_ge_60':p['trades']>=60,'each_year_trades_ge_15':bool((a.trades>=15).all()),'each_year_net1_positive':bool((a.mean_net_1bp_per_leg>0).all()),'pooled_net1_positive':p['mean_net_1bp_per_leg']>0,'pooled_break_even_gt_1bp':p['one_way_break_even_bp']>1};g['all_primary_pass']=bool(all(g.values()));return {'threshold':t,'annual':a.to_dict(orient='records'),'pooled':p,'acceptance':g}

def run(root,out):
 e=build_base(root);n=nonoverlap(e);gates=[gate(n,t) for t in Z_THRESHOLDS];passing=[g for g in gates if g['acceptance']['all_primary_pass']];nom=min([g['threshold'] for g in passing]) if passing else None
 rows=[]
 for t in Z_THRESHOLDS:
  z=n[n.directional_shock_z>=t]
  for y in ('pooled',*YEARS):rows.append({'feature':'directional_shock_z','subset':f'ge_{t:g}','year':y,**stats(z if y=='pooled' else z[z.year==y])})
 for lab,mask in [('vol_ratio_lt2',n.vol_ratio<2),('vol_ratio_2_3',(n.vol_ratio>=2)&(n.vol_ratio<3)),('vol_ratio_ge3',n.vol_ratio>=3)]:
  z=n[mask]
  for y in ('pooled',*YEARS):rows.append({'feature':'vol_ratio','subset':lab,'year':y,**stats(z if y=='pooled' else z[z.year==y])})
 meta={'schema':'star50_directional_shock_strength_dev_v5','development_only':True,'validation_queried':False,'blackbox_queried':False,'z_thresholds':list(Z_THRESHOLDS),'candidate_nominated':nom is not None,'nominated_z_threshold':nom,'base_event_count':len(e),'nonoverlap_event_count':len(n),'threshold_gates':gates}
 out.mkdir(parents=True,exist_ok=True);e.to_csv(out/'base_events.csv',index=False);n.to_csv(out/'nonoverlap_events.csv',index=False);pd.DataFrame(rows).to_csv(out/'summary.csv',index=False);(out/'summary.json').write_text(json.dumps(meta,indent=2,default=str)+'\n');print(json.dumps(meta,default=str));print(pd.DataFrame(rows)[lambda x:x.feature=='directional_shock_z'].to_csv(index=False))

def main():
 a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
