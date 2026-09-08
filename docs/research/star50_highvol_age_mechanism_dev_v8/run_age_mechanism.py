from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
import numpy as np,pandas as pd
START='2021-01-01';END='2023-12-31';YEARS=(2021,2022,2023)
LANDMARKS={1:'onset',2:'early_persist',4:'mature',7:'late'}

def load_module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def build_minute(root):
 reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','agereg');orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','ageorig');fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','agefg')
 native=orig.load_native(root,'000688.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END];state=reg.build_continuous_state(native,'000688.SH');m=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000688.SH').reset_index(drop=True);return m[(m.trading_day>=START)&(m.trading_day<=END)].reset_index(drop=True)

def build_landmarks(minute):
 rows=[]
 for session,z0 in minute.groupby('session',sort=False):
  z=z0.sort_values('minute').reset_index(drop=True);state=z.route_state.to_numpy(object);c=z.close.to_numpy(float);op=z.open.to_numpy(float);valid=z.valid.to_numpy(bool);r=np.full(len(z),np.nan);age=0
  for i in range(1,len(z)):
   if valid[i] and valid[i-1] and np.isfinite(c[i]) and np.isfinite(c[i-1]) and c[i]>0 and c[i-1]>0:r[i]=np.log(c[i]/c[i-1])*1e4
  for i in range(len(z)):
   age=age+1 if state[i]=='HighVol' else 0
   if age not in LANDMARKS:continue
   if i<4:continue
   recent=r[i-4:i+1]
   if len(recent)!=5 or not np.isfinite(recent).all():continue
   net5=float(recent.sum());sign=1 if net5>0 else (-1 if net5<0 else 0)
   if sign==0:continue
   en=i+1;ex=en+3
   if ex>=len(z) or not valid[en:ex+1].all() or not(np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en]>0 and op[ex]>0):continue
   raw=float(np.log(op[ex]/op[en])*1e4);signed=float(sign*raw)
   rows.append({'year':int(z.year.iloc[0]),'trading_day':str(z.trading_day.iloc[0]),'session':str(session),'landmark':LANDMARKS[age],'highvol_age':age,'minute':int(z.minute.iloc[i]),'net5_bp':net5,'direction':'up' if sign>0 else 'down','gross_signed_3m_bp':signed,'abs_3m_displacement_bp':abs(raw),'vol_ratio':float(z.recovery_ratio.iloc[i]) if np.isfinite(z.recovery_ratio.iloc[i]) else np.nan})
 return pd.DataFrame(rows)

def stats(z):
 q=pd.to_numeric(z.gross_signed_3m_bp,errors='coerce').dropna();a=pd.to_numeric(z.abs_3m_displacement_bp,errors='coerce').dropna();n=len(q);m=float(q.mean()) if n else np.nan
 return {'n':int(n),'mean_signed_3m_bp':m,'median_signed_3m_bp':float(q.median()) if n else np.nan,'continuation_hit':float((q>0).mean()) if n else np.nan,'mean_net_1bp_per_leg':m-2 if n else np.nan,'one_way_break_even_bp':m/2 if n else np.nan,'mean_abs_3m_displacement_bp':float(a.mean()) if len(a) else np.nan}

def run(root,out):
 m=build_minute(root);e=build_landmarks(m);rows=[];promising=[]
 for age,name in LANDMARKS.items():
  z=e[e.landmark==name];annual=[]
  for y in YEARS:
   q=stats(z[z.year==y]);annual.append({'year':y,**q});rows.append({'landmark':name,'highvol_age':age,'year':y,**q})
  p=stats(z);rows.append({'landmark':name,'highvol_age':age,'year':'pooled',**p});a=pd.DataFrame(annual);ok=bool((a.n>=15).all() and (a.mean_net_1bp_per_leg>0).all());
  if ok:promising.append(name)
 meta={'schema':'star50_highvol_age_mechanism_dev_v8','development_only':True,'validation_queried':False,'blackbox_queried':False,'landmarks':LANDMARKS,'candidate_nominated':False,'mechanism_promising_landmarks':promising,'event_count':len(e)}
 out.mkdir(parents=True,exist_ok=True);e.to_csv(out/'landmark_events.csv',index=False);pd.DataFrame(rows).to_csv(out/'summary.csv',index=False);(out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta));print(pd.DataFrame(rows).to_csv(index=False))

def main():
 a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
