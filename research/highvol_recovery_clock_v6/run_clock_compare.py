from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
V3_RUNNER=HERE.parent/'highvol_recovery_hazard_v3'/'run_hazard.py'
YEARS=(2021,2022,2023)
STATES=('UNSAFE','RECOVERING')
BUCKETS=('LT15','M15_25','M30_40','GE45')
MIN_CELL_N=100


def load_v3():
    spec=importlib.util.spec_from_file_location('v3_clock',V3_RUNNER); m=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(m); return m


def age_bucket(bars:int)->str:
    if bars<=2: return 'LT15'
    if bars<=5: return 'M15_25'
    if bars<=8: return 'M30_40'
    return 'GE45'


def build_rows(df:pd.DataFrame,v3)->pd.DataFrame:
    rows=[]
    for day_name,z0 in df.groupby('trading_day',sort=False):
        year=int(str(day_name)[:4])
        if year not in YEARS: continue
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
            eno+=1; last_shock=j
            last_active=(end-1) if end is not None else int(day.index.max())
            for k in range(j+1,last_active+1):
                if bool(day.at[k,'shock']) if pd.notna(day.at[k,'shock']) else False:
                    last_shock=k
                    continue
                state=str(day.at[k,'risk_state'])
                if state not in STATES: continue
                f=v3._future_outcome(day,k)
                if not f['hazard_supported']: continue
                ea=k-j; ra=k-last_shock
                if ra<=0: continue
                rows.append({'episode_id':f"{day.at[j,'symbol']}|{day_name}|{eno}",'symbol':str(day.at[j,'symbol']),'year':year,'trading_day':str(day_name),'current_state':state,'episode_age_bars':ea,'recent_shock_age_bars':ra,'episode_age_bucket':age_bucket(ea),'recent_shock_age_bucket':age_bucket(ra),'normal_within_next15':bool(f['normal_within_next15']),'current_vol_ratio':float(day.at[k,'vol_ratio']) if pd.notna(day.at[k,'vol_ratio']) else np.nan})
    return pd.DataFrame(rows)


def fit_table(train:pd.DataFrame,bucket_col:str)->pd.DataFrame:
    rows=[]
    for state in STATES:
        for b in BUCKETS:
            g=train[(train.current_state==state)&(train[bucket_col]==b)]
            n=len(g)
            if n==0: raise RuntimeError(f'missing cell {bucket_col} {state} {b}')
            s=int(g.normal_within_next15.sum()); p=(s+1)/(n+2)
            rows.append({'current_state':state,'age_bucket':b,'n':int(n),'successes':s,'probability':float(p)})
    return pd.DataFrame(rows)


def predict(test:pd.DataFrame,table:pd.DataFrame,bucket_col:str)->np.ndarray:
    mp={(r.current_state,r.age_bucket):r.probability for r in table.itertuples()}
    return np.array([mp[(s,b)] for s,b in zip(test.current_state,test[bucket_col])],float)


def score(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float); q=np.clip(p,1e-12,1-1e-12)
    return {'n':int(len(y)),'brier':float(np.mean((p-y)**2)),'log_loss':float(-np.mean(y*np.log(q)+(1-y)*np.log(1-q))),'observed_rate':float(np.mean(y)),'mean_prediction':float(np.mean(p))}


def cv(rows:pd.DataFrame):
    out=[]; symbol_out=[]
    for hold in YEARS:
        tr=rows[rows.year!=hold]; te=rows[rows.year==hold]
        ep=fit_table(tr,'episode_age_bucket'); rc=fit_table(tr,'recent_shock_age_bucket')
        y=te.normal_within_next15.astype(int).to_numpy(); pe=predict(te,ep,'episode_age_bucket'); pr=predict(te,rc,'recent_shock_age_bucket')
        out.append({'held_out_year':hold,'episode_clock':score(y,pe),'recent_shock_clock':score(y,pr),'brier_improvement':float(score(y,pe)['brier']-score(y,pr)['brier']),'logloss_improvement':float(score(y,pe)['log_loss']-score(y,pr)['log_loss'])})
        for symbol in rows.symbol.unique():
            mask=te.symbol.eq(symbol).to_numpy(); yy=y[mask]
            symbol_out.append({'held_out_year':hold,'symbol':symbol,'episode_clock':score(yy,pe[mask]),'recent_shock_clock':score(yy,pr[mask])})
    return out,symbol_out


def clean(v):
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,list): return [clean(x) for x in v]
    if isinstance(v,(float,np.floating)) and not np.isfinite(v): return None
    if isinstance(v,np.integer): return int(v)
    if isinstance(v,np.floating): return float(v)
    return v


def run(root:Path,out:Path):
    v3=load_v3(); frames=v3.restrict_common_days({s:v3.load_symbol(root,s) for s in v3.SYMBOLS}); frames={s:v3.add_measurements(x) for s,x in frames.items()}
    rows=pd.concat([build_rows(frames[s],v3) for s in v3.SYMBOLS],ignore_index=True)
    cv_rows,symbol_cv=cv(rows)
    final=fit_table(rows,'recent_shock_age_bucket')
    idx=final.set_index(['age_bucket','current_state'])
    ordering=[]
    for b in BUCKETS:
        pu=float(idx.at[(b,'UNSAFE'),'probability']); pr=float(idx.at[(b,'RECOVERING'),'probability']); ordering.append({'age_bucket':b,'unsafe_probability':pu,'recovering_probability':pr,'gap':pr-pu,'ordered':bool(pr>pu)})
    acceptance={'recent_clock_brier_better_all_3_years':bool(all(r['brier_improvement']>0 for r in cv_rows)),'recent_clock_logloss_better_at_least_2_of_3':bool(sum(r['logloss_improvement']>0 for r in cv_rows)>=2),'all_8_final_cells_n_ge_100':bool((final.n>=MIN_CELL_N).all()),'recovering_gt_unsafe_all_4_buckets':bool(all(r['ordered'] for r in ordering)),'state_thresholds_unchanged':True,'validation_queried_false':True,'blackbox_queried_false':True}
    summary={'schema':'highvol_recovery_clock_v6_dev','development_only':True,'row_count':int(len(rows)),'state_thresholds_unchanged':True,'pnl_computed':False,'trading_rule_created':False,'validation_queried':False,'blackbox_queried':False,'production_authority':False,'age_buckets':list(BUCKETS),'leave_one_year_out':cv_rows,'symbol_cv':symbol_cv,'final_recent_shock_table':final.to_dict(orient='records'),'final_ordering':ordering,'acceptance':acceptance,'recent_shock_clock_candidate_eligible':bool(all(acceptance.values()))}
    out.mkdir(parents=True,exist_ok=True); rows.to_csv(out/'clock_rows.csv',index=False); final.to_csv(out/'final_recent_shock_table.csv',index=False); (out/'summary.json').write_text(json.dumps(clean(summary),indent=2,allow_nan=False)+'\n'); print(json.dumps(clean(summary),allow_nan=False)); return summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=='__main__': main()
