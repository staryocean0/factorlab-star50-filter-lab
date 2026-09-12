#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, os, sys
from pathlib import Path
import numpy as np
import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
M3_ORDER=["<=0","(0,1]","(1,2]",">2"]


def load_parent(root: Path):
    path=root/'docs/research/fine_activity_future_risk_v1/run_study.py'
    spec=importlib.util.spec_from_file_location('parent_v1',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def prepare_dev(root: Path, p):
    sys.path.insert(0,str(root/'src'))
    from star50_filter.cloud_market_data import load_market_data
    panels=[]; fines=[]
    for symbol in SYMBOLS:
        native=load_market_data(symbol,'1m',p.WARMUP_START,p.DEV_END,root=root)
        panel=p.minute_panel(native,symbol)
        panels.append(panel); fines.append(p.build_fine(root,panel,symbol))
    panel=pd.concat(panels,ignore_index=True)
    fine=pd.concat(fines,ignore_index=True)
    target=p.attach_future_targets(panel)
    keys=['symbol','session','day','afternoon','minute']
    frame=target.merge(fine,on=keys,how='inner',validate='one_to_one')
    frame=p.attach_clock_z(frame,'A5','M3')
    frame=p.attach_clock_z(frame,'rms1m5','C1z')
    frame['M4']=frame.M3+frame.M1
    day=pd.to_datetime(frame.day)
    eligible=((day>=pd.Timestamp(p.DEV_START))&(day<=pd.Timestamp(p.DEV_END))
              &frame.fine_complete5&(frame.pre5m_range_bp<p.RANGE_BP)
              &frame.minute.between(35,105)&np.isfinite(frame.M3)
              &np.isfinite(frame.current_vol_ratio)&np.isfinite(frame.future_rms15_bp)
              &np.isfinite(frame.future_mean_abs15_bp)&np.isfinite(frame.future_any_unsafe15))
    dev=frame.loc[eligible].copy()
    dev['current_state']=np.where(dev.current_vol_ratio>=1.5,'Unsafe','NonUnsafe')
    dev['m3_band']=dev.M3.map(p.band_label)
    return dev


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[3]); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    p=load_parent(root); dev=prepare_dev(root,p)
    rows=[]
    for symbol in SYMBOLS:
        for state in ('NonUnsafe','Unsafe'):
            s=dev[(dev.symbol==symbol)&(dev.current_state==state)]
            for band in M3_ORDER:
                z=s[s.m3_band==band]
                rows.append({'symbol':symbol,'current_state':state,'m3_band':band,'n':int(len(z)),
                    'median_future_rms15_bp':float(z.future_rms15_bp.median()) if len(z) else None,
                    'mean_future_rms15_bp':float(z.future_rms15_bp.mean()) if len(z) else None,
                    'mean_future_abs15_bp':float(z.future_mean_abs15_bp.mean()) if len(z) else None,
                    'future_any_unsafe15_prob':float(z.future_any_unsafe15.mean()) if len(z) else None,
                    'median_current_vol_ratio':float(z.current_vol_ratio.median()) if len(z) else None})
    cube=pd.DataFrame(rows)
    pooled=dev.groupby(['symbol','current_state']).agg(n=('M3','size'),median_future_rms15_bp=('future_rms15_bp','median'),future_any_unsafe15_prob=('future_any_unsafe15','mean'),median_current_vol_ratio=('current_vol_ratio','median')).reset_index()
    checks={}
    for symbol in SYMBOLS:
        amp={}
        for state in ('NonUnsafe','Unsafe'):
            s=cube[(cube.symbol==symbol)&(cube.current_state==state)].set_index('m3_band').loc[M3_ORDER]
            amp[state]={'bottom_n_ge_100':bool(s.loc['<=0','n']>=100),'top_n_ge_30':bool(s.loc['>2','n']>=30),'top_bottom_rms_ratio_ge_1_10':bool(s.loc['>2','median_future_rms15_bp']/s.loc['<=0','median_future_rms15_bp']>=1.10)}
        amplitude_present=all(all(v.values()) for v in amp.values())
        q=pooled[pooled.symbol==symbol].set_index('current_state')
        delta=float(q.loc['Unsafe','future_any_unsafe15_prob']-q.loc['NonUnsafe','future_any_unsafe15_prob'])
        persistence={'both_state_n_ge_500':bool((q.n>=500).all()),'unsafe_minus_nonunsafe_ge_30pp':bool(delta>=0.30),'unsafe_minus_nonunsafe_pp':delta*100}
        checks[symbol]={'amplitude_axis':amp,'amplitude_axis_present':amplitude_present,'state_persistence_axis':persistence,'state_persistence_axis_present':bool(persistence['both_state_n_ge_500'] and persistence['unsafe_minus_nonunsafe_ge_30pp'])}
    verdict='two_axis_decomposition_descriptively_consistent' if all(v['amplitude_axis_present'] and v['state_persistence_axis_present'] for v in checks.values()) else 'two_axis_decomposition_not_consistent'
    cube.to_csv(out/'risk_coordinate_cube.csv',index=False); pooled.to_csv(out/'pooled_state_summary.csv',index=False)
    summary={'schema':'risk_coordinate_decomposition_v1','development_rows':int(len(dev)),'verdict':verdict,'checks':checks,'validation_queried':False,'blackbox_queried':False,'fresh_oos':False,'returns_or_pnl_evaluated':False,'candidate_nominated':False,'production_authority':False,'git_sha':os.getenv('GITHUB_SHA'),'run_id':os.getenv('GITHUB_RUN_ID')}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2)); print(cube.to_string(index=False)); print(pooled.to_string(index=False))

if __name__=='__main__': main()
