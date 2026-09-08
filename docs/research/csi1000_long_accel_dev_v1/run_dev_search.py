from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

SLOW_WINDOWS=(10,15,30); TAIL2=(0.40,0.60,0.80); CAPS=(None,0.60); HOLDS=(3,5,10); YEARS=(2021,2022,2023)

def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def build_events(minute):
    out=[]
    for session,z0 in minute.groupby('session',sort=False):
        z=z0.sort_values('minute').reset_index(drop=True); st=z.route_state.to_numpy(object); c=z.close.to_numpy(float); op=z.open.to_numpy(float); valid=z.valid.to_numpy(bool)
        r=np.full(len(z),np.nan)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(c[i]) and np.isfinite(c[i-1]) and c[i]>0 and c[i-1]>0: r[i]=np.log(c[i]/c[i-1])*1e4
        for i in range(35,len(z)):
            if st[i]!='HighVol' or st[i-1]!='NormalVol': continue
            recent=r[i-4:i+1]
            if not np.isfinite(recent).all(): continue
            net5=float(recent.sum()); tv=float(np.abs(recent).sum())
            if net5<=0 or tv<=0: continue
            row={'year':int(z.year.iloc[0]),'trading_day':z.trading_day.iloc[0],'session':session,'onset_row':i,'onset_minute':int(z.minute.iloc[i]),'tail1_share':abs(float(recent[-1]))/tv,'tail2_share':float(np.abs(recent[-2:]).sum())/tv}
            ok=True
            for w in SLOW_WINDOWS:
                x=r[i-4-w:i-4]
                if len(x)!=w or not np.isfinite(x).all(): ok=False; break
                row[f'slow{w}_net_bp']=float(x.sum())
            if not ok: continue
            for h in HOLDS:
                en=i+1; ex=en+h
                if ex>=len(z) or not valid[en:ex+1].all() or not (np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en]>0 and op[ex]>0): row[f'gross_{h}m_bp']=np.nan
                else: row[f'gross_{h}m_bp']=float(np.log(op[ex]/op[en])*1e4)
            out.append(row)
    return pd.DataFrame(out)

def select(events,w,t2,cap,h):
    z=events[(events[f'slow{w}_net_bp']>0)&(events.tail2_share>=t2)].copy()
    if cap is not None: z=z[z.tail1_share<cap]
    z=z[np.isfinite(z[f'gross_{h}m_bp'])].sort_values(['session','onset_row'])
    rows=[]
    for session,g in z.groupby('session',sort=False):
        nxt=-1
        for _,r in g.iterrows():
            i=int(r.onset_row)
            if i<nxt: continue
            rows.append(r); nxt=i+1+h
    return pd.DataFrame(rows)

def stats(z,h):
    n=len(z); mean=float(z[f'gross_{h}m_bp'].mean()) if n else np.nan
    return {'trades':n,'mean_gross_bp':mean,'mean_net1_bp':mean-2 if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan,'hit_rate':float((z[f'gross_{h}m_bp']>0).mean()) if n else np.nan}

def run(root,out):
    regime=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','reg'); orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','orig'); fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','fg')
    native=orig.load_native(root,'000852.SH').copy(); native['trading_day']=native.trading_day.astype(str).str[:10]; native=native[native.trading_day<='2023-12-31']
    state=regime.build_continuous_state(native,'000852.SH'); minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000852.SH').reset_index(drop=True); minute=minute[(minute.trading_day>='2021-01-01')&(minute.trading_day<='2023-12-31')].reset_index(drop=True)
    events=build_events(minute); annual=[]; pooled=[]
    for w in SLOW_WINDOWS:
      for t2 in TAIL2:
       for cap in CAPS:
        for h in HOLDS:
          z=select(events,w,t2,cap,h); p=stats(z,h); rec={'slow_window':w,'tail2_min':t2,'tail1_cap':('none' if cap is None else cap),'hold_min':h,**p}; pooled.append(rec)
          yr=[]
          for y in YEARS:
            q=stats(z[z.year==y],h); annual.append({'year':y,'slow_window':w,'tail2_min':t2,'tail1_cap':('none' if cap is None else cap),'hold_min':h,**q}); yr.append(q)
          rec['worst_year_net1']=min(q['mean_net1_bp'] for q in yr if np.isfinite(q['mean_net1_bp'])) if all(np.isfinite(q['mean_net1_bp']) for q in yr) else np.nan
          rec['eligible']=bool(all(q['trades']>=15 and q['mean_net1_bp']>0 for q in yr) and p['trades']>=60 and p['one_way_break_even_bp']>1)
    annual=pd.DataFrame(annual); pooled=pd.DataFrame(pooled)
    elig=pooled[pooled.eligible].copy()
    if len(elig):
        elig['_slow_rank']=-elig.slow_window; elig['_cap_rank']=np.where(elig.tail1_cap.astype(str)=='none',0,1)
        nom=elig.sort_values(['worst_year_net1','mean_net1_bp','trades','hold_min','_slow_rank','tail2_min','_cap_rank'],ascending=[False,False,False,True,True,True,True]).iloc[0].drop(labels=['_slow_rank','_cap_rank']).to_dict(); nom['nomination']='CANDIDATE'
    else: nom={'nomination':'NONE'}
    out.mkdir(parents=True,exist_ok=True); events.to_csv(out/'dev_events.csv',index=False); annual.to_csv(out/'annual_surface.csv',index=False); pooled.to_csv(out/'pooled_surface.csv',index=False); (out/'nomination.json').write_text(json.dumps(nom,indent=2,default=str)+'\n'); (out/'summary.json').write_text(json.dumps({'schema':'csi1000_long_accel_dev_v1','development_only':True,'validation_inspected':False,'blackbox_queried':False,'events':len(events),'nomination':nom},indent=2,default=str)+'\n'); print(json.dumps(nom,default=str))

def main():
    a=argparse.ArgumentParser(); a.add_argument('--repo-root',required=True); a.add_argument('--out',required=True); x=a.parse_args(); run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__': main()
