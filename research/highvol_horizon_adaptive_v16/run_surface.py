from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V15_DIR = HERE.parent / "highvol_horizon_composite_v15"
V15_RUNNER = V15_DIR / "run_adjudication.py"
V15_RECEIPT = V15_DIR / "DECISIVE_RECEIPT.json"
V15_RUNNER_BLOB = "5d29be64bb797dcd21388e2455b670127e0de81b"
V15_RECEIPT_BLOB = "f430de0a4820c951af0b9153e3e81a0e355de3d8"

DEV_YEARS = (2021, 2022, 2023)
HORIZONS = (15, 30, 60)
STATES = ("UNSAFE", "RECOVERING")
BUCKETS = ("LT15", "M15_25", "M30_40", "GE45")
EXPECTED_ROWS = 7327
MIN_TRAIN_CELL_N = 50
TOL = 1e-12


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_v15():
    if git_blob_sha(V15_RUNNER) != V15_RUNNER_BLOB:
        raise RuntimeError("V15 runner drift")
    if git_blob_sha(V15_RECEIPT) != V15_RECEIPT_BLOB:
        raise RuntimeError("V15 receipt drift")
    receipt = json.loads(V15_RECEIPT.read_text())
    if receipt["run_id"] != 34497176574 or receipt["horizon_dependence_supported"] is not True:
        raise RuntimeError("V15 authority invalid")
    spec = importlib.util.spec_from_file_location("v15_frozen_for_v16", V15_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(V15_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def project(raw15: np.ndarray, raw30: np.ndarray, age60: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p60 = np.asarray(age60, float).copy()
    p30 = np.minimum(np.asarray(raw30, float), p60)
    p15 = np.minimum(np.asarray(raw15, float), p30)
    return p15, p30, p60


def score(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    q = np.clip(p, 1e-12, 1 - 1e-12)
    return {
        "n": int(len(y)),
        "brier": float(np.mean((p-y)**2)),
        "log_loss": float(-np.mean(y*np.log(q)+(1-y)*np.log(1-q))),
        "observed_rate": float(np.mean(y)),
        "mean_prediction": float(np.mean(p)),
    }


def make_oof(rows: pd.DataFrame, v15) -> tuple[pd.DataFrame, list[dict], int]:
    parts=[]
    folds=[]
    min_cell=10**9
    for held in DEV_YEARS:
        train=rows[rows.year != held]
        test=rows[rows.year == held].copy().reset_index(drop=True)
        age_maps={h:v15.fit_age_only(train,h) for h in HORIZONS}
        sa15,n15=v15.fit_state_age(train,15)
        sa30,n30=v15.fit_state_age(train,30)
        min_cell=min(min_cell,min(n15.values()),min(n30.values()))
        y={h:test[f"normal_within_{h}m"].astype(int).to_numpy() for h in HORIZONS}
        base={h:np.array([age_maps[h][b] for b in test.age_bucket],float) for h in HORIZONS}
        raw15=np.array([sa15[(s,b)] for s,b in zip(test.current_state,test.age_bucket)],float)
        raw30=np.array([sa30[(s,b)] for s,b in zip(test.current_state,test.age_bucket)],float)
        p15,p30,p60=project(raw15,raw30,base[60])
        pred={15:p15,30:p30,60:p60}
        out=test[["symbol","trading_day","year","current_state","age_bucket"]].copy()
        out["raw_state_age_15"]=raw15
        out["raw_state_age_30"]=raw30
        out["raw_age_only_60"]=base[60]
        for h in HORIZONS:
            out[f"y_{h}"]=y[h]
            out[f"p_age_{h}"]=base[h]
            out[f"p_adaptive_{h}"]=pred[h]
        out["adjusted_15"] = p15 < raw15 - TOL
        out["adjusted_30"] = p30 < raw30 - TOL
        out["monotone"] = (p15 <= p30 + TOL) & (p30 <= p60 + TOL)
        rec={"held_out_year":held,"horizons":{}}
        for h in HORIZONS:
            a=score(y[h],base[h]); m=score(y[h],pred[h])
            rec["horizons"][str(h)]={
                "age_only":a,
                "adaptive":m,
                "brier_improvement_adaptive_over_age":float(a["brier"]-m["brier"]),
                "logloss_improvement_adaptive_over_age":float(a["log_loss"]-m["log_loss"]),
            }
        rec["adjusted_15_rows"]=int(out.adjusted_15.sum())
        rec["adjusted_30_rows"]=int(out.adjusted_30.sum())
        folds.append(rec); parts.append(out)
    oof=pd.concat(parts,ignore_index=True)
    if len(oof)!=EXPECTED_ROWS:
        raise RuntimeError(f"OOF row drift {len(oof)} != {EXPECTED_ROWS}")
    return oof,folds,int(min_cell)


def final_surface(rows: pd.DataFrame, v15) -> list[dict]:
    age60=v15.fit_age_only(rows,60)
    sa15,_=v15.fit_state_age(rows,15)
    sa30,_=v15.fit_state_age(rows,30)
    out=[]
    for state in STATES:
        for bucket in BUCKETS:
            raw15=float(sa15[(state,bucket)])
            raw30=float(sa30[(state,bucket)])
            raw60=float(age60[bucket])
            p15,p30,p60=project(np.array([raw15]),np.array([raw30]),np.array([raw60]))
            out.append({
                "current_state":state,
                "age_bucket":bucket,
                "raw_state_age_15":raw15,
                "raw_state_age_30":raw30,
                "raw_age_only_60":raw60,
                "p_15m":float(p15[0]),
                "p_30m":float(p30[0]),
                "p_60m":float(p60[0]),
                "adjusted_15":bool(p15[0] < raw15-TOL),
                "adjusted_30":bool(p30[0] < raw30-TOL),
            })
    return out


def pooled_scores(oof: pd.DataFrame) -> dict:
    out={}
    for h in HORIZONS:
        y=oof[f"y_{h}"].to_numpy(float)
        pa=oof[f"p_age_{h}"].to_numpy(float)
        pm=oof[f"p_adaptive_{h}"].to_numpy(float)
        a=score(y,pa); m=score(y,pm)
        out[str(h)]={
            "age_only":a,
            "adaptive":m,
            "brier_improvement_adaptive_over_age":float(a["brier"]-m["brier"]),
            "logloss_improvement_adaptive_over_age":float(a["log_loss"]-m["log_loss"]),
        }
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
    v15=load_v15()
    v11=v15.load_v11()
    rows=v15.build_rows(root,v11)
    oof,folds,min_cell=make_oof(rows,v15)
    pooled=pooled_scores(oof)
    surface=final_surface(rows,v15)
    annual_wins={str(h):int(sum(f["horizons"][str(h)]["brier_improvement_adaptive_over_age"]>0 for f in folds)) for h in HORIZONS}
    surface_df=pd.DataFrame(surface)
    p60_span=surface_df.groupby("age_bucket").p_60m.agg(lambda s: float(s.max()-s.min())).max()
    acceptance={
        "row_count_exact_7327":len(rows)==EXPECTED_ROWS,
        "every_state_age_training_cell_n_ge_50":min_cell>=MIN_TRAIN_CELL_N,
        "all_oof_rows_monotone":bool(oof.monotone.all()),
        "all_8_final_cells_monotone":bool(((surface_df.p_15m<=surface_df.p_30m+TOL)&(surface_df.p_30m<=surface_df.p_60m+TOL)).all()),
        "p60_state_invariant_within_age":bool(p60_span<=TOL),
        "p60_oof_exact_age_only":bool(np.max(np.abs(oof.p_adaptive_60-oof.p_age_60))<=TOL),
        "h15_pooled_brier_improves":pooled["15"]["brier_improvement_adaptive_over_age"]>0,
        "h30_pooled_brier_improves":pooled["30"]["brier_improvement_adaptive_over_age"]>0,
        "h15_pooled_logloss_improves":pooled["15"]["logloss_improvement_adaptive_over_age"]>0,
        "h30_pooled_logloss_improves":pooled["30"]["logloss_improvement_adaptive_over_age"]>0,
        "h15_annual_brier_wins_ge_2_of_3":annual_wins["15"]>=2,
        "h30_annual_brier_wins_ge_2_of_3":annual_wins["30"]>=2,
        "h60_brier_score_equivalent_age_only":abs(pooled["60"]["brier_improvement_adaptive_over_age"])<=TOL,
        "h60_logloss_score_equivalent_age_only":abs(pooled["60"]["logloss_improvement_adaptive_over_age"])<=TOL,
        "adjustments_downward_only":bool((oof.p_adaptive_15<=oof.raw_state_age_15+TOL).all() and (oof.p_adaptive_30<=oof.raw_state_age_30+TOL).all()),
        "state_thresholds_unchanged":True,
        "age_buckets_unchanged":True,
        "horizons_unchanged":True,
        "sample_cohort_unchanged":True,
        "validation_queried_false":True,
        "blackbox_queried_false":True,
        "pnl_computed_false":True,
        "trading_rule_created_false":True,
    }
    supported=bool(all(acceptance.values()))
    summary={
        "schema":"highvol_horizon_adaptive_surface_v16_development_v1",
        "development_only":True,
        "validation_informed_hypothesis":True,
        "development_years":list(DEV_YEARS),
        "row_count":int(len(rows)),
        "horizons_minutes":list(HORIZONS),
        "construction":{"15m":"state_plus_age_backward_capped","30m":"state_plus_age_capped_at_age_only_60","60m":"age_only_anchor"},
        "min_state_age_training_cell_n":min_cell,
        "oof_adjustment_counts":{"15m":int(oof.adjusted_15.sum()),"30m":int(oof.adjusted_30.sum())},
        "annual_brier_win_count":annual_wins,
        "annual_leave_one_year_out":folds,
        "pooled_leave_one_year_out":pooled,
        "full_development_surface":surface,
        "acceptance":acceptance,
        "adaptive_surface_supported":supported,
        "validation_authorized":supported,
        "threshold_search_performed":False,
        "parameter_change_performed":False,
        "validation_queried":False,
        "blackbox_queried":False,
        "pnl_computed":False,
        "trading_rule_created":False,
        "production_authority":False,
    }
    out.mkdir(parents=True,exist_ok=True)
    oof.to_parquet(out/"oof_predictions.parquet",index=False)
    surface_df.to_csv(out/"full_development_surface.csv",index=False)
    (out/"summary.json").write_text(json.dumps(clean(summary),indent=2,sort_keys=True)+"\n")
    print(json.dumps(clean(summary),sort_keys=True))
    return summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path(".")); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); run(a.repo_root.resolve(),a.out.resolve())


if __name__=="__main__": main()
