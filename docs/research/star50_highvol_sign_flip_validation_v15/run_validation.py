from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

START='2024-01-01'
END='2026-08-21'
YEARS=(2024,2025,2026)
SYMBOL='000688.SH'
CANDIDATE_ID='star50_v15_up_to_down_continuation_3m'
CANDIDATE_CODE_SHA='285a429d96dd7c92afce86d4859f111ae9b8961d'
CONFIG_SHA256='7053f5000ff0d04da62a82781a86c5f518cb135396d88a9d178fd95cf41cf704'
COST_BP_PER_LEG=1.0
MIN_YEAR_N=15
GROSS_BREAK_EVEN_BP=2.0


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_validation_minute(root:Path)->pd.DataFrame:
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','v15val_reg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','v15val_orig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','v15val_fg')
    native=orig.load_native(root,SYMBOL).copy()
    native['trading_day']=native.trading_day.astype(str).str[:10]
    native=native[(native.trading_day>=START)&(native.trading_day<=END)].copy()
    if native.empty:
        raise RuntimeError('no validation rows')
    assert native.trading_day.min()>=START and native.trading_day.max()<=END
    state=reg.build_continuous_state(native,SYMBOL)
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),SYMBOL).reset_index(drop=True)
    minute['trading_day']=minute.trading_day.astype(str).str[:10]
    return minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)


def run(root:Path,out:Path):
    frozen=load_module(root/'docs/research/star50_highvol_sign_flip_dev_v15/run_highvol_sign_flip.py','v15_frozen_candidate')
    minute=build_validation_minute(root)
    events,raw_flips=frozen.build_events(minute)
    candidate=events[events.flip_type=='UpToDown'].copy().reset_index(drop=True)
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
        'schema':'star50_highvol_sign_flip_validation_v15',
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
        'primary_endpoint':'mean new-direction continuation over 3 minutes, bp',
        'acceptance_rule':f'each 2024, 2025, 2026-through-{END}: n>={MIN_YEAR_N} and mean_continuation_3m_bp>{GROSS_BREAK_EVEN_BP}',
        'raw_flip_count':int(raw_flips),
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
