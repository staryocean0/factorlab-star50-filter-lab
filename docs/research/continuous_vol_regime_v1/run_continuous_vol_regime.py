from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SCALES=(1,2,3,5,10,15)
FAMILIES=("scaled_clock","fixed_physical")
GATES=("Ungated","HighVol","NormalVol")
SYMBOLS=("000688.SH","000852.SH")
DEV_YEARS=(2021,2022,2023)
VAL_YEARS=(2024,2025,2026)
COSTS=(0.5,1.0,2.0,3.0,5.0)


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def build_continuous_state(native:pd.DataFrame,symbol:str)->pd.DataFrame:
    rows=[]
    native=native.copy()
    native["trading_day"]=native.trading_day.astype(str).str[:10]
    native["ts"]=pd.to_datetime(native.timestamp.astype(str).str[:19])
    for day,zday in native.groupby("trading_day",sort=True):
        indexed=zday.set_index("ts")
        for afternoon,start in [(0,pd.Timestamp(f"{day} 09:30:00")),(1,pd.Timestamp(f"{day} 13:00:00"))]:
            session=f"{day}/{afternoon}"
            times=pd.date_range(start,periods=120,freq="1min")
            z=indexed.reindex(times)
            close=pd.to_numeric(z.close,errors="coerce")
            valid=z.high_frequency_analysis_eligible.eq(True)&z.causal_flat_fill.eq(False)&np.isfinite(close)&(close>0)
            logc=np.where(valid,np.log(close.to_numpy(float)),np.nan)
            r=np.full(120,np.nan,float)
            for i in range(1,120):
                if np.isfinite(logc[i]) and np.isfinite(logc[i-1]): r[i]=(logc[i]-logc[i-1])*1e4
            sq=pd.Series(r*r)
            fast=np.sqrt(sq.rolling(5,min_periods=5).mean()).to_numpy()
            bg=np.sqrt(sq.shift(5).rolling(30,min_periods=30).mean()).to_numpy()
            ratio=fast/np.maximum(bg,1.0)
            state=np.full(120,"Unknown",object)
            known=np.isfinite(ratio)
            state[known & (ratio>=1.5)]="HighVol"
            state[known & (ratio<1.5)]="NormalVol"
            for i in range(120):
                rows.append({"session":session,"minute":i+1,"route_state":state[i],"vol_ratio":ratio[i] if np.isfinite(ratio[i]) else np.nan})
    return pd.DataFrame(rows)


def summarize_one(orig,bars,signal,gate,symbol,year,family,scale):
    z=bars[bars.year==year].copy()
    s=signal[z.index.to_numpy(int)]
    q=orig.simulate_gate(z.reset_index(drop=True),s,gate)
    q.update({"symbol":symbol,"year":year,"family":family,"scale_min":scale,"gate":gate})
    q["exposure_minutes"]=q["exposure_bars"]*scale
    q["gross_bp_per_exposure_min"]=q["gross_bp"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
    q["break_even_one_way_cost_bp"]=q["gross_bp"]/q["one_way_turnover"] if q["one_way_turnover"] else np.nan
    q["hit_rate"]=q["winning_returns"]/q["booked_returns"] if q["booked_returns"] else np.nan
    for c in COSTS:
        q[f"net_bp_cost_{c:g}"]=q["gross_bp"]-c*q["one_way_turnover"]
        q[f"net_bp_per_exposure_min_cost_{c:g}"]=q[f"net_bp_cost_{c:g}"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
    return q


def pool_years(df:pd.DataFrame,years)->pd.DataFrame:
    x=df[df.year.isin(years)].copy()
    keys=["symbol","family","scale_min","gate"]
    sums=x.groupby(keys)[["gross_bp","one_way_turnover","exposure_bars","exposure_minutes","booked_returns","winning_returns"]].sum().reset_index()
    sums["gross_bp_per_exposure_min"]=sums.gross_bp/sums.exposure_minutes.replace(0,np.nan)
    sums["break_even_one_way_cost_bp"]=sums.gross_bp/sums.one_way_turnover.replace(0,np.nan)
    sums["hit_rate"]=sums.winning_returns/sums.booked_returns.replace(0,np.nan)
    for c in COSTS:
        sums[f"net_bp_cost_{c:g}"]=sums.gross_bp-c*sums.one_way_turnover
        sums[f"net_bp_per_exposure_min_cost_{c:g}"]=sums[f"net_bp_cost_{c:g}"]/sums.exposure_minutes.replace(0,np.nan)
    return sums


def nominate(annual:pd.DataFrame,dev_pool:pd.DataFrame)->pd.DataFrame:
    rows=[]
    high=annual[(annual.gate=="HighVol")&(annual.year.isin(DEV_YEARS))]
    pooled=dev_pool[dev_pool.gate=="HighVol"]
    for symbol in SYMBOLS:
        candidates=[]
        for family in FAMILIES:
            for scale in SCALES:
                y=high[(high.symbol==symbol)&(high.family==family)&(high.scale_min==scale)]
                p=pooled[(pooled.symbol==symbol)&(pooled.family==family)&(pooled.scale_min==scale)]
                if len(y)!=3 or len(p)!=1: continue
                all_exposure=bool((y.exposure_minutes>0).all())
                positive_years=int((y["net_bp_per_exposure_min_cost_1"]>0).sum())
                eligible=all_exposure and positive_years>=2
                score=float(p.iloc[0]["net_bp_per_exposure_min_cost_1"])
                candidates.append((eligible,score,scale,0 if family=="fixed_physical" else 1,family,positive_years,all_exposure))
        eligible=[x for x in candidates if x[0]]
        if not eligible:
            rows.append({"symbol":symbol,"nomination":"NONE","family":None,"scale_min":None,"dev_score_net1_per_min":np.nan,"positive_dev_years":0})
        else:
            # highest score; deterministic tie breaker lower scale then fixed_physical
            eligible=sorted(eligible,key=lambda x:(-x[1],x[2],x[3]))
            x=eligible[0]
            rows.append({"symbol":symbol,"nomination":"CANDIDATE","family":x[4],"scale_min":x[2],"dev_score_net1_per_min":x[1],"positive_dev_years":x[5]})
    return pd.DataFrame(rows)


def evaluate_nomination(annual:pd.DataFrame,dev_pool:pd.DataFrame,val_pool:pd.DataFrame,nom:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for n in nom.itertuples(index=False):
        if n.nomination!="CANDIDATE":
            rows.append({"symbol":n.symbol,"status":"NO_DEV_CANDIDATE"});continue
        symbol=n.symbol;family=n.family;scale=int(n.scale_min)
        val_y=annual[(annual.symbol==symbol)&(annual.family==family)&(annual.scale_min==scale)&(annual.gate=="HighVol")&(annual.year.isin(VAL_YEARS))]
        val_p=val_pool[(val_pool.symbol==symbol)&(val_pool.family==family)&(val_pool.scale_min==scale)&(val_pool.gate=="HighVol")]
        norm_p=val_pool[(val_pool.symbol==symbol)&(val_pool.family==family)&(val_pool.scale_min==scale)&(val_pool.gate=="NormalVol")]
        anchor=val_pool[(val_pool.symbol==symbol)&(val_pool.family=="fixed_physical")&(val_pool.scale_min==5)&(val_pool.gate=="HighVol")]
        if len(val_p)!=1 or len(norm_p)!=1 or len(anchor)!=1: raise RuntimeError("validation lookup failed")
        vp=val_p.iloc[0];npool=norm_p.iloc[0];a=anchor.iloc[0]
        positive_slices=int((val_y["net_bp_per_exposure_min_cost_1"]>0).sum())
        rows.append({
            "symbol":symbol,"status":"EVALUATED","family":family,"scale_min":scale,
            "positive_validation_slices":positive_slices,
            "validation_pooled_net1_per_min":float(vp["net_bp_per_exposure_min_cost_1"]),
            "validation_break_even_cost_bp":float(vp["break_even_one_way_cost_bp"]),
            "validation_normal_net1_per_min":float(npool["net_bp_per_exposure_min_cost_1"]),
            "validation_high_minus_normal_net1_per_min":float(vp["net_bp_per_exposure_min_cost_1"]-npool["net_bp_per_exposure_min_cost_1"]),
            "validation_5m_anchor_net1_per_min":float(a["net_bp_per_exposure_min_cost_1"]),
            "validation_candidate_minus_5m_net1_per_min":float(vp["net_bp_per_exposure_min_cost_1"]-a["net_bp_per_exposure_min_cost_1"]),
            "q1_positive_two_slices_and_pool":bool(positive_slices>=2 and vp["net_bp_per_exposure_min_cost_1"]>0),
            "q2_break_even_gt_1bp":bool(vp["break_even_one_way_cost_bp"]>1.0),
            "q3_high_outperforms_normal":bool(vp["net_bp_per_exposure_min_cost_1"]>npool["net_bp_per_exposure_min_cost_1"]),
            "q4_outperforms_5m_anchor":bool(vp["net_bp_per_exposure_min_cost_1"]>a["net_bp_per_exposure_min_cost_1"]),
        })
    return pd.DataFrame(rows)


def run(root:Path,out:Path):
    orig=load_module(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_orig")
    fg=load_module(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","phase2_grid")
    filters=orig.load_module(root/"src/star50_filter/filters.py","filters_cont")
    rows=[];receipts=[];state_receipts=[]
    for symbol in SYMBOLS:
        native=orig.load_native(root,symbol)
        state=build_continuous_state(native,symbol)
        state_receipts.append({"symbol":symbol,"rows":len(state),"high_minutes":int((state.route_state=="HighVol").sum()),"normal_minutes":int((state.route_state=="NormalVol").sum()),"unknown_minutes":int((state.route_state=="Unknown").sum())})
        minute=fg.build_minute_grid(native,state.rename(columns={"vol_ratio":"recovery_ratio"}),symbol)
        for scale in SCALES:
            bars=fg.aggregate_scale(minute,scale).reset_index(drop=True)
            receipts.append({"symbol":symbol,"scale_min":scale,"rows":len(bars),"valid":int(bars.valid.sum()),"first_day":bars.trading_day.min(),"last_day":bars.trading_day.max()})
            for family in FAMILIES:
                sig,_,_=orig.base_signal(filters,bars,family,scale)
                for year in DEV_YEARS+VAL_YEARS:
                    for gate in GATES:
                        rows.append(summarize_one(orig,bars,sig,gate,symbol,year,family,scale))
    annual=pd.DataFrame(rows)
    dev_pool=pool_years(annual,DEV_YEARS)
    val_pool=pool_years(annual,VAL_YEARS)
    nom=nominate(annual,dev_pool)
    evaluation=evaluate_nomination(annual,dev_pool,val_pool,nom)
    out.mkdir(parents=True,exist_ok=True)
    annual.to_csv(out/"annual_surface.csv",index=False)
    dev_pool.to_csv(out/"development_pool_2021_2023.csv",index=False)
    val_pool.to_csv(out/"validation_pool_2024_2026.csv",index=False)
    nom.to_csv(out/"development_nomination.csv",index=False)
    evaluation.to_csv(out/"validation_evaluation.csv",index=False)
    pd.DataFrame(receipts).to_csv(out/"bar_receipts.csv",index=False)
    pd.DataFrame(state_receipts).to_csv(out/"state_receipts.csv",index=False)
    summary={"schema":"continuous_vol_regime_v1","threshold":1.5,"background_floor_bp":1.0,"fast_window_min":5,"background_window_min":30,"overlap":False,"development_years":list(DEV_YEARS),"validation_years":[2024,2025,"2026_through_2026-08-21"],"blackbox_queried":False,"nomination":nom.to_dict(orient="records"),"evaluation":evaluation.to_dict(orient="records")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print(json.dumps(summary,default=str))
    return summary


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    args=ap.parse_args();run(Path(args.repo_root).resolve(),Path(args.out))

if __name__=="__main__": main()
