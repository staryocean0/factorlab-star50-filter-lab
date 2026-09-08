from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
DEV_YEARS=(2021,2022,2023)
VAL_YEARS=(2024,2025,2026)
HOLDS=(1,2,3,5,10)
MOM_E=(0.0,0.4,0.6,0.8)
REV_E=(1.0,0.6,0.4,0.2)
COSTS=(0.5,1.0,2.0)


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def build_onsets(minute:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for session,z0 in minute.groupby("session",sort=False):
        z=z0.sort_values("minute").reset_index(drop=True)
        state=z.route_state.to_numpy(object)
        close=z.close.to_numpy(float); op=z.open.to_numpy(float); valid=z.valid.to_numpy(bool)
        # close-to-close 1m returns within the half-session
        r=np.full(len(z),np.nan,float)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(close[i]) and np.isfinite(close[i-1]) and close[i]>0 and close[i-1]>0:
                r[i]=np.log(close[i]/close[i-1])*1e4
        for i in range(1,len(z)):
            if state[i]!="HighVol" or state[i-1]!="NormalVol": continue
            if i<5: continue
            recent=r[i-4:i+1]
            if len(recent)!=5 or not np.isfinite(recent).all(): continue
            net=float(np.sum(recent));tv=float(np.sum(np.abs(recent)))
            if tv<=0 or net==0: continue
            eff=abs(net)/tv;sign=1.0 if net>0 else -1.0
            rows.append({"symbol":z.symbol.iloc[0],"year":int(z.year.iloc[0]),"trading_day":z.trading_day.iloc[0],"session":session,
                         "onset_row":i,"onset_minute":int(z.minute.iloc[i]),"eff5":eff,"net5_bp":net,"sign5":sign})
    return pd.DataFrame(rows)


def candidate_trade_rows(minute:pd.DataFrame,onsets:pd.DataFrame,family:str,eff_threshold:float,hold:int)->pd.DataFrame:
    rows=[]
    by_session={k:v.sort_values("onset_row") for k,v in onsets.groupby("session",sort=False)}
    for session,z0 in minute.groupby("session",sort=False):
        if session not in by_session: continue
        z=z0.sort_values("minute").reset_index(drop=True)
        op=z.open.to_numpy(float);valid=z.valid.to_numpy(bool)
        next_allowed_onset=0
        for e in by_session[session].itertuples(index=False):
            i=int(e.onset_row)
            # if a previous selected trade is still active at this decision close, ignore this onset
            if i < next_allowed_onset: continue
            if family=="momentum":
                if e.eff5 < eff_threshold: continue
                pos=float(e.sign5)
            elif family=="reversal":
                if e.eff5 > eff_threshold: continue
                pos=-float(e.sign5)
            else: raise ValueError(family)
            entry=i+1;exit_=entry+hold
            if exit_>=len(z): continue
            # Never bridge invalid source minutes; both opens and every intervening 1m row must be valid.
            if not valid[entry:exit_+1].all(): continue
            if not (np.isfinite(op[entry]) and np.isfinite(op[exit_]) and op[entry]>0 and op[exit_]>0): continue
            gross=pos*np.log(op[exit_]/op[entry])*1e4
            rows.append({"symbol":e.symbol,"year":int(e.year),"trading_day":e.trading_day,"session":session,
                         "onset_minute":int(e.onset_minute),"family":family,"eff_threshold":eff_threshold,"hold_min":hold,
                         "eff5":float(e.eff5),"net5_bp":float(e.net5_bp),"position":pos,"entry_minute":int(z.minute.iloc[entry]),
                         "exit_minute":int(z.minute.iloc[exit_]),"gross_bp":float(gross)})
            next_allowed_onset=exit_
    return pd.DataFrame(rows)


def summarize(trades:pd.DataFrame,symbol:str,year:int,family:str,eff_threshold:float,hold:int)->dict:
    z=trades[trades.year==year] if len(trades) else trades
    n=len(z);gross=float(z.gross_bp.sum()) if n else 0.0;turn=2.0*n;expo=hold*n
    q={"symbol":symbol,"year":year,"family":family,"eff_threshold":eff_threshold,"hold_min":hold,
       "trades":n,"gross_bp":gross,"one_way_turnover":turn,"exposure_minutes":expo,
       "hit_rate":float((z.gross_bp>0).mean()) if n else np.nan,
       "gross_bp_per_trade":gross/n if n else np.nan,
       "gross_bp_per_exposure_min":gross/expo if expo else np.nan,
       "break_even_one_way_cost_bp":gross/turn if turn else np.nan}
    for c in COSTS:
        net=gross-c*turn
        q[f"net_bp_cost_{c:g}"]=net
        q[f"net_bp_per_trade_cost_{c:g}"]=net/n if n else np.nan
        q[f"net_bp_per_exposure_min_cost_{c:g}"]=net/expo if expo else np.nan
    return q


def pool_years(df:pd.DataFrame,years)->pd.DataFrame:
    x=df[df.year.isin(years)].copy();keys=["symbol","family","eff_threshold","hold_min"]
    s=x.groupby(keys)[["trades","gross_bp","one_way_turnover","exposure_minutes"]].sum().reset_index()
    # weighted hit rate from annual tables cannot be recovered exactly; compute only economics here.
    s["gross_bp_per_trade"]=s.gross_bp/s.trades.replace(0,np.nan)
    s["gross_bp_per_exposure_min"]=s.gross_bp/s.exposure_minutes.replace(0,np.nan)
    s["break_even_one_way_cost_bp"]=s.gross_bp/s.one_way_turnover.replace(0,np.nan)
    for c in COSTS:
        s[f"net_bp_cost_{c:g}"]=s.gross_bp-c*s.one_way_turnover
        s[f"net_bp_per_trade_cost_{c:g}"]=s[f"net_bp_cost_{c:g}"]/s.trades.replace(0,np.nan)
        s[f"net_bp_per_exposure_min_cost_{c:g}"]=s[f"net_bp_cost_{c:g}"]/s.exposure_minutes.replace(0,np.nan)
    return s


def nominate(annual:pd.DataFrame,dev:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for symbol in SYMBOLS:
        cand=[]
        for family,thresholds in (("momentum",MOM_E),("reversal",REV_E)):
            for e in thresholds:
                for h in HOLDS:
                    y=annual[(annual.symbol==symbol)&(annual.family==family)&(annual.eff_threshold==e)&(annual.hold_min==h)&annual.year.isin(DEV_YEARS)]
                    p=dev[(dev.symbol==symbol)&(dev.family==family)&(dev.eff_threshold==e)&(dev.hold_min==h)]
                    if len(y)!=3 or len(p)!=1: continue
                    pp=p.iloc[0];positive=int((y.net_bp_per_trade_cost_1>0).sum())
                    eligible=bool((y.trades>=10).all() and pp.trades>=50 and positive>=2 and pp.break_even_one_way_cost_bp>1 and pp.net_bp_per_trade_cost_1>0)
                    restrict_rank=(e if family=="momentum" else 1-e)
                    cand.append((eligible,float(pp.net_bp_per_exposure_min_cost_1),int(pp.trades),h,restrict_rank,0 if family=="momentum" else 1,family,e,positive,float(pp.break_even_one_way_cost_bp),float(pp.net_bp_per_trade_cost_1)))
        eligible=[x for x in cand if x[0]]
        if not eligible:
            rows.append({"symbol":symbol,"nomination":"NONE","family":None,"eff_threshold":np.nan,"hold_min":np.nan,"dev_trades":0,"positive_dev_years":0,"dev_break_even_bp":np.nan,"dev_net1_per_trade":np.nan,"dev_net1_per_exposure_min":np.nan})
        else:
            eligible=sorted(eligible,key=lambda x:(-x[1],-x[2],x[3],x[4],x[5]));x=eligible[0]
            rows.append({"symbol":symbol,"nomination":"CANDIDATE","family":x[6],"eff_threshold":x[7],"hold_min":x[3],"dev_trades":x[2],"positive_dev_years":x[8],"dev_break_even_bp":x[9],"dev_net1_per_trade":x[10],"dev_net1_per_exposure_min":x[1]})
    return pd.DataFrame(rows)


def evaluate(annual:pd.DataFrame,val:pd.DataFrame,nom:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for n in nom.itertuples(index=False):
        if n.nomination!="CANDIDATE": rows.append({"symbol":n.symbol,"status":"NO_DEV_CANDIDATE"});continue
        y=annual[(annual.symbol==n.symbol)&(annual.family==n.family)&(annual.eff_threshold==n.eff_threshold)&(annual.hold_min==n.hold_min)&annual.year.isin(VAL_YEARS)]
        p=val[(val.symbol==n.symbol)&(val.family==n.family)&(val.eff_threshold==n.eff_threshold)&(val.hold_min==n.hold_min)].iloc[0]
        pos=int((y.net_bp_per_trade_cost_1>0).sum())
        rows.append({"symbol":n.symbol,"status":"EVALUATED","family":n.family,"eff_threshold":float(n.eff_threshold),"hold_min":int(n.hold_min),
                     "validation_trades":int(p.trades),"positive_validation_slices":pos,"validation_break_even_bp":float(p.break_even_one_way_cost_bp),
                     "validation_net1_per_trade":float(p.net_bp_per_trade_cost_1),"validation_net1_per_exposure_min":float(p.net_bp_per_exposure_min_cost_1),
                     "q1_pool_net_positive":bool(p.net_bp_cost_1>0),"q2_two_positive_slices":bool(pos>=2),"q3_break_even_gt_1":bool(p.break_even_one_way_cost_bp>1),
                     "q4_trade_count_ge_30":bool(p.trades>=30),"q5_net_per_exposure_positive":bool(p.net_bp_per_exposure_min_cost_1>0)})
    return pd.DataFrame(rows)


def run(root:Path,out:Path):
    regime=load_module(root/"docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py","regime_onset")
    orig=load_module(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_onset")
    fg=load_module(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","grid_onset")
    annual_rows=[];trade_frames=[];receipts=[]
    for symbol in SYMBOLS:
        native=orig.load_native(root,symbol);state=regime.build_continuous_state(native,symbol)
        minute=fg.build_minute_grid(native,state.rename(columns={"vol_ratio":"recovery_ratio"}),symbol).reset_index(drop=True)
        onsets=build_onsets(minute)
        receipts.append({"symbol":symbol,"onsets":len(onsets),"first_day":minute.trading_day.min(),"last_day":minute.trading_day.max()})
        for family,thresholds in (("momentum",MOM_E),("reversal",REV_E)):
            for e in thresholds:
                for h in HOLDS:
                    tr=candidate_trade_rows(minute,onsets,family,e,h)
                    if len(tr): trade_frames.append(tr)
                    for year in DEV_YEARS+VAL_YEARS:
                        annual_rows.append(summarize(tr,symbol,year,family,e,h))
    annual=pd.DataFrame(annual_rows);dev=pool_years(annual,DEV_YEARS);val=pool_years(annual,VAL_YEARS);nom=nominate(annual,dev);ev=evaluate(annual,val,nom)
    trades=pd.concat(trade_frames,ignore_index=True) if trade_frames else pd.DataFrame()
    out.mkdir(parents=True,exist_ok=True)
    annual.to_csv(out/"annual_surface.csv",index=False);dev.to_csv(out/"development_pool_2021_2023.csv",index=False);val.to_csv(out/"validation_pool_2024_2026.csv",index=False);nom.to_csv(out/"development_nomination.csv",index=False);ev.to_csv(out/"validation_evaluation.csv",index=False);pd.DataFrame(receipts).to_csv(out/"onset_receipts.csv",index=False)
    # candidate-level trades only, not all-menu duplicate trades
    selected=[]
    for n in nom.itertuples(index=False):
        if n.nomination=="CANDIDATE" and len(trades):
            selected.append(trades[(trades.symbol==n.symbol)&(trades.family==n.family)&(trades.eff_threshold==n.eff_threshold)&(trades.hold_min==n.hold_min)])
    if selected: pd.concat(selected,ignore_index=True).to_csv(out/"selected_candidate_trades.csv",index=False)
    summary={"schema":"highvol_onset_path_v1","development_years":list(DEV_YEARS),"validation_years":[2024,2025,"2026_through_2026-08-21"],"blackbox_queried":False,"nomination":nom.to_dict(orient="records"),"evaluation":ev.to_dict(orient="records")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n");print(json.dumps(summary,default=str));return summary


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True);args=ap.parse_args();run(Path(args.repo_root).resolve(),Path(args.out))

if __name__=="__main__": main()
