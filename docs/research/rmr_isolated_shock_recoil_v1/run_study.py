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
SHOCK_BP=30.0
SIGMA_MULT=4.0
LOOKBACK=30
HORIZONS=(1,3,5,15)


def write_json(path:Path,obj)->None:
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def make_panel(frame:pd.DataFrame,symbol:str)->pd.DataFrame:
    q=frame[frame.symbol==symbol].copy()
    local=q.market_time_shanghai.dt.tz_localize(None)
    q["afternoon"]=(local.dt.hour>=13).astype(int)
    q["day"]=q.trading_day.astype(str)
    q["session"]=q.day+"/"+q.afternoon.astype(str)
    q=q.sort_values("market_time_shanghai",kind="stable").reset_index(drop=True)
    q["minute"]=q.groupby("session",sort=False).cumcount()+1
    counts=q.groupby("session").size()
    q=q[q.session.isin(set(counts[counts==120].index))].copy().reset_index(drop=True)
    q["eligible"]=q.get("high_frequency_analysis_eligible",True)
    q["eligible"]=q.eligible.fillna(False).astype(bool)
    q["return_bp"]=np.nan
    for _,ix in q.groupby("session",sort=False).groups.items():
        idx=np.asarray(list(ix))
        close=q.loc[idx,"close"].to_numpy(float)
        q.loc[idx,"return_bp"]=np.r_[np.nan,np.diff(np.log(close))*1e4]
    return q[["day","session","minute","eligible","close","return_bp"]]


def build_events(panel:pd.DataFrame,symbol:str)->pd.DataFrame:
    rows=[]
    for session,part in panel.groupby("session",sort=False):
        z=part.sort_values("minute",kind="stable").reset_index(drop=True)
        if len(z)!=120: continue
        r=z.return_bp.to_numpy(float); p=z.close.to_numpy(float); e=z.eligible.to_numpy(bool)
        event=np.zeros(120,bool)
        sigma=np.full(120,np.nan)
        # Define events sequentially, using only trailing data and earlier event flags.
        for t in range(LOOKBACK+1,120):
            back=r[t-LOOKBACK:t]
            if not (e[t-LOOKBACK:t+1].all() and np.isfinite(back).all() and np.isfinite(r[t])):
                continue
            s=max(float(np.sqrt(np.mean(back*back))),1.0)
            sigma[t]=s
            raw=abs(r[t])>SHOCK_BP and abs(r[t])>SIGMA_MULT*s
            if raw and not event[t-LOOKBACK:t].any(): event[t]=True
        for t in np.flatnonzero(event):
            if t+max(HORIZONS)>=120 or not e[t:t+max(HORIZONS)+1].all(): continue
            direction=float(np.sign(r[t]))
            if direction==0: continue
            row={"symbol":symbol,"day":z.loc[t,"day"],"session":session,"minute":int(z.loc[t,"minute"]),
                 "year":int(str(z.loc[t,"day"])[:4]),"shock_return_bp":float(r[t]),
                 "shock_direction":"UP" if direction>0 else "DOWN","sigma_pre_bp":float(sigma[t])}
            for h in HORIZONS:
                fh=float(np.log(p[t+h]/p[t])*1e4)
                row[f"signed_F{h}_bp"]=direction*fh
            row["reversal5"]=bool(row["signed_F5_bp"]<0)
            row["recovery_fraction_5"]=-row["signed_F5_bp"]/abs(row["shock_return_bp"])
            row["recovery50_5"]=bool(row["recovery_fraction_5"]>=0.5)
            rows.append(row)
    return pd.DataFrame(rows)


def metrics(z:pd.DataFrame)->dict:
    return {"n":int(len(z)),
            "median_signed_F5_bp":float(z.signed_F5_bp.median()) if len(z) else None,
            "mean_signed_F5_bp":float(z.signed_F5_bp.mean()) if len(z) else None,
            "reversal5_prob":float(z.reversal5.mean()) if len(z) else None,
            "median_recovery_fraction_5":float(z.recovery_fraction_5.median()) if len(z) else None,
            "recovery50_5_prob":float(z.recovery50_5.mean()) if len(z) else None,
            "median_signed_F1_bp":float(z.signed_F1_bp.median()) if len(z) else None,
            "median_signed_F3_bp":float(z.signed_F3_bp.median()) if len(z) else None,
            "median_signed_F15_bp":float(z.signed_F15_bp.median()) if len(z) else None}


def summarize(events:pd.DataFrame):
    annual=[]; pooled=[]; per={}
    for symbol in SYMBOLS:
        s=events[events.symbol==symbol]
        for y in YEARS: annual.append({"symbol":symbol,"year":y,**metrics(s[s.year==y])})
        pooled.append({"symbol":symbol,"view":"ALL",**metrics(s)})
        for d in ("UP","DOWN"): pooled.append({"symbol":symbol,"view":d,**metrics(s[s.shock_direction==d])})
        a=pd.DataFrame(annual); ay=a[a.symbol==symbol].set_index("year")
        p=pd.DataFrame(pooled); ps=p[p.symbol==symbol].set_index("view")
        checks={"n_ge_100_pooled":bool(ps.loc["ALL","n"]>=100),
                "n_ge_20_each_year":bool((ay.n>=20).all()),
                "median_reverts_each_year":bool((ay.median_signed_F5_bp<0).all()),
                "pooled_reversal_prob_ge_55pct":bool(ps.loc["ALL","reversal5_prob"]>=0.55),
                "up_n_ge_30_and_reverts":bool(ps.loc["UP","n"]>=30 and ps.loc["UP","median_signed_F5_bp"]<0),
                "down_n_ge_30_and_reverts":bool(ps.loc["DOWN","n"]>=30 and ps.loc["DOWN","median_signed_F5_bp"]<0),
                "median_recovery_fraction_positive":bool(ps.loc["ALL","median_recovery_fraction_5"]>0)}
        per[symbol]={"checks":checks,"pass":bool(all(checks.values()))}
    annual=pd.DataFrame(annual); pooled=pd.DataFrame(pooled)
    verdict="broad_signal_source_supported" if all(v["pass"] for v in per.values()) else "broad_signal_source_not_established"
    return annual,pooled,{"verdict":verdict,"per_symbol":per}


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[3]); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); root=a.repo_root.resolve(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(root/"src")); from star50_filter.cloud_market_data import load_market_data
    frames=[]
    for s in SYMBOLS:
        native=load_market_data(s,"1m","2021-01-01","2023-12-31",root=root)
        frames.append(build_events(make_panel(native,s),s))
    events=pd.concat(frames,ignore_index=True)
    if set(events.year.unique())-set(YEARS): raise RuntimeError("non-Development row")
    annual,pooled,decision=summarize(events)
    events.to_csv(out/"events.csv",index=False); annual.to_csv(out/"annual_summary.csv",index=False); pooled.to_csv(out/"pooled_summary.csv",index=False)
    summary={"schema":"rmr_isolated_shock_recoil_v1","development_years":list(YEARS),"events":int(len(events)),"decision":decision,
             "validation_queried":False,"blackbox_queried":False,"returns_or_pnl_evaluated":False,
             "candidate_nominated":bool(decision["verdict"]=="broad_signal_source_supported"),"production_authority":False,
             "git_sha":os.getenv("GITHUB_SHA"),"run_id":os.getenv("GITHUB_RUN_ID")}
    write_json(out/"summary.json",summary); print(json.dumps(summary,ensure_ascii=False,indent=2)); print(annual.to_string(index=False)); print(pooled.to_string(index=False)); return 0

if __name__=="__main__": raise SystemExit(main())
