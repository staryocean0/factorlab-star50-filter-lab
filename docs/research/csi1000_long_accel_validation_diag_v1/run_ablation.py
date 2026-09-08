from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

START='2024-01-01'; END='2026-08-21'; YEARS=(2024,2025,2026); HOLD=3

def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def select(events,variant):
    z=events.copy()
    if variant in ('slow30_only','full_candidate'): z=z[z.slow30_net_bp>0]
    if variant in ('accel_only','full_candidate'): z=z[(z.tail2_share>=.60)&(z.tail1_share<.60)]
    z=z[np.isfinite(z.gross_3m_bp)].sort_values(['session','onset_row'])
    rows=[]
    for session,g in z.groupby('session',sort=False):
        nxt=-1
        for _,r in g.iterrows():
            i=int(r.onset_row)
            if i<nxt: continue
            rows.append(r);nxt=i+1+HOLD
    q=pd.DataFrame(rows)
    if len(q): q=q.copy();q['gross_bp']=q.gross_3m_bp
    return q

def metrics(z):
    n=len(z);mean=float(z.gross_bp.mean()) if n else np.nan
    return {'trades':n,'mean_gross_bp':mean,'mean_net1_bp':mean-2 if n else np.nan,'hit_rate':float((z.gross_bp>0).mean()) if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan}

def run(root,out):
    dev=load_module(root/'docs/research/csi1000_long_accel_dev_v1/run_dev_search.py','devab');reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','regab');orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','origab');fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','fgab')
    native=orig.load_native(root,'000852.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,'000852.SH');minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000852.SH').reset_index(drop=True);minute=minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)
    events=dev.build_events(minute)
    variants=('base_long_highvol','slow30_only','accel_only','full_candidate');rows=[];trade_frames=[]
    for v in variants:
        z=select(events,v);z=z.copy();z['variant']=v;trade_frames.append(z)
        for y in YEARS:
            rows.append({'variant':v,'year':y,**metrics(z[z.year==y])})
        rows.append({'variant':v,'year':'pooled',**metrics(z)})
    full=select(events,'full_candidate').copy();rev=full.copy();rev['gross_bp']=-rev.gross_bp
    for y in YEARS: rows.append({'variant':'reverse_full_candidate','year':y,**metrics(rev[rev.year==y])})
    rows.append({'variant':'reverse_full_candidate','year':'pooled',**metrics(rev)})
    out.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(out/'ablation_summary.csv',index=False);pd.concat(trade_frames,ignore_index=True).to_csv(out/'ablation_trades.csv',index=False)
    s={'schema':'csi1000_long_accel_validation_diag_v1','validation_start':START,'validation_end':END,'blackbox_queried':False,'variants':list(variants)+['reverse_full_candidate']};(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s))

def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
