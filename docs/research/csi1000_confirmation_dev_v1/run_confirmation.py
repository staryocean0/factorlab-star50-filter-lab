from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
import numpy as np,pandas as pd
POLICIES=('immediate','wait1_persist','wait1_persist_positive');YEARS=(2021,2022,2023);END='2023-12-31';HOLD=3

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def base_events(dev,minute):
 e=dev.build_events(minute);return e[(e.slow30_net_bp>0)&(e.tail2_share>=.6)&(e.tail1_share<.6)].copy()

def policy_trades(minute,events,policy):
 rows=[];by={k:v.sort_values('minute').reset_index(drop=True) for k,v in minute.groupby('session',sort=False)}
 for session,g in events.groupby('session',sort=False):
  z=by[session];valid=z.valid.to_numpy(bool);op=z.open.to_numpy(float);cl=z.close.to_numpy(float);st=z.route_state.to_numpy(object);nxt=-1
  for e in g.sort_values('onset_row').itertuples(index=False):
   i=int(e.onset_row)
   if i<nxt:continue
   if policy=='immediate': d=0
   else:
    if i+1>=len(z) or st[i+1]!='HighVol':continue
    if policy=='wait1_persist_positive':
     if not(valid[i] and valid[i+1] and np.isfinite(cl[i]) and np.isfinite(cl[i+1]) and cl[i]>0 and cl[i+1]>0):continue
     if np.log(cl[i+1]/cl[i])<=0:continue
    d=1
   en=i+1+d;ex=en+HOLD
   if ex>=len(z) or not valid[en:ex+1].all() or not(np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en]>0 and op[ex]>0):continue
   gross=float(np.log(op[ex]/op[en])*1e4);rows.append({'policy':policy,'year':int(e.year),'trading_day':e.trading_day,'session':session,'onset_minute':int(e.onset_minute),'gross_bp':gross});nxt=ex
 return pd.DataFrame(rows)

def metrics(z):
 n=len(z);mean=float(z.gross_bp.mean()) if n else np.nan
 return {'trades':n,'mean_gross_bp':mean,'mean_net1_bp':mean-2 if n else np.nan,'hit_rate':float((z.gross_bp>0).mean()) if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan}

def run(root,out):
 dev=load(root/'docs/research/csi1000_long_accel_dev_v1/run_dev_search.py','devc');reg=load(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','regc');orig=load(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','origc');fg=load(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','fgc')
 native=orig.load_native(root,'000852.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END];state=reg.build_continuous_state(native,'000852.SH');minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000852.SH').reset_index(drop=True);minute=minute[minute.trading_day.between('2021-01-01',END)].reset_index(drop=True);events=base_events(dev,minute)
 alltr=[];annual=[];pooled=[]
 for p in POLICIES:
  tr=policy_trades(minute,events,p);alltr.append(tr)
  for y in YEARS: annual.append({'policy':p,'year':y,**metrics(tr[tr.year==y])})
  pooled.append({'policy':p,**metrics(tr)})
 annual=pd.DataFrame(annual);pooled=pd.DataFrame(pooled);elig=[]
 for p in POLICIES[1:]:
  y=annual[annual.policy==p];q=pooled[pooled.policy==p].iloc[0];ok=bool((y.trades>=15).all() and (y.mean_net1_bp>0).all() and q.trades>=60 and q.one_way_break_even_bp>1);elig.append({'policy':p,'eligible':ok,'worst_year_net1':float(y.mean_net1_bp.min()),'pooled_net1':float(q.mean_net1_bp),'pooled_trades':int(q.trades),'pooled_break_even':float(q.one_way_break_even_bp)})
 e=pd.DataFrame(elig);qq=e[e.eligible].sort_values(['worst_year_net1','pooled_net1','pooled_trades'],ascending=[False,False,False]);nom={'nomination':'NONE'} if not len(qq) else {'nomination':'CANDIDATE',**qq.iloc[0].to_dict()}
 out.mkdir(parents=True,exist_ok=True);pd.concat(alltr,ignore_index=True).to_csv(out/'trades.csv',index=False);annual.to_csv(out/'annual.csv',index=False);pooled.to_csv(out/'pooled.csv',index=False);e.to_csv(out/'eligibility.csv',index=False);(out/'summary.json').write_text(json.dumps({'schema':'csi1000_confirmation_dev_v1','development_only':True,'validation_queried':False,'blackbox_queried':False,'nomination':nom},indent=2,default=str)+'\n');print(json.dumps(nom,default=str))

def main():
 a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
