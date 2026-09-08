from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import pandas as pd

START='2024-01-01';END='2026-08-21';YEARS=(2024,2025,2026);HORIZONS=(1,2,3,5,10)

def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def run(root,out):
    mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','vmech')
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','vreg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','vorig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','vfg')
    native=orig.load_native(root,'000688.SH').copy();native['trading_day']=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=reg.build_continuous_state(native,'000688.SH');minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),'000688.SH').reset_index(drop=True)
    minute=minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)
    events=mech.build_events(minute);events['all']='all';cube=['direction','slow_aligned','accel_high','efficient_high']
    summary=[];summary+=mech.agg(events,['all'],'all');summary+=mech.agg(events,['direction'],'direction');summary+=mech.agg(events,['direction','slow_aligned'],'direction_x_slow');summary+=mech.agg(events,['direction','accel_high'],'direction_x_accel');summary+=mech.agg(events,['direction','efficient_high'],'direction_x_efficiency');summary+=mech.agg(events,cube,'full_cube')
    annual=[]
    for y in YEARS:
        e=events[events.year==y];annual+=mech.agg(e,['all'],f'year_{y}_all');annual+=mech.agg(e,cube,f'year_{y}_cube')
    # Load frozen Development mechanism artifact logic by recomputing Development through same module.
    dminute=mech.build_minute(root);dev=mech.build_events(dminute);dev['role']='Development';events2=events.drop(columns=['all']).copy();events2['role']='Validation'
    cmp=[]
    for role,z in [('Development',dev),('Validation',events2)]:
      for keys,g in z.groupby(cube,dropna=False,sort=True):
        base={'role':role,**dict(zip(cube,keys))}
        for h in (3,5):
          q=pd.to_numeric(g[f'signed_{h}m_bp'],errors='coerce').dropna();cmp.append({**base,'horizon_min':h,'n':len(q),'mean_signed_bp':float(q.mean()) if len(q) else None,'hit':float((q>0).mean()) if len(q) else None})
    out.mkdir(parents=True,exist_ok=True);events.drop(columns=['all']).to_csv(out/'validation_events.csv',index=False);pd.DataFrame(summary).to_csv(out/'validation_summary.csv',index=False);pd.DataFrame(annual).to_csv(out/'validation_annual.csv',index=False);pd.DataFrame(cmp).to_csv(out/'dev_validation_cube.csv',index=False)
    meta={'schema':'star50_highvol_mechanism_validation_diag_v1','validation_start':START,'validation_end':END,'event_count':len(events),'blackbox_queried':False,'candidate_nominated':False}
    (out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))

def main():
    a=argparse.ArgumentParser();a.add_argument('--repo-root',required=True);a.add_argument('--out',required=True);x=a.parse_args();run(Path(x.repo_root).resolve(),Path(x.out))
if __name__=='__main__':main()
