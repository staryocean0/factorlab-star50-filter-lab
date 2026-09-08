from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

START='2021-01-01';END='2023-12-31';YEARS=(2021,2022,2023);THRESHOLDS=(2,4,6,8,12)


def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def build_parent(root):
    dev=load_module(root/'docs/research/csi1000_long_accel_dev_v1/run_dev_search.py','stdev')
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','streg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','storig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','stfg')
    native=orig.load_native(root,'000852.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,'000852.SH');minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000852.SH').reset_index(drop=True)
    minute=minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)
    events=dev.build_events(minute);sel=dev.select(events,30,.60,.60,3).copy().reset_index(drop=True)
    if len(sel)!=104:raise AssertionError(f'parent count {len(sel)} != 104')
    return minute,sel


def simulate(minute,sel,threshold):
    groups={k:g.sort_values('minute').reset_index(drop=True) for k,g in minute.groupby('session',sort=False)}
    rows=[]
    for cid,r in sel.iterrows():
        g=groups[str(r.session)];i=int(r.onset_row);en=i+1;parent_ex=en+3
        p0=float(g.open.iloc[en]);exit_i=parent_ex;stop_after=0;trigger_close_bp=np.nan
        if threshold is not None:
            for held in (1,2):
                bar_i=en+held-1
                c=float(g.close.iloc[bar_i])
                if not (np.isfinite(c) and c>0):raise AssertionError('invalid close on parent path')
                x=float(np.log(c/p0)*1e4)
                if x<=-float(threshold):
                    exit_i=en+held;stop_after=held;trigger_close_bp=x;break
        px=float(g.open.iloc[exit_i])
        if not (np.isfinite(px) and px>0):raise AssertionError('invalid exit open')
        gross=float(np.log(px/p0)*1e4)
        rows.append({'candidate_id':cid,'year':int(r.year),'trading_day':str(r.trading_day),'session':str(r.session),'onset_row':i,
                     'threshold_bp':'no_stop' if threshold is None else threshold,'stopped':bool(stop_after),'stop_after_min':stop_after,
                     'trigger_close_bp':trigger_close_bp,'holding_min':int(exit_i-en),'gross_bp':gross})
    return pd.DataFrame(rows)


def metrics(z):
    n=len(z);g=z.gross_bp.to_numpy(float);q10=float(np.quantile(g,.10));es=float(g[g<=q10].mean())
    return {'trades':n,'stops':int(z.stopped.sum()),'stop_rate':float(z.stopped.mean()),'mean_gross_bp':float(g.mean()),'mean_net1_bp':float(g.mean()-2),
            'median_gross_bp':float(np.median(g)),'q10_gross_bp':q10,'worst_gross_bp':float(g.min()),'es10_gross_bp':es,
            'hit_rate':float((g>0).mean()),'mean_holding_min':float(z.holding_min.mean())}


def run(root,out):
    minute,sel=build_parent(root)
    surfaces=[];alltr=[]
    for th in (None,)+THRESHOLDS:
        z=simulate(minute,sel,th);alltr.append(z)
        for y in YEARS:surfaces.append({'threshold_bp':'no_stop' if th is None else th,'year':y,**metrics(z[z.year==y])})
        surfaces.append({'threshold_bp':'no_stop' if th is None else th,'year':'pooled',**metrics(z)})
    s=pd.DataFrame(surfaces);p=s[s.year.astype(str)=='pooled'].set_index('threshold_bp');base=p.loc['no_stop']
    eligible=[]
    for th in THRESHOLDS:
        yr=s[(s.threshold_bp.astype(str)==str(th))&(s.year.astype(str).isin([str(y) for y in YEARS]))]
        pooled=p.loc[th] if th in p.index else p.loc[str(th)]
        ok=bool((yr.mean_net1_bp>0).all() and pooled.mean_net1_bp>=base.mean_net1_bp and pooled.q10_gross_bp>base.q10_gross_bp and pooled.worst_gross_bp>base.worst_gross_bp)
        if ok:
            eligible.append({'threshold_bp':th,'worst_year_net1':float(yr.mean_net1_bp.min()),'pooled_mean_net1':float(pooled.mean_net1_bp),'pooled_es10':float(pooled.es10_gross_bp)})
    if eligible:
        e=pd.DataFrame(eligible).sort_values(['worst_year_net1','pooled_mean_net1','pooled_es10','threshold_bp'],ascending=[False,False,False,True]).iloc[0]
        nomination={'nomination':'STOP','threshold_bp':int(e.threshold_bp)}
    else:nomination={'nomination':'NO_STOP'}
    out.mkdir(parents=True,exist_ok=True);pd.concat(alltr,ignore_index=True).to_csv(out/'trade_surface.csv',index=False);s.to_csv(out/'summary_surface.csv',index=False)
    (out/'nomination.json').write_text(json.dumps(nomination,indent=2)+'\n')
    meta={'schema':'csi1000_stop_dev_v1','development_only':True,'validation_queried':False,'blackbox_queried':False,'parent_trades':len(sel),'thresholds':list(THRESHOLDS),'nomination':nomination}
    (out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))


def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
