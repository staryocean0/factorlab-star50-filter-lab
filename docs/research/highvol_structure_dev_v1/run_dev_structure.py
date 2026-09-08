from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
HOLDS=(1,2,3,5,10)
DEV_START="2021-01-01"
DEV_END="2023-12-31"


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def _safe_eff(x:np.ndarray)->float:
    tv=float(np.sum(np.abs(x))); net=float(np.sum(x))
    if not np.isfinite(tv) or tv<=0: return np.nan
    return abs(net)/tv


def build_event_rows(minute:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for session,z0 in minute.groupby("session",sort=False):
        z=z0.sort_values("minute").reset_index(drop=True)
        state=z.route_state.to_numpy(object)
        close=z.close.to_numpy(float); op=z.open.to_numpy(float); valid=z.valid.to_numpy(bool)
        ratio=pd.to_numeric(z.recovery_ratio,errors="coerce").to_numpy(float)
        r=np.full(len(z),np.nan,float)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(close[i]) and np.isfinite(close[i-1]) and close[i]>0 and close[i-1]>0:
                r[i]=np.log(close[i]/close[i-1])*1e4
        for i in range(10,len(z)):
            if state[i]!="HighVol" or state[i-1]!="NormalVol": continue
            recent=r[i-4:i+1]; prior=r[i-9:i-4]
            if len(recent)!=5 or len(prior)!=5 or not np.isfinite(recent).all() or not np.isfinite(prior).all(): continue
            net=float(np.sum(recent)); tv=float(np.sum(np.abs(recent)))
            if tv<=0 or net==0: continue
            sign=1.0 if net>0 else -1.0
            first3=recent[:3]; last2=recent[3:]
            denom=max(float(np.mean(np.abs(first3))),1e-12)
            row={
                "symbol":z.symbol.iloc[0],"year":int(z.year.iloc[0]),"trading_day":z.trading_day.iloc[0],"session":session,
                "onset_minute":int(z.minute.iloc[i]),"onset_row":i,"vol_ratio":float(ratio[i]) if np.isfinite(ratio[i]) else np.nan,
                "net5_bp":net,"sign5":sign,"eff5":abs(net)/tv,
                "sign_agreement5":float(np.mean(np.sign(recent)==sign)),
                "tail1_share":abs(float(recent[-1]))/tv,
                "tail2_share":float(np.sum(np.abs(last2)))/tv,
                "accel_abs_2v3":float(np.mean(np.abs(last2)))/denom,
                "last1_bp":float(recent[-1]),"last2_net_bp":float(np.sum(last2)),
                "prior5_net_bp":float(np.sum(prior)),"prior5_eff":_safe_eff(prior),
                "prior5_same_direction":bool(np.sum(prior)!=0 and np.sign(np.sum(prior))==sign),
            }
            for h in HOLDS:
                entry=i+1; exit_=entry+h
                key=f"cont_{h}m_bp"
                if exit_>=len(z) or not valid[entry:exit_+1].all() or not (np.isfinite(op[entry]) and np.isfinite(op[exit_]) and op[entry]>0 and op[exit_]>0):
                    row[key]=np.nan
                else:
                    row[key]=sign*np.log(op[exit_]/op[entry])*1e4
            rows.append(row)
    return pd.DataFrame(rows)


BIN_SPECS={
    "eff5":([-np.inf,0.4,0.6,0.8,np.inf],["<0.4","0.4-0.6","0.6-0.8",">=0.8"]),
    "tail1_share":([-np.inf,0.2,0.4,0.6,np.inf],["<0.2","0.2-0.4","0.4-0.6",">=0.6"]),
    "tail2_share":([-np.inf,0.4,0.6,0.8,np.inf],["<0.4","0.4-0.6","0.6-0.8",">=0.8"]),
    "accel_abs_2v3":([-np.inf,0.75,1.25,2.0,np.inf],["<0.75","0.75-1.25","1.25-2",">=2"]),
    "prior5_eff":([-np.inf,0.4,0.6,0.8,np.inf],["<0.4","0.4-0.6","0.6-0.8",">=0.8"]),
    "vol_ratio":([-np.inf,2.0,3.0,5.0,np.inf],["1.5-2","2-3","3-5",">=5"]),
    "sign_agreement5":([-np.inf,0.6,0.8,0.999999, np.inf],["<=0.4","0.6","0.8","1.0"]),
}


def bin_table(events:pd.DataFrame)->pd.DataFrame:
    out=[]
    for feature,(edges,labels) in BIN_SPECS.items():
        b=pd.cut(events[feature],bins=edges,labels=labels,right=False,include_lowest=True)
        tmp=events.assign(_bin=b.astype(object))
        for (symbol,year,bin_name),z in tmp.groupby(["symbol","year","_bin"],dropna=True):
            for h in HOLDS:
                y=pd.to_numeric(z[f"cont_{h}m_bp"],errors="coerce").dropna()
                if len(y)==0: continue
                mean=float(y.mean())
                out.append({"symbol":symbol,"year":int(year),"feature":feature,"bin":str(bin_name),"hold_min":h,"n":len(y),
                            "mean_cont_bp":mean,"median_cont_bp":float(y.median()),"hit_rate":float((y>0).mean()),
                            "break_even_one_way_bp":mean/2.0,"mean_net1bp_roundtrip_bp":mean-2.0})
    # boolean persistence separately
    for (symbol,year,val),z in events.groupby(["symbol","year","prior5_same_direction"]):
        for h in HOLDS:
            y=pd.to_numeric(z[f"cont_{h}m_bp"],errors="coerce").dropna()
            if len(y)==0: continue
            mean=float(y.mean())
            out.append({"symbol":symbol,"year":int(year),"feature":"prior5_same_direction","bin":str(bool(val)),"hold_min":h,"n":len(y),
                        "mean_cont_bp":mean,"median_cont_bp":float(y.median()),"hit_rate":float((y>0).mean()),
                        "break_even_one_way_bp":mean/2.0,"mean_net1bp_roundtrip_bp":mean-2.0})
    return pd.DataFrame(out)


def pooled_bins(annual_bins:pd.DataFrame)->pd.DataFrame:
    # Pool raw event counts approximately correctly by n-weighted means. Median is deliberately omitted.
    rows=[]
    keys=["symbol","feature","bin","hold_min"]
    for key,z in annual_bins.groupby(keys,dropna=False):
        n=int(z.n.sum())
        if n<=0: continue
        mean=float(np.average(z.mean_cont_bp,weights=z.n))
        hit=float(np.average(z.hit_rate,weights=z.n))
        rows.append(dict(zip(keys,key)) | {"n":n,"mean_cont_bp":mean,"hit_rate":hit,"break_even_one_way_bp":mean/2.0,
                    "mean_net1bp_roundtrip_bp":mean-2.0,"positive_years_net1":int((z.mean_net1bp_roundtrip_bp>0).sum())})
    return pd.DataFrame(rows)


def corr_table(events:pd.DataFrame)->pd.DataFrame:
    features=["eff5","tail1_share","tail2_share","accel_abs_2v3","prior5_eff","vol_ratio","sign_agreement5"]
    rows=[]
    for symbol,z0 in events.groupby("symbol"):
        for feature in features:
            for h in HOLDS:
                z=z0[[feature,f"cont_{h}m_bp"]].replace([np.inf,-np.inf],np.nan).dropna()
                if len(z)<10: continue
                rows.append({"symbol":symbol,"feature":feature,"hold_min":h,"n":len(z),
                             "pearson":float(z[feature].corr(z[f"cont_{h}m_bp"],method="pearson")),
                             "spearman":float(z[feature].corr(z[f"cont_{h}m_bp"],method="spearman"))})
    return pd.DataFrame(rows)


def run(root:Path,out:Path):
    regime=load_module(root/"docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py","regime_struct")
    orig=load_module(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_struct")
    fg=load_module(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","grid_struct")
    frames=[];receipts=[]
    for symbol in SYMBOLS:
        native=orig.load_native(root,symbol).copy()
        native["trading_day"]=native.trading_day.astype(str).str[:10]
        native=native[native.trading_day<=DEV_END].copy()
        state=regime.build_continuous_state(native,symbol)
        minute=fg.build_minute_grid(native,state.rename(columns={"vol_ratio":"recovery_ratio"}),symbol).reset_index(drop=True)
        minute=minute[(minute.trading_day>=DEV_START)&(minute.trading_day<=DEV_END)].reset_index(drop=True)
        ev=build_event_rows(minute)
        frames.append(ev)
        receipts.append({"symbol":symbol,"events":len(ev),"first_day":ev.trading_day.min() if len(ev) else None,"last_day":ev.trading_day.max() if len(ev) else None})
    events=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
    annual=bin_table(events);pooled=pooled_bins(annual);corr=corr_table(events)
    out.mkdir(parents=True,exist_ok=True)
    events.to_csv(out/"development_onsets.csv",index=False)
    annual.to_csv(out/"annual_bin_map.csv",index=False)
    pooled.to_csv(out/"pooled_bin_map.csv",index=False)
    corr.to_csv(out/"feature_correlations.csv",index=False)
    pd.DataFrame(receipts).to_csv(out/"receipts.csv",index=False)
    summary={"schema":"highvol_structure_dev_v1","development_only":True,"development_start":DEV_START,"development_end":DEV_END,
             "validation_inspected":False,"blackbox_queried":False,"events":receipts}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print(json.dumps(summary,default=str))


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=="__main__": main()
