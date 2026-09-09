from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
V3_RUNNER=HERE.parent/'highvol_recovery_hazard_v3'/'run_hazard.py'
DEV_YEARS=(2021,2022,2023)
NORMAL_HORIZONS=(3,6,12)
RESH_HORIZONS=(3,6)


def load_v3():
    spec=importlib.util.spec_from_file_location('v3_frozen',V3_RUNNER)
    mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod); return mod


def outcome(day: pd.DataFrame, anchor: int, normal_end: int|None, h: int, field: str):
    last=int(day.index.max()); stop=anchor+h
    if normal_end is not None and normal_end<=stop:
        future=day.loc[anchor+1:normal_end-1] if normal_end>anchor+1 else day.iloc[0:0]
        if field=='normal': return True, True
        return True, bool(future.shock.fillna(False).astype(bool).any()) if len(future) else False
    if stop<=last:
        future=day.loc[anchor+1:stop]
        if field=='normal': return True, False
        return True, bool(future.shock.fillna(False).astype(bool).any())
    return False, None


def build_anchors(df: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for day_name,z0 in df.groupby('trading_day',sort=False):
        year=int(str(day_name)[:4])
        if year not in DEV_YEARS: continue
        day=z0.sort_values('timestamp',kind='stable').reset_index(drop=True)
        prev_unsafe=day.risk_state.shift(1).eq('UNSAFE').fillna(False)
        starts=list(day.index[day.shock.fillna(False).astype(bool)&~prev_unsafe])
        occupied=-1; eno=0
        for j in starts:
            j=int(j)
            if j<=occupied: continue
            normals=day.index[(day.index>j)&day.risk_state.eq('NORMAL')]
            end=int(normals[0]) if len(normals) else None
            occupied=(end-1) if end is not None else int(day.index.max())
            eno+=1
            pre=day.loc[j:(end-1 if end is not None else int(day.index.max()))]
            shocks=[int(i) for i in pre.index[pre.shock.fillna(False).astype(bool)] if int(i)>=j]
            recurrent=[i for i in shocks if i>j]
            anchors=[('INITIAL',j)]
            if recurrent: anchors.append(('FIRST_RECURRENT',recurrent[0]))
            for atype,a in anchors:
                row={'episode_id':f"{day.at[j,'symbol']}|{day_name}|{eno}",'symbol':str(day.at[j,'symbol']),'year':year,'trading_day':str(day_name),'anchor_type':atype,'anchor_row':a,'episode_age_bars':a-j,'episode_age_minutes':5*(a-j),'current_state':str(day.at[a,'risk_state']),'current_vol_ratio':float(day.at[a,'vol_ratio']) if pd.notna(day.at[a,'vol_ratio']) else np.nan,'normal_observed':end is not None,'bars_to_normal_after_anchor':(end-a) if end is not None else np.nan}
                for h in NORMAL_HORIZONS:
                    support,val=outcome(day,a,end,h,'normal'); row[f'normal_{h}b_supported']=support; row[f'normal_within_{h}b']=val
                for h in RESH_HORIZONS:
                    support,val=outcome(day,a,end,h,'reshock'); row[f'reshock_{h}b_supported']=support; row[f'reshock_before_normal_{h}b']=val
                rows.append(row)
    return pd.DataFrame(rows)


def frac_supported(g: pd.DataFrame, support_col: str, value_col: str):
    q=g[g[support_col].astype(bool)]
    return int(len(q)), float(q[value_col].astype(bool).mean()) if len(q) else np.nan


def summarize(anchors: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for symbol in anchors.symbol.unique():
        for atype in ('INITIAL','FIRST_RECURRENT'):
            base=anchors[(anchors.symbol==symbol)&(anchors.anchor_type==atype)]
            for year in ('pooled',*DEV_YEARS):
                g=base if year=='pooled' else base[base.year==int(year)]
                r={'symbol':symbol,'anchor_type':atype,'year':year,'anchors':int(len(g)),'median_episode_age_bars':float(g.episode_age_bars.median()) if len(g) else np.nan,'median_bars_to_normal':float(g.bars_to_normal_after_anchor.dropna().median()) if g.bars_to_normal_after_anchor.notna().any() else np.nan}
                for h in NORMAL_HORIZONS:
                    n,p=frac_supported(g,f'normal_{h}b_supported',f'normal_within_{h}b'); r[f'normal_{h}b_n']=n; r[f'normal_{h}b_prob']=p
                for h in RESH_HORIZONS:
                    n,p=frac_supported(g,f'reshock_{h}b_supported',f'reshock_before_normal_{h}b'); r[f'reshock_{h}b_n']=n; r[f'reshock_{h}b_prob']=p
                rows.append(r)
    return pd.DataFrame(rows)


def differences(summary: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    fields=[*(f'normal_{h}b_prob' for h in NORMAL_HORIZONS),*(f'reshock_{h}b_prob' for h in RESH_HORIZONS),'median_bars_to_normal']
    for symbol in summary.symbol.unique():
        for year in ('pooled',*DEV_YEARS):
            q=summary[(summary.symbol==symbol)&(summary.year.astype(str)==str(year))].set_index('anchor_type')
            if not {'INITIAL','FIRST_RECURRENT'}.issubset(q.index): continue
            for field in fields:
                a=q.at['INITIAL',field]; b=q.at['FIRST_RECURRENT',field]
                rows.append({'symbol':symbol,'year':year,'metric':field,'first_recurrent_minus_initial':float(b-a) if pd.notna(a) and pd.notna(b) else np.nan})
    return pd.DataFrame(rows)


def clean_records(df):
    out=[]
    for r in df.to_dict(orient='records'):
        out.append({k:(None if isinstance(v,(float,np.floating)) and not np.isfinite(v) else int(v) if isinstance(v,np.integer) else float(v) if isinstance(v,np.floating) else v) for k,v in r.items()})
    return out


def run(root: Path,out: Path):
    v3=load_v3(); frames=v3.restrict_common_days({s:v3.load_symbol(root,s) for s in v3.SYMBOLS}); frames={s:v3.add_measurements(x) for s,x in frames.items()}
    anchors=pd.concat([build_anchors(frames[s]) for s in v3.SYMBOLS],ignore_index=True)
    summary=summarize(anchors); diffs=differences(summary)
    recurrent=anchors[anchors.anchor_type=='FIRST_RECURRENT']
    diag={}
    for symbol in v3.SYMBOLS:
        q=recurrent[recurrent.symbol==symbol]
        diag[symbol]={'episodes_with_first_recurrent':int(len(q)),'median_bars_to_first_recurrence':float(q.episode_age_bars.median()) if len(q) else None,'p90_bars_to_first_recurrence':float(q.episode_age_bars.quantile(.9)) if len(q) else None}
    summary_json={'schema':'highvol_reshock_cluster_v5_dev','development_only':True,'state_thresholds_unchanged':True,'pnl_computed':False,'trading_rule_created':False,'validation_queried':False,'blackbox_queried':False,'production_authority':False,'anchor_counts':{s:{'initial':int(((anchors.symbol==s)&(anchors.anchor_type=='INITIAL')).sum()),'first_recurrent':int(((anchors.symbol==s)&(anchors.anchor_type=='FIRST_RECURRENT')).sum())} for s in v3.SYMBOLS},'first_recurrence_timing':diag,'summary':clean_records(summary),'differences':clean_records(diffs)}
    out.mkdir(parents=True,exist_ok=True); anchors.to_csv(out/'anchor_ledger.csv',index=False); summary.to_csv(out/'anchor_summary.csv',index=False); diffs.to_csv(out/'anchor_differences.csv',index=False); (out/'summary.json').write_text(json.dumps(summary_json,indent=2,allow_nan=False)+'\n'); print(json.dumps(summary_json,allow_nan=False)); return summary_json


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=='__main__': main()
