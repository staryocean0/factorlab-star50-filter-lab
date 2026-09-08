from __future__ import annotations

import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

START='2021-01-01'; END='2023-12-31'; YEARS=(2021,2022,2023); SYMBOL='000688.SH'
VIEWS=('all','UpToDown','DownToUp')


def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def build_minute(root):
    v12=load_module(root/'docs/research/star50_turnover_pressure_dev_v12/run_turnover_pressure.py','v15_v12')
    return v12.build_minute(root)


def build_events(minute):
    rows=[]; raw=0
    for session,z0 in minute.groupby('session',sort=False):
        z=z0.sort_values('minute').reset_index(drop=True); st=z.route_state.to_numpy(object); c=z.close.to_numpy(float); op=z.open.to_numpy(float); valid=z.valid.to_numpy(bool)
        r=np.full(len(z),np.nan)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(c[i]) and np.isfinite(c[i-1]) and c[i]>0 and c[i-1]>0:r[i]=np.log(c[i]/c[i-1])*1e4
        net5=np.full(len(z),np.nan)
        for i in range(4,len(z)):
            q=r[i-4:i+1]
            if len(q)==5 and np.isfinite(q).all():net5[i]=float(q.sum())
        next_entry=0
        for i in range(5,len(z)):
            if st[i]!='HighVol' or st[i-1]!='HighVol':continue
            a=net5[i-1]; b=net5[i]
            if not(np.isfinite(a) and np.isfinite(b)) or a==0 or b==0 or np.sign(a)==np.sign(b):continue
            raw+=1; new_sign=1 if b>0 else -1; typ='UpToDown' if new_sign<0 else 'DownToUp'
            en=i+1; ex=en+3
            if en<next_entry or ex>=len(z) or not valid[en:ex+1].all():continue
            if not(np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en]>0 and op[ex]>0):continue
            fut=float(np.log(op[ex]/op[en])*1e4)
            rows.append({'year':int(z.year.iloc[i]),'trading_day':str(z.trading_day.iloc[i]),'session':str(session),'minute':int(z.minute.iloc[i]),'flip_type':typ,'old_net5_bp':float(a),'new_net5_bp':float(b),'future_raw_3m_bp':fut,'new_direction_continuation_3m_bp':float(new_sign*fut),'old_direction_reversal_3m_bp':float(-new_sign*fut),'abs_3m_displacement_bp':abs(fut)})
            next_entry=ex
    return pd.DataFrame(rows),raw


def stats(z):
    c=pd.to_numeric(z.new_direction_continuation_3m_bp,errors='coerce').dropna(); r=pd.to_numeric(z.old_direction_reversal_3m_bp,errors='coerce').dropna(); a=pd.to_numeric(z.abs_3m_displacement_bp,errors='coerce').dropna(); n=len(c); mc=float(c.mean()) if n else np.nan; mr=float(r.mean()) if n else np.nan
    return {'n':int(n),'mean_continuation_3m_bp':mc,'median_continuation_3m_bp':float(c.median()) if n else np.nan,'continuation_hit':float((c>0).mean()) if n else np.nan,'continuation_net_1bp_per_leg':mc-2 if n else np.nan,'continuation_one_way_break_even_bp':mc/2 if n else np.nan,'mean_reversal_3m_bp':mr,'median_reversal_3m_bp':float(r.median()) if n else np.nan,'reversal_hit':float((r>0).mean()) if n else np.nan,'reversal_net_1bp_per_leg':mr-2 if n else np.nan,'reversal_one_way_break_even_bp':mr/2 if n else np.nan,'mean_abs_3m_displacement_bp':float(a.mean()) if len(a) else np.nan}


def run(root,out):
    e,raw=build_events(build_minute(root)); rows=[]; promising=[]
    for view in VIEWS:
        z=e if view=='all' else e[e.flip_type==view]; annual=[]
        for y in YEARS:
            q=stats(z[z.year==y]); annual.append(q); rows.append({'view':view,'year':y,**q})
        rows.append({'view':view,'year':'pooled',**stats(z)}); a=pd.DataFrame(annual)
        if len(a)==3 and bool((a.n>=15).all()):
            cont=bool((a.continuation_net_1bp_per_leg>0).all()); rev=bool((a.reversal_net_1bp_per_leg>0).all())
            if cont or rev:promising.append({'view':view,'direction':'new_direction_continuation' if cont else 'old_direction_reversal'})
    s={'schema':'star50_highvol_sign_flip_dev_v15','development_only':True,'validation_queried':False,'blackbox_queried':False,'candidate_nominated':False,'views':list(VIEWS),'raw_flip_count':int(raw),'event_count':int(len(e)),'flip_counts':{str(k):int(v) for k,v in e.flip_type.value_counts().to_dict().items()},'mechanism_promising_views':promising}
    out.mkdir(parents=True,exist_ok=True); e.to_csv(out/'events.csv',index=False); pd.DataFrame(rows).to_csv(out/'summary.csv',index=False); (out/'summary.json').write_text(json.dumps(s,indent=2)+'\n'); print(json.dumps(s)); print(pd.DataFrame(rows).to_csv(index=False))


def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',required=True); p.add_argument('--out',required=True); a=p.parse_args(); run(Path(a.repo_root).resolve(),Path(a.out))
if __name__=='__main__':main()
