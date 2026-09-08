from __future__ import annotations
import argparse,importlib.util,itertools,json
from pathlib import Path
import numpy as np,pandas as pd
YEARS=(2021,2022,2023)

def load_module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def nonoverlap(z,hold=3):
 rows=[]
 for _,g in z.sort_values(['session','onset_row'],kind='stable').groupby('session',sort=False):
  nxt=-1
  for _,r in g.iterrows():
   i=int(r.onset_row)
   if i<nxt:continue
   rows.append(r);nxt=i+1+hold
 return pd.DataFrame(rows).reset_index(drop=True) if rows else z.iloc[:0].copy()

def stats(z):
 q=pd.to_numeric(z.signed_3m_bp,errors='coerce').dropna();n=len(q);m=float(q.mean()) if n else np.nan
 return {'trades':int(n),'mean_gross_bp':m,'median_gross_bp':float(q.median()) if n else np.nan,'hit_rate':float((q>0).mean()) if n else np.nan,'mean_net_1bp_per_leg':m-2 if n else np.nan,'one_way_break_even_bp':m/2 if n else np.nan}

def evaluate(events,direction,slow,accel,eff):
 z=events[(events.direction==direction)&(events.slow_aligned==slow)&(events.accel_high==accel)&(events.efficient_high==eff)&np.isfinite(events.signed_3m_bp)].copy();z=nonoverlap(z,3)
 annual=pd.DataFrame([{'year':y,**stats(z[z.year==y])} for y in YEARS]);p=stats(z)
 g={'pooled_trades_ge_60':bool(p['trades']>=60),'each_year_trades_ge_15':bool((annual.trades>=15).all()),'each_year_net1_positive':bool((annual.mean_net_1bp_per_leg>0).all()),'pooled_net1_positive':bool(p['mean_net_1bp_per_leg']>0),'pooled_break_even_gt_1bp':bool(p['one_way_break_even_bp']>1)};g['all_primary_pass']=bool(all(g.values()))
 return z,annual,p,g

def run(root,out):
 mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','cube_mech');events=mech.build_events(mech.build_minute(root));rows=[];trade_rows=[];passes=[]
 for direction,slow,accel,eff in itertools.product(('down','up'),(False,True),(False,True),(False,True)):
  z,a,p,g=evaluate(events,direction,slow,accel,eff);cell=f'{direction}|slow={slow}|accel={accel}|eff={eff}'
  rows.append({'cell':cell,'year':'pooled',**p,**{f'gate_{k}':v for k,v in g.items()}})
  for r in a.to_dict(orient='records'):rows.append({'cell':cell,**r})
  if g['all_primary_pass']:passes.append(cell)
  if len(z):
   q=z.copy();q['cell']=cell;trade_rows.append(q)
 meta={'schema':'star50_fixed_cube_falsification_dev_v7','development_only':True,'validation_queried':False,'blackbox_queried':False,'cell_count':16,'passing_cells':passes,'any_stable_cell':bool(passes),'interpretation':'passing cells are hypotheses only; no automatic candidate promotion'}
 out.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(out/'cell_summary.csv',index=False);pd.concat(trade_rows,ignore_index=True).to_csv(out/'cell_trades.csv',index=False) if trade_rows else None;(out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta));print(pd.DataFrame(rows)[lambda x:x.year.astype(str)=='pooled'].to_csv(index=False))

def main():
 a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
