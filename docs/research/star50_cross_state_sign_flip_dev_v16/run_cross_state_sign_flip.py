from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

START='2021-01-01'
END='2023-12-31'
YEARS=(2021,2022,2023)
STAR='000688.SH'
CSI='000852.SH'
VIEWS=('all','CSIHighVol','CSINormalVol')


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_minute(root:Path,symbol:str)->pd.DataFrame:
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py',f'v16reg_{symbol.replace(".","_")}')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py',f'v16orig_{symbol.replace(".","_")}')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py',f'v16fg_{symbol.replace(".","_")}')
    native=orig.load_native(root,symbol).copy()
    native['trading_day']=native.trading_day.astype(str).str[:10]
    native=native[(native.trading_day>=START)&(native.trading_day<=END)].copy()
    if native.empty:
        raise RuntimeError(f'no Development rows for {symbol}')
    state=reg.build_continuous_state(native,symbol)
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),symbol).reset_index(drop=True)
    minute['trading_day']=minute.trading_day.astype(str).str[:10]
    return minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)


def run(root:Path,out:Path):
    frozen=load_module(root/'docs/research/star50_highvol_sign_flip_dev_v15/run_highvol_sign_flip.py','v16_frozen_v15')
    star=build_minute(root,STAR)
    csi=build_minute(root,CSI)
    events,raw_flips=frozen.build_events(star)
    events=events[events.flip_type=='UpToDown'].copy()
    cstate=csi[['session','minute','route_state']].rename(columns={'route_state':'csi_route_state'})
    if cstate.duplicated(['session','minute']).any():
        raise RuntimeError('duplicate CSI state key')
    events=events.merge(cstate,on=['session','minute'],how='left',validate='many_to_one')
    events=events[events.csi_route_state.isin(['HighVol','NormalVol'])].copy().reset_index(drop=True)
    events['cross_state']=events.csi_route_state.map({'HighVol':'CSIHighVol','NormalVol':'CSINormalVol'})
    rows=[]
    promising=[]
    for view in VIEWS:
        z=events if view=='all' else events[events.cross_state==view]
        annual=[]
        for year in YEARS:
            q=frozen.stats(z[z.year==year])
            annual.append(q)
            rows.append({'view':view,'year':year,**q})
        rows.append({'view':view,'year':'pooled',**frozen.stats(z)})
        a=pd.DataFrame(annual)
        if len(a)==3 and bool((a.n>=15).all()) and bool((a.mean_continuation_3m_bp>2.0).all()):
            promising.append({'view':view,'direction':'new_down_direction_continuation'})
    summary={
        'schema':'star50_cross_state_sign_flip_dev_v16',
        'development_only':True,
        'validation_queried':False,
        'blackbox_queried':False,
        'candidate_nominated':False,
        'star_symbol':STAR,
        'cross_symbol':CSI,
        'views':list(VIEWS),
        'raw_star_flip_count':int(raw_flips),
        'star_up_to_down_count':int((events.flip_type=='UpToDown').sum()),
        'event_count':int(len(events)),
        'cross_state_counts':{str(k):int(v) for k,v in events.cross_state.value_counts().to_dict().items()},
        'mechanism_promising_views':promising
    }
    out.mkdir(parents=True,exist_ok=True)
    events.to_csv(out/'events.csv',index=False)
    pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
    print(pd.DataFrame(rows).to_csv(index=False))
    return summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=='__main__':
    main()
