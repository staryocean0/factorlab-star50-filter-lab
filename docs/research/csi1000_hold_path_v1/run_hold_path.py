from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

END='2026-08-21'; DEV_START='2021-01-01'; DEV_END='2023-12-31'; VAL_START='2024-01-01'; VAL_END=END
BOOT_DRAWS=10_000; BOOT_SEED=20260908


def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def build_minute(root):
    dev=load_module(root/'docs/research/csi1000_long_accel_dev_v1/run_dev_search.py','hpdev')
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','hpreg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','hporig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','hpfg')
    native=orig.load_native(root,'000852.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,'000852.SH')
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000852.SH').reset_index(drop=True)
    minute=minute[(minute.trading_day>=DEV_START)&(minute.trading_day<=END)].reset_index(drop=True)
    return dev,minute


def select_candidates(dev,minute,start,end,role):
    m=minute[(minute.trading_day>=start)&(minute.trading_day<=end)].reset_index(drop=True)
    events=dev.build_events(m)
    sel=dev.select(events,30,.60,.60,3).copy().reset_index(drop=True)
    sel['role']=role
    return m,sel


def path_rows(minute,sel):
    groups={k:g.sort_values('minute').reset_index(drop=True) for k,g in minute.groupby('session',sort=False)}
    rows=[]
    for cid,r in sel.reset_index(drop=True).iterrows():
        g=groups[str(r.session)];i=int(r.onset_row);en=i+1;ex=en+3
        if ex>=len(g): raise AssertionError('candidate exit outside session')
        sl=g.iloc[en:ex+1]
        if len(sl)!=4 or not sl.valid.all(): raise AssertionError('selected candidate lost valid execution path')
        p=[float(g.open.iloc[en+j]) for j in range(4)]
        if not all(np.isfinite(x) and x>0 for x in p): raise AssertionError('invalid open in selected candidate')
        c=[float(np.log(p[j]/p[j-1])*1e4) for j in range(1,4)]
        cum=[float(np.log(p[j]/p[0])*1e4) for j in range(1,4)]
        highs=pd.to_numeric(g.high.iloc[en:ex],errors='coerce').to_numpy(float)
        lows=pd.to_numeric(g.low.iloc[en:ex],errors='coerce').to_numpy(float)
        if not (np.isfinite(highs).all() and np.isfinite(lows).all()): raise AssertionError('invalid high/low in selected candidate')
        mfe=float(np.log(np.max(highs)/p[0])*1e4)
        mae=float(np.log(np.min(lows)/p[0])*1e4)
        gross=float(r.gross_3m_bp)
        if abs(sum(c)-gross)>1e-8 or abs(cum[-1]-gross)>1e-8: raise AssertionError('path decomposition does not reproduce frozen gross')
        rows.append({
            'candidate_id':cid,'role':r.role,'year':int(r.year),'trading_day':str(r.trading_day),'session':str(r.session),
            'onset_row':i,'onset_minute':int(r.onset_minute),'entry_minute':int(g.minute.iloc[en]),'exit_minute':int(g.minute.iloc[ex]),
            'minute1_bp':c[0],'minute2_bp':c[1],'minute3_bp':c[2],
            'cum1_bp':cum[0],'cum2_bp':cum[1],'cum3_bp':cum[2],
            'mfe_bp':mfe,'mae_bp':mae,
            'state_after_1m':str(g.route_state.iloc[en]),'state_after_2m':str(g.route_state.iloc[en+1]),
        })
    return pd.DataFrame(rows)


def summarize(z,role,year='pooled'):
    q=z[z.role==role] if year=='pooled' else z[(z.role==role)&(z.year==int(year))]
    n=len(q);out={'role':role,'year':year,'trades':n}
    if not n:return out
    means={k:float(q[k].mean()) for k in ('minute1_bp','minute2_bp','minute3_bp')}
    for k,v in means.items():out['mean_'+k]=v;out['median_'+k]=float(q[k].median())
    total=sum(means.values())
    for k,v in means.items():out['share_'+k]=float(v/total) if abs(total)>1e-15 else np.nan
    for h in (1,2,3):
        out[f'mean_cum{h}_bp']=float(q[f'cum{h}_bp'].mean());out[f'hit_cum{h}']=float((q[f'cum{h}_bp']>0).mean())
    for x in ('mfe_bp','mae_bp'):
        for p in (10,25,50,75,90):out[f'{x}_q{p}']=float(q[x].quantile(p/100))
    out['still_highvol_after_1m']=float(q.state_after_1m.eq('HighVol').mean())
    out['still_highvol_after_2m']=float(q.state_after_2m.eq('HighVol').mean())
    out['profit_1m_to_loss_3m']=float(((q.cum1_bp>0)&(q.cum3_bp<=0)).mean())
    out['loss_1m_to_profit_3m']=float(((q.cum1_bp<=0)&(q.cum3_bp>0)).mean())
    out['mean_net1bp_1m_exit']=out['mean_cum1_bp']-2
    out['mean_net1bp_2m_exit']=out['mean_cum2_bp']-2
    out['mean_net1bp_3m_exit']=out['mean_cum3_bp']-2
    return out


def bootstrap_contribution(z,role,col,draws=BOOT_DRAWS,seed=BOOT_SEED):
    q=z[z.role==role][['trading_day',col]].copy();g=q.groupby('trading_day')[col].agg(['sum','count']).reset_index()
    if len(g)<2:return {'role':role,'component':col,'days':len(g),'observed_mean_bp':float(q[col].mean()) if len(q) else np.nan,'ci_low':np.nan,'ci_high':np.nan}
    sums=g['sum'].to_numpy(float);counts=g['count'].to_numpy(float);rng=np.random.default_rng(seed+(2 if col=='minute2_bp' else 3)+(0 if role=='Development' else 100))
    vals=np.empty(draws,float)
    for b in range(draws):
        ix=rng.integers(0,len(g),len(g));vals[b]=sums[ix].sum()/counts[ix].sum()
    lo,hi=np.quantile(vals,[.025,.975])
    return {'role':role,'component':col,'days':len(g),'observed_mean_bp':float(q[col].mean()),'ci_low':float(lo),'ci_high':float(hi)}


def run(root,out):
    dev,minute=build_minute(root)
    dm,ds=select_candidates(dev,minute,DEV_START,DEV_END,'Development')
    vm,vs=select_candidates(dev,minute,VAL_START,VAL_END,'Validation')
    if len(ds)!=104 or len(vs)!=129: raise AssertionError(f'frozen counts mismatch: dev={len(ds)} val={len(vs)}')
    paths=pd.concat([path_rows(dm,ds),path_rows(vm,vs)],ignore_index=True)
    summaries=[]
    for role,years in [('Development',(2021,2022,2023)),('Validation',(2024,2025,2026))]:
        summaries.append(summarize(paths,role,'pooled'))
        for y in years:summaries.append(summarize(paths,role,y))
    boot=[bootstrap_contribution(paths,r,c) for r in ('Development','Validation') for c in ('minute2_bp','minute3_bp')]
    out.mkdir(parents=True,exist_ok=True);paths.to_csv(out/'trade_paths.csv',index=False);pd.DataFrame(summaries).to_csv(out/'path_summary.csv',index=False);pd.DataFrame(boot).to_csv(out/'bootstrap_summary.csv',index=False)
    meta={'schema':'csi1000_hold_path_v1','candidate_counts':{'Development':len(ds),'Validation':len(vs)},'blackbox_queried':False,'development_horizon':[DEV_START,DEV_END],'validation_horizon':[VAL_START,VAL_END],'bootstrap_draws':BOOT_DRAWS,'bootstrap_seed':BOOT_SEED}
    (out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))


def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
