from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

LOOKBACKS=(1,2,3,5,10)
DIRECTIONS=("momentum","reversal")
DELAYS=(1,2)
GATES=("Ungated","HighVol","NormalVol")
SYMBOLS=("000688.SH","000852.SH")
DEV_YEARS=(2021,2022,2023)
VAL_YEARS=(2024,2025,2026)
COSTS=(0.5,1.0,2.0)


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def contiguous_runs(mask:np.ndarray):
    mask=np.asarray(mask,bool);n=len(mask);i=0
    while i<n:
        while i<n and not mask[i]: i+=1
        if i>=n: break
        j=i+1
        while j<n and mask[j]: j+=1
        yield i,j
        i=j


def signals_for_lookback(minute:pd.DataFrame,lookback:int,direction:str)->np.ndarray:
    out=np.zeros(len(minute),float)
    mult=1.0 if direction=="momentum" else -1.0
    for _,idx in minute.groupby("session",sort=False).indices.items():
        ix=np.asarray(idx,int)
        close=minute.close.to_numpy(float)[ix]
        valid=minute.valid.to_numpy(bool)[ix]&np.isfinite(close)&(close>0)
        sig=np.zeros(len(ix),float)
        for i in range(lookback,len(ix)):
            if not valid[i-lookback:i+1].all(): continue
            move=np.log(close[i]/close[i-lookback])*1e4
            if move>0: sig[i]=mult
            elif move<0: sig[i]=-mult
        out[ix]=sig
    return out


def simulate(minute:pd.DataFrame,signal:np.ndarray,gate:str,delay:int)->dict:
    gross=0.0;turn=0.0;exposure=0;booked=0;wins=0
    opens_all=minute.open.to_numpy(float);valid_all=minute.valid.to_numpy(bool);states=minute.route_state.to_numpy(object)
    for _,idx in minute.groupby("session",sort=False).indices.items():
        ix=np.asarray(idx,int)
        op=opens_all[ix]; valid=valid_all[ix]&np.isfinite(op)&(op>0); sig=signal[ix]; st=states[ix]
        for a,b in contiguous_runs(valid):
            oo=op[a:b]; ss=sig[a:b]; state=st[a:b]; n=len(oo)
            if n<2: continue
            if gate=="Ungated": desired=ss
            else: desired=np.where(state==gate,ss,0.0)
            interval_pos=np.zeros(n-1,float)
            if n-1-delay>0:
                interval_pos[delay:]=desired[:n-1-delay]
            ret=np.log(oo[1:]/oo[:-1])*1e4
            pnl=interval_pos*ret
            gross+=float(np.sum(pnl))
            turn+=float(np.sum(np.abs(np.diff(np.r_[0.0,interval_pos,0.0]))))
            active=interval_pos!=0
            count=int(active.sum());exposure+=count;booked+=count;wins+=int((pnl[active]>0).sum())
    return {"gross_bp":gross,"one_way_turnover":turn,"exposure_minutes":exposure,"booked_returns":booked,"winning_returns":wins}


def annual_row(minute,signal,symbol,year,direction,lookback,delay,gate):
    z=minute[minute.year==year].copy()
    s=signal[z.index.to_numpy(int)]
    q=simulate(z.reset_index(drop=True),s,gate,delay)
    q.update({"symbol":symbol,"year":year,"direction":direction,"lookback_min":lookback,"delay_min":delay,"gate":gate})
    q["gross_bp_per_exposure_min"]=q["gross_bp"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
    q["break_even_one_way_cost_bp"]=q["gross_bp"]/q["one_way_turnover"] if q["one_way_turnover"] else np.nan
    q["hit_rate"]=q["winning_returns"]/q["booked_returns"] if q["booked_returns"] else np.nan
    for c in COSTS:
        q[f"net_bp_cost_{c:g}"]=q["gross_bp"]-c*q["one_way_turnover"]
        q[f"net_bp_per_exposure_min_cost_{c:g}"]=q[f"net_bp_cost_{c:g}"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
    return q


def pool_years(df:pd.DataFrame,years)->pd.DataFrame:
    x=df[df.year.isin(years)].copy();keys=["symbol","direction","lookback_min","delay_min","gate"]
    sums=x.groupby(keys)[["gross_bp","one_way_turnover","exposure_minutes","booked_returns","winning_returns"]].sum().reset_index()
    sums["gross_bp_per_exposure_min"]=sums.gross_bp/sums.exposure_minutes.replace(0,np.nan)
    sums["break_even_one_way_cost_bp"]=sums.gross_bp/sums.one_way_turnover.replace(0,np.nan)
    sums["hit_rate"]=sums.winning_returns/sums.booked_returns.replace(0,np.nan)
    for c in COSTS:
        sums[f"net_bp_cost_{c:g}"]=sums.gross_bp-c*sums.one_way_turnover
        sums[f"net_bp_per_exposure_min_cost_{c:g}"]=sums[f"net_bp_cost_{c:g}"]/sums.exposure_minutes.replace(0,np.nan)
    return sums


def nominate(annual:pd.DataFrame,dev_pool:pd.DataFrame)->pd.DataFrame:
    rows=[];high=annual[(annual.gate=="HighVol")&(annual.year.isin(DEV_YEARS))];pool=dev_pool[dev_pool.gate=="HighVol"]
    for symbol in SYMBOLS:
        candidates=[]
        for direction in DIRECTIONS:
            for lookback in LOOKBACKS:
                for delay in DELAYS:
                    y=high[(high.symbol==symbol)&(high.direction==direction)&(high.lookback_min==lookback)&(high.delay_min==delay)]
                    p=pool[(pool.symbol==symbol)&(pool.direction==direction)&(pool.lookback_min==lookback)&(pool.delay_min==delay)]
                    if len(y)!=3 or len(p)!=1: continue
                    pp=p.iloc[0]
                    positive=int((y["net_bp_per_exposure_min_cost_1"]>0).sum())
                    eligible=bool((y.exposure_minutes>0).all() and positive>=2 and pp.break_even_one_way_cost_bp>1.0)
                    score=float(pp.net_bp_per_exposure_min_cost_1)
                    candidates.append((eligible,score,lookback,delay,0 if direction=="reversal" else 1,direction,positive,float(pp.break_even_one_way_cost_bp)))
        e=[x for x in candidates if x[0]]
        if not e:
            rows.append({"symbol":symbol,"nomination":"NONE","direction":None,"lookback_min":None,"delay_min":None,"dev_net1_per_min":np.nan,"positive_dev_years":0,"dev_break_even_bp":np.nan})
        else:
            e=sorted(e,key=lambda x:(-x[1],x[2],x[3],x[4]));x=e[0]
            rows.append({"symbol":symbol,"nomination":"CANDIDATE","direction":x[5],"lookback_min":x[2],"delay_min":x[3],"dev_net1_per_min":x[1],"positive_dev_years":x[6],"dev_break_even_bp":x[7]})
    return pd.DataFrame(rows)


def evaluate(annual,val_pool,nom):
    rows=[]
    for n in nom.itertuples(index=False):
        if n.nomination!="CANDIDATE": rows.append({"symbol":n.symbol,"status":"NO_DEV_CANDIDATE"});continue
        z=annual[(annual.symbol==n.symbol)&(annual.direction==n.direction)&(annual.lookback_min==n.lookback_min)&(annual.delay_min==n.delay_min)&(annual.gate=="HighVol")&annual.year.isin(VAL_YEARS)]
        hp=val_pool[(val_pool.symbol==n.symbol)&(val_pool.direction==n.direction)&(val_pool.lookback_min==n.lookback_min)&(val_pool.delay_min==n.delay_min)&(val_pool.gate=="HighVol")].iloc[0]
        npool=val_pool[(val_pool.symbol==n.symbol)&(val_pool.direction==n.direction)&(val_pool.lookback_min==n.lookback_min)&(val_pool.delay_min==n.delay_min)&(val_pool.gate=="NormalVol")].iloc[0]
        pos=int((z.net_bp_per_exposure_min_cost_1>0).sum())
        rows.append({"symbol":n.symbol,"status":"EVALUATED","direction":n.direction,"lookback_min":int(n.lookback_min),"delay_min":int(n.delay_min),"positive_validation_slices":pos,"validation_high_net1_per_min":float(hp.net_bp_per_exposure_min_cost_1),"validation_break_even_bp":float(hp.break_even_one_way_cost_bp),"validation_normal_net1_per_min":float(npool.net_bp_per_exposure_min_cost_1),"validation_high_minus_normal":float(hp.net_bp_per_exposure_min_cost_1-npool.net_bp_per_exposure_min_cost_1),"q1_pool_positive":bool(hp.net_bp_per_exposure_min_cost_1>0),"q2_two_positive_slices":bool(pos>=2),"q3_break_even_gt_1":bool(hp.break_even_one_way_cost_bp>1),"q4_high_better_normal":bool(hp.net_bp_per_exposure_min_cost_1>npool.net_bp_per_exposure_min_cost_1)})
    return pd.DataFrame(rows)


def run(root:Path,out:Path):
    regime=load_module(root/"docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py","regime")
    orig=load_module(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_orig_dir")
    fg=load_module(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","phase2_grid_dir")
    rows=[];receipts=[]
    for symbol in SYMBOLS:
        native=orig.load_native(root,symbol)
        state=regime.build_continuous_state(native,symbol)
        minute=fg.build_minute_grid(native,state.rename(columns={"vol_ratio":"recovery_ratio"}),symbol).reset_index(drop=True)
        receipts.append({"symbol":symbol,"rows":len(minute),"high_minutes":int((minute.route_state=="HighVol").sum()),"normal_minutes":int((minute.route_state=="NormalVol").sum()),"unknown_minutes":int((minute.route_state=="Unknown").sum())})
        for direction in DIRECTIONS:
            for lookback in LOOKBACKS:
                sig=signals_for_lookback(minute,lookback,direction)
                for delay in DELAYS:
                    for year in DEV_YEARS+VAL_YEARS:
                        for gate in GATES:
                            rows.append(annual_row(minute,sig,symbol,year,direction,lookback,delay,gate))
    annual=pd.DataFrame(rows);dev=pool_years(annual,DEV_YEARS);val=pool_years(annual,VAL_YEARS);nom=nominate(annual,dev);ev=evaluate(annual,val,nom)
    out.mkdir(parents=True,exist_ok=True)
    annual.to_csv(out/"annual_surface.csv",index=False);dev.to_csv(out/"development_pool_2021_2023.csv",index=False);val.to_csv(out/"validation_pool_2024_2026.csv",index=False);nom.to_csv(out/"development_nomination.csv",index=False);ev.to_csv(out/"validation_evaluation.csv",index=False);pd.DataFrame(receipts).to_csv(out/"state_receipts.csv",index=False)
    summary={"schema":"continuous_vol_direction_v1","development_years":list(DEV_YEARS),"validation_years":[2024,2025,"2026_through_2026-08-21"],"blackbox_queried":False,"nomination":nom.to_dict(orient="records"),"evaluation":ev.to_dict(orient="records")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n");print(json.dumps(summary,default=str));return summary


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True);args=ap.parse_args();run(Path(args.repo_root).resolve(),Path(args.out))

if __name__=="__main__": main()
