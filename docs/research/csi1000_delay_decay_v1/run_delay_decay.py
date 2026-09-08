from __future__ import annotations

import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

SYMBOL='000852.SH'; START='2021-01-01'; END='2026-08-21'; DELAYS=(0,1,2,3,5); HOLD=3; BOOT=10000; SEED=20260908


def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def role(day):
    return 'Development' if str(day)<='2023-12-31' else 'Validation'


def build_delay_rows(minute, selected):
    by_session={k:v.sort_values('minute').reset_index(drop=True) for k,v in minute.groupby('session',sort=False)}
    rows=[]
    for cid,e in enumerate(selected.sort_values(['trading_day','session','onset_row'],kind='stable').itertuples(index=False)):
        z=by_session[str(e.session)];i=int(e.onset_row);valid=z.valid.to_numpy(bool);op=z.open.to_numpy(float)
        for d in DELAYS:
            en=i+1+d;ex=en+HOLD
            if ex>=len(z) or not valid[en:ex+1].all() or not(np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en]>0 and op[ex]>0):
                gross=np.nan;state_before=None;ratio_before=np.nan;entry_min=np.nan;exit_min=np.nan
            else:
                gross=float(np.log(op[ex]/op[en])*1e4)
                state_before=str(z.route_state.iloc[i+d])
                ratio_before=float(z.recovery_ratio.iloc[i+d]) if np.isfinite(z.recovery_ratio.iloc[i+d]) else np.nan
                entry_min=int(z.minute.iloc[en]);exit_min=int(z.minute.iloc[ex])
            rows.append({'candidate_id':cid,'trading_day':str(e.trading_day)[:10],'year':int(e.year),'role':role(e.trading_day),'session':str(e.session),'onset_minute':int(e.onset_minute),'delay_min':d,'entry_minute':entry_min,'exit_minute':exit_min,'gross_bp':gross,'state_before_entry':state_before,'ratio_before_entry':ratio_before})
    return pd.DataFrame(rows)


def summarize(rows):
    out=[]
    for (r,d),g0 in rows.groupby(['role','delay_min'],sort=False):
        for y in list(sorted(g0.year.unique()))+['pooled']:
            g=g0 if y=='pooled' else g0[g0.year==y]
            z=g[np.isfinite(g.gross_bp)]
            n=len(z);mean=float(z.gross_bp.mean()) if n else np.nan
            out.append({'role':r,'year':y,'delay_min':int(d),'eligible_events':n,'mean_gross_bp':mean,'median_gross_bp':float(z.gross_bp.median()) if n else np.nan,'hit_rate':float((z.gross_bp>0).mean()) if n else np.nan,'mean_net1_bp':mean-2 if n else np.nan,'still_highvol_fraction':float((z.state_before_entry=='HighVol').mean()) if n else np.nan})
    return pd.DataFrame(out)


def paired(rows):
    w=rows.pivot(index=['candidate_id','trading_day','year','role'],columns='delay_min',values='gross_bp').reset_index()
    out=[]
    for r in ('Development','Validation'):
        q=w[w.role==r]
        for d in DELAYS[1:]:
            z=q[np.isfinite(q[0]) & np.isfinite(q[d])].copy();z['diff']=z[d]-z[0]
            out.append({'role':r,'delay_min':d,'pairs':len(z),'mean_delay_minus_immediate_bp':float(z['diff'].mean()) if len(z) else np.nan,'median_delay_minus_immediate_bp':float(z['diff'].median()) if len(z) else np.nan})
    return pd.DataFrame(out),w


def bootstrap(w, role_name, d, draws=BOOT, seed=SEED):
    z=w[(w.role==role_name)&np.isfinite(w[0])&np.isfinite(w[d])].copy();z['diff']=z[d]-z[0]
    groups=[g['diff'].to_numpy(float) for _,g in z.groupby('trading_day',sort=True)]
    if not groups:return {'role':role_name,'delay_min':d,'draws':0,'candidate_days':0,'q025':np.nan,'q50':np.nan,'q975':np.nan,'fraction_lt_zero':np.nan}
    rng=np.random.default_rng(seed+d+(0 if role_name=='Development' else 100));m=len(groups);vals=np.empty(draws)
    for b in range(draws):
        idx=rng.integers(0,m,size=m);vals[b]=np.concatenate([groups[i] for i in idx]).mean()
    q=np.quantile(vals,[.025,.5,.975])
    return {'role':role_name,'delay_min':d,'draws':draws,'candidate_days':m,'q025':float(q[0]),'q50':float(q[1]),'q975':float(q[2]),'fraction_lt_zero':float((vals<0).mean())}


def run(root,out):
    dev=load_module(root/'docs/research/csi1000_long_accel_dev_v1/run_dev_search.py','devdelay');reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','regdelay');orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','origdelay');fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','fgdelay')
    native=orig.load_native(root,SYMBOL).copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,SYMBOL);minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),SYMBOL).reset_index(drop=True);minute=minute[minute.trading_day.between(START,END)].reset_index(drop=True)
    events=dev.build_events(minute);selected=dev.select(events,30,.60,.60,3).copy()
    rows=build_delay_rows(minute,selected)
    # d=0 must reproduce frozen selected-event gross exactly.
    d0=rows[rows.delay_min==0].sort_values(['trading_day','session','onset_minute']).gross_bp.to_numpy(float)
    ref=selected.sort_values(['trading_day','session','onset_minute']).gross_3m_bp.to_numpy(float)
    if len(d0)!=len(ref) or np.nanmax(np.abs(d0-ref))>1e-9: raise AssertionError('d0 does not reproduce frozen candidate')
    summary=summarize(rows);pair,w=paired(rows);boots=pd.DataFrame([bootstrap(w,r,d) for r in ('Development','Validation') for d in DELAYS[1:]])
    out.mkdir(parents=True,exist_ok=True);rows.to_csv(out/'delay_rows.csv',index=False);summary.to_csv(out/'delay_summary.csv',index=False);pair.to_csv(out/'paired_delay_summary.csv',index=False);boots.to_csv(out/'bootstrap_summary.csv',index=False)
    counts={'development_candidates':int((selected.trading_day.astype(str)<='2023-12-31').sum()),'validation_candidates':int((selected.trading_day.astype(str)>='2024-01-01').sum())}
    s={'schema':'csi1000_delay_decay_v1','candidate':{'slow_window':30,'tail2_min':.60,'tail1_cap':.60,'hold_min':3,'direction':'long'},'delays':list(DELAYS),'counts':counts,'blackbox_queried':False}
    (out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s));return s


def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
