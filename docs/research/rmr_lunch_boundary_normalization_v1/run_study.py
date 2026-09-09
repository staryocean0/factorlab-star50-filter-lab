#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
YEARS=(2021,2022,2023)
LOOKBACK=30


def write_json(path:Path,obj)->None:
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def band(z:float)->str:
    if z<=1: return "low"
    if z<=2: return "mid"
    return "high"


def make_rows(frame:pd.DataFrame,symbol:str)->pd.DataFrame:
    q=frame[frame.symbol==symbol].copy()
    local=q.market_time_shanghai.dt.tz_localize(None)
    q["afternoon"]=(local.dt.hour>=13).astype(int)
    q["day"]=q.trading_day.astype(str)
    q=q.sort_values("market_time_shanghai",kind="stable").reset_index(drop=True)
    q["eligible"]=q.get("high_frequency_analysis_eligible",True)
    q["eligible"]=q.eligible.fillna(False).astype(bool)
    rows=[]
    for day,z in q.groupby("day",sort=True):
        am=z[z.afternoon==0].reset_index(drop=True)
        pm=z[z.afternoon==1].reset_index(drop=True)
        if len(am)!=120 or len(pm)!=120: continue
        if not (am.eligible.all() and pm.eligible.iloc[:15].all()): continue
        am_close=am.close.to_numpy(float)
        if not np.isfinite(am_close).all() or (am_close<=0).any(): continue
        ret=np.diff(np.log(am_close))*1e4
        if len(ret)<LOOKBACK or not np.isfinite(ret[-LOOKBACK:]).all(): continue
        sigma=max(float(np.sqrt(np.mean(ret[-LOOKBACK:]**2))),1.0)
        anchor=float(am.close.iloc[-1]); reopen=float(pm.open.iloc[0])
        if not (np.isfinite(anchor) and np.isfinite(reopen) and anchor>0 and reopen>0): continue
        gap=float(np.log(reopen/anchor)*1e4)
        if abs(gap)<=1e-12: continue
        zscore=abs(gap)/sigma
        direction=float(np.sign(gap))
        c5=float(pm.close.iloc[4]); c15=float(pm.close.iloc[14])
        if not (np.isfinite(c5) and np.isfinite(c15) and c5>0 and c15>0): continue
        f5=float(np.log(c5/reopen)*1e4); f15=float(np.log(c15/reopen)*1e4)
        sf5=direction*f5; sf15=direction*f15
        rows.append({"symbol":symbol,"day":day,"year":int(day[:4]),"lunch_gap_bp":gap,
                     "gap_direction":"UP" if gap>0 else "DOWN","sigma_pre_bp":sigma,"Z":zscore,"band":band(zscore),
                     "signed_F5_bp":sf5,"signed_F15_bp":sf15,"reversal5":bool(sf5<0),
                     "recovery_fraction_5":-sf5/abs(gap)})
    return pd.DataFrame(rows)


def metrics(z:pd.DataFrame)->dict:
    return {"n":int(len(z)),"median_signed_F5_bp":float(z.signed_F5_bp.median()) if len(z) else None,
            "mean_signed_F5_bp":float(z.signed_F5_bp.mean()) if len(z) else None,
            "reversal5_prob":float(z.reversal5.mean()) if len(z) else None,
            "median_recovery_fraction_5":float(z.recovery_fraction_5.median()) if len(z) else None,
            "median_signed_F15_bp":float(z.signed_F15_bp.median()) if len(z) else None}


def summarize(rows:pd.DataFrame):
    annual=[]; pooled=[]; per={}
    for s in SYMBOLS:
        x=rows[rows.symbol==s]
        mat=x[x.Z>1]; low=x[x.Z<=1]
        for y in YEARS: annual.append({"symbol":s,"year":y,**metrics(mat[mat.year==y])})
        pooled.append({"symbol":s,"view":"material_Z_gt_1",**metrics(mat)})
        pooled.append({"symbol":s,"view":"low_Z_le_1",**metrics(low)})
        for d in ("UP","DOWN"): pooled.append({"symbol":s,"view":f"material_{d}",**metrics(mat[mat.gap_direction==d])})
        for b in ("low","mid","high"): pooled.append({"symbol":s,"view":f"band_{b}",**metrics(x[x.band==b])})
        a=pd.DataFrame(annual); ay=a[a.symbol==s].set_index("year")
        p=pd.DataFrame(pooled); ps=p[p.symbol==s].set_index("view")
        m=ps.loc["material_Z_gt_1"]; l=ps.loc["low_Z_le_1"]; up=ps.loc["material_UP"]; down=ps.loc["material_DOWN"]
        checks={"n_ge_100_pooled":bool(m.n>=100),"n_ge_20_each_year":bool((ay.n>=20).all()),
                "median_reverts_each_year":bool((ay.median_signed_F5_bp<0).all()),
                "pooled_reversal_prob_ge_55pct":bool(m.reversal5_prob>=0.55),
                "up_n_ge_30_and_reverts":bool(up.n>=30 and up.median_signed_F5_bp<0),
                "down_n_ge_30_and_reverts":bool(down.n>=30 and down.median_signed_F5_bp<0),
                "median_recovery_fraction_positive":bool(m.median_recovery_fraction_5>0),
                "reversal_advantage_vs_low_ge_5pp":bool(m.reversal5_prob-l.reversal5_prob>=0.05)}
        per[s]={"checks":checks,"pass":bool(all(checks.values()))}
    annual=pd.DataFrame(annual); pooled=pd.DataFrame(pooled)
    verdict="broad_signal_source_supported" if all(v["pass"] for v in per.values()) else "broad_signal_source_not_established"
    return annual,pooled,{"verdict":verdict,"per_symbol":per}


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[3]); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(root/"src")); from star50_filter.cloud_market_data import load_market_data
    frames=[]
    for s in SYMBOLS:
        native=load_market_data(s,"1m","2021-01-01","2023-12-31",root=root); frames.append(make_rows(native,s))
    rows=pd.concat(frames,ignore_index=True)
    if set(rows.year.unique())-set(YEARS): raise RuntimeError("non-Development row")
    annual,pooled,decision=summarize(rows)
    rows.to_csv(out/"days.csv",index=False); annual.to_csv(out/"annual_summary.csv",index=False); pooled.to_csv(out/"pooled_summary.csv",index=False)
    summary={"schema":"rmr_lunch_boundary_normalization_v1","development_years":list(YEARS),"days":int(len(rows)),"decision":decision,
             "validation_queried":False,"blackbox_queried":False,"returns_or_pnl_evaluated":False,
             "candidate_nominated":bool(decision["verdict"]=="broad_signal_source_supported"),"production_authority":False,
             "git_sha":os.getenv("GITHUB_SHA"),"run_id":os.getenv("GITHUB_RUN_ID")}
    write_json(out/"summary.json",summary); print(json.dumps(summary,ensure_ascii=False,indent=2)); print(annual.to_string(index=False)); print(pooled.to_string(index=False)); return 0

if __name__=="__main__": raise SystemExit(main())
