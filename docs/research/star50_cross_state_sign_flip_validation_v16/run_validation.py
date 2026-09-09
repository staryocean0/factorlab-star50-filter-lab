from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

START='2024-01-01'
END='2026-08-21'
YEARS=(2024,2025,2026)
STAR='000688.SH'
CSI='000852.SH'
CANDIDATE_ID='star50_v16_up_to_down_csi_normal_continuation_3m'
CANDIDATE_CODE_SHA='358430c30a207e083e04e7cdfd8215aee8711411'
CONFIG_SHA256='a36b5998653a526f4b1eba8f4b5c71efa7474597006c86c0a0b6d6ac37095a9c'
MIN_YEAR_N=15
GROSS_BREAK_EVEN_BP=2.0


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_minute(root:Path,symbol:str)->pd.DataFrame:
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py',f'v16val_reg_{symbol.replace(".","_")}')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py',f'v16val_orig_{symbol.replace(".","_")}')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py',f'v16val_fg_{symbol.replace(".","_")}')
    native=orig.load_native(root,symbol).copy()
    native['trading_day']=native.trading_day.astype(str).str[:10]
    native=native[(native.trading_day>=START)&(native.trading_day<=END)].copy()
    if native.empty:
        raise RuntimeError(f'no Validation rows for {symbol}')
    assert native.trading_day.min()>=START and native.trading_day.max()<=END
    state=reg.build_continuous_state(native,symbol)
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),symbol).reset_index(drop=True)
    minute['trading_day']=minute.trading_day.astype(str).str[:10]
    return minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)


def run(root:Path,out:Path):
    frozen=load_module(root/'docs/research/star50_highvol_sign_flip_dev_v15/run_highvol_sign_flip.py','v16val_v15')
    star=build_minute(root,STAR)
    csi=build_minute(root,CSI)
    events,raw_flips=frozen.build_events(star)
    events=events[events.flip_type=='UpToDown'].copy()
    cstate=csi[['session','minute','route_state']].rename(columns={'route_state':'csi_route_state'})
    if cstate.duplicated(['session','minute']).any():
        raise RuntimeError('duplicate CSI state key')
    events=events.merge(cstate,on=['session','minute'],how='left',validate='many_to_one')
    candidate=events[events.csi_route_state=='NormalVol'].copy().reset_index(drop=True)
    rows=[]
    annual=[]
    for year in YEARS:
        q=frozen.stats(candidate[candidate.year==year])
        annual.append(q)
        rows.append({'year':year,**q})
    pooled=frozen.stats(candidate)
    rows.append({'year':'pooled',**pooled})
    annual_df=pd.DataFrame(annual,index=YEARS)
    year_passes={
        str(year): bool(annual_df.loc[year,'n']>=MIN_YEAR_N and annual_df.loc[year,'mean_continuation_3m_bp']>GROSS_BREAK_EVEN_BP)
        for year in YEARS
    }
    validation_pass=bool(all(year_passes.values()))
    summary={
        'schema':'star50_cross_state_sign_flip_validation_v16',
        'candidate_id':CANDIDATE_ID,
        'candidate_code_commit_sha':CANDIDATE_CODE_SHA,
        'config_sha256':CONFIG_SHA256,
        'candidate_nominated':True,
        'development_frozen':True,
        'validation_queried':True,
        'validation_date_start':START,
        'validation_date_end':END,
        'blackbox_queried':False,
        'production_authority':False,
        'primary_endpoint':'mean new-down-direction continuation over 3 minutes, bp',
        'acceptance_rule':f'each 2024, 2025, 2026-through-{END}: n>={MIN_YEAR_N} and mean_continuation_3m_bp>{GROSS_BREAK_EVEN_BP}',
        'raw_star_flip_count':int(raw_flips),
        'candidate_event_count':int(len(candidate)),
        'year_passes':year_passes,
        'validation_pass':validation_pass,
        'verdict':'VALIDATION_PASS' if validation_pass else 'VALIDATION_REJECT'
    }
    out.mkdir(parents=True,exist_ok=True)
    candidate.to_csv(out/'candidate_events.csv',index=False)
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
