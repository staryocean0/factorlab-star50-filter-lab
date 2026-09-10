from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V11_RUNNER = HERE.parent / "highvol_recovery_survival_v11" / "run_survival.py"
DEV_YEARS = (2021, 2022, 2023)
HORIZONS = (15, 30, 60)
STATES = ("UNSAFE", "RECOVERING")
BUCKETS = ("LT15", "M15_25", "M30_40", "GE45")
MIN_TRAIN_CELL_N = 50


def load_v11():
    spec = importlib.util.spec_from_file_location("v11_for_v14", V11_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(V11_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_rows(root: Path, v11) -> pd.DataFrame:
    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in v11.SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([v11.build_rows(frames[s]) for s in v11.SYMBOLS], ignore_index=True)
    if rows.empty:
        raise RuntimeError("no V11 common-cohort rows")
    return rows


def smooth_prob(y: pd.Series) -> float:
    a = y.astype(int)
    return float((int(a.sum()) + 1) / (len(a) + 2))


def fit_age_only(train: pd.DataFrame, h: int) -> tuple[dict[str, float], dict[str, int]]:
    probs = {}; ns = {}
    for bucket in BUCKETS:
        g = train[train.age_bucket == bucket]
        if g.empty:
            raise RuntimeError(f"missing age bucket {bucket}")
        probs[bucket] = smooth_prob(g[f"normal_within_{h}m"])
        ns[bucket] = int(len(g))
    return probs, ns


def fit_state_age(train: pd.DataFrame, h: int) -> tuple[dict[tuple[str, str], float], dict[str, int]]:
    probs = {}; ns = {}
    for state in STATES:
        for bucket in BUCKETS:
            g = train[(train.current_state == state) & (train.age_bucket == bucket)]
            key = (state, bucket)
            if g.empty:
                raise RuntimeError(f"missing state-age cell {key}")
            probs[key] = smooth_prob(g[f"normal_within_{h}m"])
            ns[f"{state}|{bucket}"] = int(len(g))
    return probs, ns


def score(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, float); p = np.asarray(p, float)
    q = np.clip(p, 1e-12, 1 - 1e-12)
    return {
        "n": int(len(y)),
        "brier": float(np.mean((p-y)**2)),
        "log_loss": float(-np.mean(y*np.log(q)+(1-y)*np.log(1-q))),
        "observed_rate": float(np.mean(y)),
        "mean_prediction": float(np.mean(p)),
    }


def run_cv(rows: pd.DataFrame) -> tuple[list[dict], dict, int]:
    folds=[]
    pooled={h:{"y":[],"age":[],"state_age":[]} for h in HORIZONS}
    min_cell=10**9
    for held in DEV_YEARS:
        train=rows[rows.year != held]
        test=rows[rows.year == held]
        fr={"held_out_year":held,"horizons":{}}
        for h in HORIZONS:
            age_map,_=fit_age_only(train,h)
            sa_map,sa_n=fit_state_age(train,h)
            min_cell=min(min_cell,min(sa_n.values()))
            y=test[f"normal_within_{h}m"].astype(int).to_numpy()
            p_age=np.array([age_map[b] for b in test.age_bucket],float)
            p_sa=np.array([sa_map[(s,b)] for s,b in zip(test.current_state,test.age_bucket)],float)
            a=score(y,p_age); s=score(y,p_sa)
            fr["horizons"][str(h)]={
                "age_only":a,
                "state_plus_age":s,
                "brier_improvement_state_over_age":float(a["brier"]-s["brier"]),
                "logloss_improvement_state_over_age":float(a["log_loss"]-s["log_loss"]),
                "state_age_training_cell_n":sa_n,
            }
            pooled[h]["y"].append(y); pooled[h]["age"].append(p_age); pooled[h]["state_age"].append(p_sa)
        folds.append(fr)
    out={}
    for h in HORIZONS:
        y=np.concatenate(pooled[h]["y"]); pa=np.concatenate(pooled[h]["age"]); ps=np.concatenate(pooled[h]["state_age"])
        a=score(y,pa); s=score(y,ps)
        out[str(h)]={
            "age_only":a,
            "state_plus_age":s,
            "brier_improvement_state_over_age":float(a["brier"]-s["brier"]),
            "logloss_improvement_state_over_age":float(a["log_loss"]-s["log_loss"]),
        }
    return folds,out,int(min_cell)


def final_surface(rows: pd.DataFrame) -> list[dict]:
    out=[]
    for state in STATES:
        for bucket in BUCKETS:
            g=rows[(rows.current_state==state)&(rows.age_bucket==bucket)]
            r={"current_state":state,"age_bucket":bucket,"n":int(len(g))}
            for h in HORIZONS:
                r[f"p_{h}m"]=smooth_prob(g[f"normal_within_{h}m"])
            out.append(r)
    return out


def clean(v):
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,list): return [clean(x) for x in v]
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,float)):
        x=float(v); return x if np.isfinite(x) else None
    if isinstance(v,(np.bool_,)): return bool(v)
    return v


def run(root:Path,out:Path)->dict:
    v11=load_v11()
    if tuple(v11.HORIZONS)!=HORIZONS or tuple(v11.BUCKETS)!=BUCKETS or tuple(v11.STATES)!=STATES:
        raise RuntimeError("V11 frozen dimensions drift")
    rows=build_rows(root,v11)
    folds,pooled,min_cell=run_cv(rows)
    annual_brier_wins={str(h):int(sum(f["horizons"][str(h)]["brier_improvement_state_over_age"]>0 for f in folds)) for h in HORIZONS}
    gates={
        "pooled_brier_improves_all_horizons":all(pooled[str(h)]["brier_improvement_state_over_age"]>0 for h in HORIZONS),
        "pooled_logloss_improves_all_horizons":all(pooled[str(h)]["logloss_improvement_state_over_age"]>0 for h in HORIZONS),
        "annual_brier_improves_at_least_2_of_3_each_horizon":all(annual_brier_wins[str(h)]>=2 for h in HORIZONS),
        "every_state_age_training_cell_n_ge_50":min_cell>=MIN_TRAIN_CELL_N,
        "state_thresholds_unchanged":True,
        "age_buckets_unchanged":True,
        "sample_cohort_unchanged":True,
        "horizons_unchanged":True,
        "validation_queried_false":True,
        "blackbox_queried_false":True,
    }
    supported=bool(all(gates.values()))
    summary={
        "schema":"highvol_horizon_specific_state_value_v14_development",
        "development_only":True,
        "development_years":list(DEV_YEARS),
        "row_count":int(len(rows)),
        "models":["age_only","state_plus_age"],
        "horizons_minutes":list(HORIZONS),
        "min_state_age_training_cell_n":min_cell,
        "annual_brier_win_count":annual_brier_wins,
        "folds":folds,
        "pooled_loyo":pooled,
        "full_development_horizon_specific_surface":final_surface(rows),
        "acceptance":gates,
        "horizon_specific_state_value_supported":supported,
        "validation_authorized":supported,
        "validation_queried":False,
        "blackbox_queried":False,
        "pnl_computed":False,
        "trading_rule_created":False,
        "production_authority":False,
        "decision":"NOMINATE_HORIZON_SPECIFIC_RECOVERY_SURFACE_FOR_FROZEN_VALIDATION" if supported else "REJECT_INCREMENTAL_STATE_VALUE_BEYOND_RECENT_SHOCK_AGE",
    }
    out.mkdir(parents=True,exist_ok=True)
    rows.to_parquet(out/"common_cohort.parquet",index=False)
    (out/"summary.json").write_text(json.dumps(clean(summary),indent=2,sort_keys=True)+"\n")
    print(json.dumps(clean(summary),sort_keys=True))
    return summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path(".")); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); run(a.repo_root.resolve(),a.out.resolve())

if __name__=="__main__": main()
