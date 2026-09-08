from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2024-01-01'
END='2026-08-21'


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def build_minute(root:Path,symbol:str)->pd.DataFrame:
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py',f'cross_reg_{symbol}')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py',f'cross_orig_{symbol}')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py',f'cross_fg_{symbol}')
    native=orig.load_native(root,symbol).copy()
    native['trading_day']=native.trading_day.astype(str).str[:10]
    native=native[(native.trading_day>=START)&(native.trading_day<=END)].copy()
    assert len(native)
    state=reg.build_continuous_state(native,symbol)
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),symbol).reset_index(drop=True)
    return minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)


def add_recent_context(minute:pd.DataFrame,prefix:str)->pd.DataFrame:
    rows=[]
    for session,z0 in minute.groupby('session',sort=False):
        z=z0.sort_values('minute').reset_index(drop=True)
        p=np.log(pd.to_numeric(z.close,errors='coerce').to_numpy(float))
        r=np.diff(p,prepend=np.nan)*1e4
        valid=z.valid.to_numpy(bool)
        for i in range(len(z)):
            net5=np.nan;slow30=np.nan
            if i>=34 and valid[i-34:i+1].all() and np.isfinite(r[i-34:i+1]).all():
                net5=float(r[i-4:i+1].sum())
                slow30=float(r[i-34:i-4].sum())
            rows.append({
                'session':session,'onset_minute':int(z.loc[i,'minute']),
                f'{prefix}_net5_bp':net5,f'{prefix}_slow30_bp':slow30,
                f'{prefix}_state':str(z.loc[i,'route_state']),
                f'{prefix}_vol_ratio':float(z.loc[i,'recovery_ratio']) if np.isfinite(z.loc[i,'recovery_ratio']) else np.nan,
            })
    return pd.DataFrame(rows)


def metrics(z:pd.DataFrame)->dict:
    g=pd.to_numeric(z.signed_3m_bp,errors='coerce').dropna()
    return {'n':int(len(g)),'mean_gross_3m_bp':float(g.mean()) if len(g) else np.nan,
            'mean_net_1bp_per_leg':float(g.mean()-2.0) if len(g) else np.nan,
            'median_gross_3m_bp':float(g.median()) if len(g) else np.nan,
            'hit_rate':float((g>0).mean()) if len(g) else np.nan}


def summarize(name:str,z:pd.DataFrame)->list[dict]:
    rows=[]
    for year in (2024,2025,2026):
        rows.append({'subset':name,'year':year,**metrics(z[z.year.eq(year)])})
    rows.append({'subset':name,'year':'pooled',**metrics(z)})
    return rows


def run(root:Path,out:Path)->None:
    dev=load_module(root/'docs/research/star50_down_regime_break_v2/run_dev.py','cross_dev')
    mech=load_module(root/'docs/research/star50_highvol_mechanism_dev_v1/run_mechanism.py','cross_mech')
    star=build_minute(root,'000688.SH')
    csi=build_minute(root,'000852.SH')
    events=mech.build_events(star)
    selected=dev.select(events)
    cross=add_recent_context(csi,'csi1000')
    z=selected.merge(cross,on=['session','onset_minute'],how='left',validate='many_to_one')
    valid=np.isfinite(pd.to_numeric(z.csi1000_net5_bp,errors='coerce'))
    fast_down=valid&(z.csi1000_net5_bp<0)
    fast_up=valid&(z.csi1000_net5_bp>0)
    high=z.csi1000_state.eq('HighVol')
    slow_up=np.isfinite(pd.to_numeric(z.csi1000_slow30_bp,errors='coerce'))&(z.csi1000_slow30_bp>0)
    subsets={
        'v2_all':pd.Series(True,index=z.index),
        'csi1000_fast5_down':fast_down,
        'csi1000_fast5_up':fast_up,
        'csi1000_highvol':high,
        'csi1000_fast5_down_and_highvol':fast_down&high,
        'both_indices_slow_up_fast_down_break':fast_down&slow_up,
        'csi1000_not_fast_down':~fast_down,
    }
    rows=[]
    for name,mask in subsets.items():rows.extend(summarize(name,z.loc[mask].copy()))
    out.mkdir(parents=True,exist_ok=True)
    z.to_csv(out/'v2_trades_with_csi1000_context.csv',index=False)
    pd.DataFrame(rows).to_csv(out/'subset_summary.csv',index=False)
    meta={'schema':'star50_v2_cross_index_confirmation_diag_v1','role':'reusable_validation_diagnostic',
          'start':START,'end':END,'diagnostic_only':True,'candidate_validation_claim':False,'blackbox_queried':False}
    (out/'summary.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(pd.DataFrame(rows).to_csv(index=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo-root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    run(Path(a.repo_root).resolve(),Path(a.out).resolve())

if __name__=='__main__':main()
