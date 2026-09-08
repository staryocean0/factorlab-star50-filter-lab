from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

START='2021-01-01';END='2023-12-31';YEARS=(2021,2022,2023);HORIZONS=(1,2,3,5,10);DRAWS=10_000;SEED=20260908


def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def build_minute(root):
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','sreg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','sorig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','sfg')
    native=orig.load_native(root,'000688.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,'000688.SH')
    m=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000688.SH').reset_index(drop=True)
    return m[(m.trading_day>=START)&(m.trading_day<=END)].reset_index(drop=True)


def build_events(minute):
    rows=[]
    for session,z0 in minute.groupby('session',sort=False):
        z=z0.sort_values('minute').reset_index(drop=True);st=z.route_state.to_numpy(object);c=z.close.to_numpy(float);op=z.open.to_numpy(float);valid=z.valid.to_numpy(bool)
        r=np.full(len(z),np.nan)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(c[i]) and np.isfinite(c[i-1]) and c[i]>0 and c[i-1]>0:r[i]=np.log(c[i]/c[i-1])*1e4
        for i in range(35,len(z)):
            if st[i]!='HighVol' or st[i-1]!='NormalVol':continue
            recent=r[i-4:i+1]
            if len(recent)!=5 or not np.isfinite(recent).all():continue
            net5=float(recent.sum());tv=float(np.abs(recent).sum())
            if tv<=0 or net5==0:continue
            direction=1 if net5>0 else -1
            slow=r[i-34:i-4]
            if len(slow)!=30 or not np.isfinite(slow).all():continue
            slow30=float(slow.sum())
            row={'year':int(z.year.iloc[0]),'trading_day':str(z.trading_day.iloc[0]),'session':str(session),'onset_row':i,'onset_minute':int(z.minute.iloc[i]),
                 'direction':'up' if direction>0 else 'down','direction_sign':direction,'net5_bp':net5,'tv5_bp':tv,'tail1_share':abs(float(recent[-1]))/tv,
                 'tail2_share':float(np.abs(recent[-2:]).sum())/tv,'efficiency5':abs(net5)/tv,'slow30_net_bp':slow30,
                 'slow_aligned':bool(direction*slow30>0),'accel_high':bool(float(np.abs(recent[-2:]).sum())/tv>=.60),
                 'efficient_high':bool(abs(net5)/tv>=.60),'single_spike':bool(abs(float(recent[-1]))/tv>=.60),
                 'vol_ratio':float(z.recovery_ratio.iloc[i]) if np.isfinite(z.recovery_ratio.iloc[i]) else np.nan}
            en=i+1
            for h in HORIZONS:
                ex=en+h
                if ex>=len(z) or not valid[en:ex+1].all() or not(np.isfinite(op[en]) and np.isfinite(op[ex]) and op[en]>0 and op[ex]>0):row[f'signed_{h}m_bp']=np.nan
                else:row[f'signed_{h}m_bp']=float(direction*np.log(op[ex]/op[en])*1e4)
            rows.append(row)
    return pd.DataFrame(rows)


def agg(events,group_cols,label):
    rows=[]
    groupby_arg=group_cols[0] if len(group_cols)==1 else group_cols
    for keys,g in events.groupby(groupby_arg,dropna=False,sort=True):
        if not isinstance(keys,tuple):keys=(keys,)
        base={'view':label,**{c:k for c,k in zip(group_cols,keys)}}
        for h in HORIZONS:
            q=pd.to_numeric(g[f'signed_{h}m_bp'],errors='coerce').dropna()
            rows.append({**base,'horizon_min':h,'n':len(q),'mean_signed_bp':float(q.mean()) if len(q) else np.nan,'median_signed_bp':float(q.median()) if len(q) else np.nan,'continuation_hit':float((q>0).mean()) if len(q) else np.nan})
    return rows


def bootstrap(events,mask,h,draws=DRAWS,seed=SEED):
    q=events.loc[mask,['trading_day',f'signed_{h}m_bp']].dropna();g=q.groupby('trading_day')[f'signed_{h}m_bp'].agg(['sum','count']).reset_index()
    if len(q)<20 or len(g)<2:return {'n':len(q),'days':len(g),'mean':float(q.iloc[:,1].mean()) if len(q) else np.nan,'ci_low':np.nan,'ci_high':np.nan}
    sums=g['sum'].to_numpy(float);cnt=g['count'].to_numpy(float);rng=np.random.default_rng(seed+h)
    vals=np.empty(draws)
    for b in range(draws):
        ix=rng.integers(0,len(g),len(g));vals[b]=sums[ix].sum()/cnt[ix].sum()
    lo,hi=np.quantile(vals,[.025,.975]);return {'n':len(q),'days':len(g),'mean':float(q.iloc[:,1].mean()),'ci_low':float(lo),'ci_high':float(hi)}


def run(root,out):
    minute=build_minute(root);events=build_events(minute)
    summary=[]
    events['all']='all'
    summary += agg(events,['all'],'all')
    summary += agg(events,['direction'],'direction')
    summary += agg(events,['direction','slow_aligned'],'direction_x_slow')
    summary += agg(events,['direction','accel_high'],'direction_x_accel')
    summary += agg(events,['direction','efficient_high'],'direction_x_efficiency')
    cube=['direction','slow_aligned','accel_high','efficient_high'];summary += agg(events,cube,'full_cube')
    annual=[]
    for y in YEARS:
        e=events[events.year==y]
        annual += agg(e,['all'],f'year_{y}_all')
        annual += agg(e,cube,f'year_{y}_cube')
    boot=[]
    for keys,g in events.groupby(cube,dropna=False,sort=True):
        mask=np.ones(len(events),dtype=bool)
        rec={c:k for c,k in zip(cube,keys)}
        for c,k in zip(cube,keys):mask &= events[c].eq(k).to_numpy()
        for h in (3,5):boot.append({**rec,'horizon_min':h,**bootstrap(events,mask,h)})
    out.mkdir(parents=True,exist_ok=True);events.drop(columns=['all']).to_csv(out/'events.csv',index=False);pd.DataFrame(summary).to_csv(out/'summary.csv',index=False);pd.DataFrame(annual).to_csv(out/'annual_summary.csv',index=False);pd.DataFrame(boot).to_csv(out/'bootstrap_cube.csv',index=False)
    meta={'schema':'star50_highvol_mechanism_dev_v1','development_only':True,'validation_queried':False,'blackbox_queried':False,'event_count':len(events),'horizons':list(HORIZONS),'bootstrap_draws':DRAWS}
    (out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))


def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
