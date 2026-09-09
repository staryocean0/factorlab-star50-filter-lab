from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

START='2024-01-01'
END='2026-08-21'
YEARS=(2024,2025,2026)
SYMBOL='000688.SH'
CANDIDATE_ID='star50_v17_first_up_to_down_highvol_episode_continuation_3m'
CANDIDATE_CODE_SHA='5c0c173a58466ea9423750252606d6458b4fcf64'
CONFIG_SHA256='ba7232e4c08559486fe732c72934a4970e5d1eaae6814fa20124efdbced154de'
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
    reg=load_module(root/'docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py','v17val_reg')
    orig=load_module(root/'docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py','v17val_orig')
    fg=load_module(root/'docs/research/state_conditioned_frequency_v2/code/fast_grid.py','v17val_fg')
    native=orig.load_native(root,SYMBOL).copy()
    native['trading_day']=native.trading_day.astype(str).str[:10]
    native=native[(native.trading_day>=START)&(native.trading_day<=END)].copy()
    if native.empty:
        raise RuntimeError('no Validation rows')
    assert native.trading_day.min()>=START and native.trading_day.max()<=END
    state=reg.build_continuous_state(native,SYMBOL)
    minute=fg.build_minute_grid(native,state.rename(columns={'vol_ratio':'recovery_ratio'}),SYMBOL).reset_index(drop=True)
    minute['trading_day']=minute.trading_day.astype(str).str[:10]
    return minute[(minute.trading_day>=START)&(minute.trading_day<=END)].reset_index(drop=True)


def run(root:Path,out:Path):
    v15=load_module(root/'docs/research/star50_highvol_sign_flip_dev_v15/run_highvol_sign_flip.py','v17val_v15')
    v17=load_module(root/'docs/research/star50_highvol_flip_ordinal_dev_v17/run_flip_ordinal.py','v17val_v17')
    minute=build_validation_minute(root)
    events,raw=v17.build_events(minute)
    candidate=events[events.ordinal_state=='FirstUpToDown'].copy().reset_index(drop=True)
    rows=[]
    annual=[]
    for year in YEARS:
        q=v15.stats(candidate[candidate.year==year])
        annual.append(q)
        rows.append({'year':year,**q})
    rows.append({'year':'pooled',**v15.stats(candidate)})
    annual_df=pd.DataFrame(annual,index=YEARS)
    year_passes={str(year): bool(annual_df.loc[year,'n']>=MIN_YEAR_N and annual_df.loc[year,'mean_continuation_3m_bp']>GROSS_BREAK_EVEN_BP) for year in YEARS}
    validation_pass=bool(all(year_passes.values()))
    summary={
        'schema':'star50_highvol_flip_ordinal_validation_v17',
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
        'raw_up_to_down_flip_count':int(raw),
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
