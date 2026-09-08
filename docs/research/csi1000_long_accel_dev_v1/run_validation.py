from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd

START='2024-01-01'; END='2026-08-21'; YEARS=(2024,2025,2026); COSTS=(0.5,1.0,1.5,2.0)

def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def metrics(z):
    n=len(z); mean=float(z.gross_bp.mean()) if n else np.nan
    q={'trades':n,'mean_gross_bp':mean,'hit_rate':float((z.gross_bp>0).mean()) if n else np.nan,'one_way_break_even_bp':mean/2 if n else np.nan}
    for c in COSTS:q[f'mean_net_{c:g}bp_per_leg']=mean-2*c if n else np.nan
    return q

def run(root,out):
    dev=load_module(root/'docs/research/csi1000_long_accel_dev_v1/run_dev_search.py','devv');reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','regv');orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','origv');fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','fgv')
    native=orig.load_native(root,'000852.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,'000852.SH');minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000852.SH').reset_index(drop=True);minute=minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)
    events=dev.build_events(minute);sel=dev.select(events,30,.60,.60,3).copy();sel['gross_bp']=sel['gross_3m_bp']
    annual=[]
    for y in YEARS:q=metrics(sel[sel.year==y]);q['year']=y;annual.append(q)
    annual=pd.DataFrame(annual);pooled=metrics(sel); positive=int((annual['mean_net_1bp_per_leg']>0).sum())
    accept={'trades_ge_30':bool(pooled['trades']>=30),'pooled_net1_positive':bool(pooled['mean_net_1bp_per_leg']>0 if pooled['trades'] else False),'two_of_three_slices_net1_positive':bool(positive>=2),'break_even_gt_1bp':bool(pooled['one_way_break_even_bp']>1 if pooled['trades'] else False)};accept['all_primary_pass']=bool(all(accept.values()))
    out.mkdir(parents=True,exist_ok=True);sel.to_csv(out/'validation_trades.csv',index=False);annual.to_csv(out/'annual_validation.csv',index=False);pd.DataFrame([pooled]).to_csv(out/'pooled_validation.csv',index=False)
    s={'schema':'csi1000_long_accel_v1_validation','candidate':{'slow_window':30,'tail2_min':.60,'tail1_cap':.60,'hold_min':3,'direction':'long'},'validation_start':START,'validation_end':END,'blackbox_queried':False,'positive_slices':positive,'pooled':pooled,'acceptance':accept};(out/'summary.json').write_text(json.dumps(s,indent=2,default=str)+'\n');print(json.dumps(s,default=str))

def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
