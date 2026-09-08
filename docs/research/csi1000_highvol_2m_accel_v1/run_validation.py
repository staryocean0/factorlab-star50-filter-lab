from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

VAL_START="2024-01-01"
VAL_END="2026-08-21"
COSTS=(0.5,1.0,1.5,2.0)


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def select_candidate(events:pd.DataFrame)->pd.DataFrame:
    z=events[(events.symbol=="000852.SH")&(events.tail2_share>=0.80)&(events.tail1_share<0.60)].copy()
    z=z[np.isfinite(pd.to_numeric(z.cont_10m_bp,errors="coerce"))].sort_values(["session","onset_row"])
    rows=[]
    for session,g in z.groupby("session",sort=False):
        next_allowed=-1
        for r in g.itertuples(index=False):
            i=int(r.onset_row)
            if i<next_allowed: continue
            rows.append({
                "symbol":r.symbol,"year":int(r.year),"trading_day":r.trading_day,"session":session,
                "onset_minute":int(r.onset_minute),"onset_row":i,"sign5":float(r.sign5),
                "tail1_share":float(r.tail1_share),"tail2_share":float(r.tail2_share),"eff5":float(r.eff5),
                "vol_ratio":float(r.vol_ratio),"gross_bp":float(r.cont_10m_bp),
            })
            next_allowed=i+11
    return pd.DataFrame(rows)


def metrics(z:pd.DataFrame)->dict:
    n=len(z);gross=float(z.gross_bp.sum()) if n else 0.0;mean=gross/n if n else np.nan
    out={"trades":n,"gross_bp":gross,"mean_gross_bp":mean,"hit_rate":float((z.gross_bp>0).mean()) if n else np.nan,
         "one_way_break_even_bp":mean/2.0 if n else np.nan}
    for c in COSTS:
        out[f"net_bp_cost_{c:g}"]=gross-(2*c*n)
        out[f"mean_net_bp_cost_{c:g}"]=mean-2*c if n else np.nan
    return out


def run(root:Path,out:Path):
    regime=load_module(root/"docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py","regime_val")
    struct=load_module(root/"docs/research/highvol_structure_dev_v1/run_dev_structure.py","struct_val")
    orig=load_module(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_val")
    fg=load_module(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","grid_val")

    native=orig.load_native(root,"000852.SH").copy()
    native["trading_day"]=native.trading_day.astype(str).str[:10]
    native=native[native.trading_day<=VAL_END].copy()
    state=regime.build_continuous_state(native,"000852.SH")
    minute=fg.build_minute_grid(native,state.rename(columns={"vol_ratio":"recovery_ratio"}),"000852.SH").reset_index(drop=True)
    minute=minute[(minute.trading_day>=VAL_START)&(minute.trading_day<=VAL_END)].reset_index(drop=True)
    events=struct.build_event_rows(minute)
    trades=select_candidate(events)

    annual=[]
    for year in (2024,2025,2026):
        q=metrics(trades[trades.year==year]);q["year"]=year;annual.append(q)
    annual=pd.DataFrame(annual)
    pooled=metrics(trades)
    direction=[]
    for sign,label in ((1.0,"long"),(-1.0,"short")):
        q=metrics(trades[trades.sign5==sign]);q["direction"]=label;direction.append(q)
    direction=pd.DataFrame(direction)

    positive_slices=int((annual.mean_net_bp_cost_1>0).sum())
    acceptance={
        "pooled_net1_positive":bool(pooled["mean_net_bp_cost_1"]>0 if pooled["trades"] else False),
        "at_least_two_positive_validation_slices":bool(positive_slices>=2),
        "pooled_break_even_gt_1bp":bool(pooled["one_way_break_even_bp"]>1 if pooled["trades"] else False),
        "pooled_trades_ge_30":bool(pooled["trades"]>=30),
        "directions_reported_without_filtering":True,
    }
    acceptance["all_primary_pass"]=bool(all(acceptance.values()))

    out.mkdir(parents=True,exist_ok=True)
    trades.to_csv(out/"validation_trades.csv",index=False)
    annual.to_csv(out/"annual_validation.csv",index=False)
    direction.to_csv(out/"direction_validation.csv",index=False)
    pd.DataFrame([pooled]).to_csv(out/"pooled_validation.csv",index=False)
    summary={"schema":"csi1000_highvol_2m_accel_v1_validation","candidate_frozen":True,"validation_start":VAL_START,"validation_end":VAL_END,
             "blackbox_queried":False,"positive_validation_slices":positive_slices,"pooled":pooled,"acceptance":acceptance}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print(json.dumps(summary,default=str))


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=="__main__": main()
