from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SCALES=(1,2,3,5,10,15)
FAMILIES=("scaled_clock","fixed_physical")
GATES=("Ungated","NoEpisode","Unsafe","Recovering")
COSTS=(0.5,1.0,2.0,3.0,5.0)
SYMBOLS=("000688.SH","000852.SH")
YEARS_EVAL=(2021,2022,2023,2024,2025,2026)


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def load_native(root:Path,symbol:str)->pd.DataFrame:
    frames=[]
    for year in range(2020,2026):
        p=root/f"data/cross_index_risk_gate_v1/1m/{symbol}/{year}.parquet"
        if p.exists(): frames.append(pd.read_parquet(p))
    p26=root/f"data/cross_index_risk_gate_2026_v1/1m/{symbol}/2026.parquet"
    if p26.exists(): frames.append(pd.read_parquet(p26))
    if not frames: raise FileNotFoundError(symbol)
    x=pd.concat(frames,ignore_index=True)
    x["trading_day"]=x.trading_day.astype(str).str[:10]
    x["ts"]=pd.to_datetime(x.timestamp.astype(str).str[:19])
    return x.sort_values(["trading_day","ts"],kind="stable").reset_index(drop=True)


def route_states(state_mod,native:pd.DataFrame,symbol:str)->pd.DataFrame:
    panel=state_mod.build_panel(native,symbol)
    rows=[]
    for session,z0 in panel.groupby("session",sort=False):
        z=z0.sort_values("minute").reset_index(drop=True)
        r=z.return_bp.to_numpy(float); first=z["first"].to_numpy(float); mins=z.minute.to_numpy(int)
        latest=None; sig=np.nan
        for i in range(len(z)):
            if first[i]==1 and mins[i]>=33 and np.isfinite(z.loc[i,"sigma_pre"]) and float(z.loc[i,"sigma_pre"])>0:
                latest=i;sig=float(z.loc[i,"sigma_pre"])
            if latest is None:
                state="NoEpisode";ratio=np.nan
            else:
                lag=i-latest
                if lag<5:
                    state="Unsafe";ratio=np.nan
                else:
                    a=r[i-4:i+1]
                    if len(a)!=5 or not np.isfinite(a).all():
                        state="Unknown";ratio=np.nan
                    else:
                        ratio=float(np.sqrt(np.mean(a*a))/sig)
                        state="Unsafe" if ratio>=1.5 else "Recovering"
            rows.append({"session":session,"minute":int(mins[i]),"route_state":state,"recovery_ratio":ratio})
    return pd.DataFrame(rows)


def session_grid(native:pd.DataFrame,state_df:pd.DataFrame,symbol:str,scale:int)->pd.DataFrame:
    st=state_df.set_index(["session","minute"])
    rows=[]
    need=("open","high","low","close")
    for day,zday in native.groupby("trading_day",sort=True):
        for afternoon,start in [(0,pd.Timestamp(f"{day} 09:30:00")),(1,pd.Timestamp(f"{day} 13:00:00"))]:
            session=f"{day}/{afternoon}"
            times=pd.date_range(start,periods=120,freq="1min")
            z=zday.set_index("ts").reindex(times)
            good=z.high_frequency_analysis_eligible.eq(True)&z.causal_flat_fill.eq(False)
            for c in need:
                vals=pd.to_numeric(z[c],errors="coerce")
                good &= np.isfinite(vals)&(vals>0)
            for b0 in range(0,120,scale):
                b1=b0+scale
                q=z.iloc[b0:b1]
                valid=bool(len(q)==scale and good.iloc[b0:b1].all())
                close_minute=b1
                try:
                    state=st.loc[(session,close_minute),"route_state"]
                    ratio=st.loc[(session,close_minute),"recovery_ratio"]
                except KeyError:
                    state="Unknown";ratio=np.nan
                if valid:
                    op=float(q.open.iloc[0]);hi=float(pd.to_numeric(q.high).max());lo=float(pd.to_numeric(q.low).min());cl=float(q.close.iloc[-1])
                else:
                    op=hi=lo=cl=np.nan
                rows.append({"symbol":symbol,"trading_day":day,"year":int(str(day)[:4]),"session":session,
                    "scale_min":scale,"bar_in_session":b0//scale+1,"bar_close_minute":close_minute,
                    "timestamp":times[b1-1],"open":op,"high":hi,"low":lo,"close":cl,"valid":valid,
                    "route_state":state,"recovery_ratio":ratio})
    return pd.DataFrame(rows)


def contiguous_runs(mask:np.ndarray):
    mask=np.asarray(mask,bool);n=len(mask);i=0
    while i<n:
        while i<n and not mask[i]: i+=1
        if i>=n: break
        j=i+1
        while j<n and mask[j]: j+=1
        yield i,j
        i=j


def base_signal(filters, bars:pd.DataFrame, family:str, scale:int)->tuple[np.ndarray,np.ndarray,np.ndarray]:
    if family=="scaled_clock": period=12;window=48
    elif family=="fixed_physical": period=60//scale;window=240//scale
    else: raise ValueError(family)
    close=bars.close.to_numpy(float)
    valid=np.isfinite(close)&(close>0)&bars.valid.to_numpy(bool)
    low=np.full(len(bars),np.nan);sigma=np.full(len(bars),np.nan);sigpos=np.zeros(len(bars))
    for a,b in contiguous_runs(valid):
        logc=np.log(close[a:b])
        if len(logc)<3: continue
        lp=filters.butter_lowpass(logc,period_bars=period,order=1)
        diff=pd.Series(logc).diff()
        s=diff.rolling(window,min_periods=window).std(ddof=0).to_numpy()
        p=filters.hysteresis_positions(lp,s)
        low[a:b]=lp;sigma[a:b]=s;sigpos[a:b]=p
    return sigpos,low,sigma


def simulate_gate(bars:pd.DataFrame, signal:np.ndarray, gate:str)->dict:
    if gate=="Ungated": allow=bars.valid.to_numpy(bool)
    else: allow=bars.valid.to_numpy(bool)&bars.route_state.eq(gate).to_numpy(bool)
    desired=np.where(allow,signal,0.0)
    gross=0.0;turn=0.0;exp_bars=0;booked=0;wins=0
    # The research router is intraday: every half-session starts/ends flat.
    for _,idx in bars.groupby("session",sort=False).indices.items():
        ix=np.asarray(idx,int)
        op=bars.open.to_numpy(float)[ix];d=desired[ix]
        valid=np.isfinite(op)&(op>0)&bars.valid.to_numpy(bool)[ix]
        for a,b in contiguous_runs(valid):
            oo=op[a:b];ss=d[a:b];n=len(oo)
            if n==0: continue
            ep=np.zeros(n,float)
            if n>2: ep[2:]=ss[:-2]
            fwd=np.zeros(n,float)
            if n>1: fwd[1:]=np.log(oo[1:]/oo[:-1])*1e4
            pnl=ep*fwd
            gross+=float(np.sum(pnl))
            changes=np.abs(np.diff(np.r_[0.0,ep,0.0]))
            turn+=float(np.sum(changes))
            active=ep!=0
            exp_bars+=int(active.sum());booked+=int(active.sum());wins+=int((pnl[active]>0).sum())
    return {"gross_bp":gross,"one_way_turnover":turn,"exposure_bars":exp_bars,
        "booked_returns":booked,"winning_returns":wins}


def summarize_one(bars,signal,family,scale,gate,symbol,year):
    z=bars[bars.year==year].copy()
    # signal array is on full chronology; align by retained integer index.
    s=signal[z.index.to_numpy(int)]
    q=simulate_gate(z.reset_index(drop=True),s,gate)
    q.update({"symbol":symbol,"year":year,"family":family,"scale_min":scale,"gate":gate})
    q["exposure_minutes"]=q["exposure_bars"]*scale
    q["gross_bp_per_exposure_min"]=q["gross_bp"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
    q["break_even_one_way_cost_bp"]=q["gross_bp"]/q["one_way_turnover"] if q["one_way_turnover"] else np.nan
    q["hit_rate"]=q["winning_returns"]/q["booked_returns"] if q["booked_returns"] else np.nan
    for c in COSTS:
        q[f"net_bp_cost_{c:g}"]=q["gross_bp"]-c*q["one_way_turnover"]
        q[f"net_bp_per_exposure_min_cost_{c:g}"]=q[f"net_bp_cost_{c:g}"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
    return q


def summarize_all_gates(bars:pd.DataFrame,signal:np.ndarray,family:str,scale:int,symbol:str)->list[dict]:
    """Exact single-pass equivalent of repeated summarize_one calls.

    It preserves session order, contiguous-valid-run boundaries, two-bar latency,
    gate-at-decision semantics, forced-flat turnover, and floating summation order.
    The only change is avoiding 24 repeated scans of the same bar path.
    """
    acc={(year,gate):{"gross_bp":0.0,"one_way_turnover":0.0,"exposure_bars":0,
                     "booked_returns":0,"winning_returns":0}
         for year in YEARS_EVAL for gate in GATES}
    opens=bars.open.to_numpy(float)
    valid_all=bars.valid.to_numpy(bool)
    states=bars.route_state.to_numpy(object)
    years=bars.year.to_numpy(int)
    for _,idx in bars.groupby("session",sort=False).indices.items():
        ix=np.asarray(idx,int)
        year=int(years[ix[0]])
        if year not in YEARS_EVAL: continue
        op=opens[ix];valid=np.isfinite(op)&(op>0)&valid_all[ix]
        sig=signal[ix];st=states[ix]
        for a,b in contiguous_runs(valid):
            oo=op[a:b];ss=sig[a:b];state_run=st[a:b];n=len(oo)
            if n==0: continue
            fwd=np.zeros(n,float)
            if n>1: fwd[1:]=np.log(oo[1:]/oo[:-1])*1e4
            for gate in GATES:
                desired=ss if gate=="Ungated" else np.where(state_run==gate,ss,0.0)
                ep=np.zeros(n,float)
                if n>2: ep[2:]=desired[:-2]
                pnl=ep*fwd
                q=acc[(year,gate)]
                q["gross_bp"]+=float(np.sum(pnl))
                q["one_way_turnover"]+=float(np.sum(np.abs(np.diff(np.r_[0.0,ep,0.0]))))
                active=ep!=0
                count=int(active.sum())
                q["exposure_bars"]+=count;q["booked_returns"]+=count
                q["winning_returns"]+=int((pnl[active]>0).sum())
    rows=[]
    for year in YEARS_EVAL:
        for gate in GATES:
            q=dict(acc[(year,gate)])
            q.update({"symbol":symbol,"year":year,"family":family,"scale_min":scale,"gate":gate})
            q["exposure_minutes"]=q["exposure_bars"]*scale
            q["gross_bp_per_exposure_min"]=q["gross_bp"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
            q["break_even_one_way_cost_bp"]=q["gross_bp"]/q["one_way_turnover"] if q["one_way_turnover"] else np.nan
            q["hit_rate"]=q["winning_returns"]/q["booked_returns"] if q["booked_returns"] else np.nan
            for c in COSTS:
                q[f"net_bp_cost_{c:g}"]=q["gross_bp"]-c*q["one_way_turnover"]
                q[f"net_bp_per_exposure_min_cost_{c:g}"]=q[f"net_bp_cost_{c:g}"]/q["exposure_minutes"] if q["exposure_minutes"] else np.nan
            rows.append(q)
    return rows


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


def run(root:Path,out:Path):
    state_mod=load_module(root/"docs/research/post_shock_recovery_v1/code/state_sufficiency.py","state_builder")
    filters=load_module(root/"src/star50_filter/filters.py","filters")
    rows=[];anchor=[];bar_receipts=[]
    for symbol in SYMBOLS:
        native=load_native(root,symbol)
        states=route_states(state_mod,native,symbol)
        for scale in SCALES:
            bars=session_grid(native,states,symbol,scale).reset_index(drop=True)
            bar_receipts.append({"symbol":symbol,"scale_min":scale,"rows":len(bars),"valid":int(bars.valid.sum()),
                "first_day":bars.trading_day.min(),"last_day":bars.trading_day.max()})
            for family in FAMILIES:
                sig,low,sigma=base_signal(filters,bars,family,scale)
                if scale==5:
                    anchor.append({"symbol":symbol,"family":family,"signal_sha":__import__('hashlib').sha256(np.asarray(sig,dtype='<f8').tobytes()).hexdigest(),
                        "low_sha":__import__('hashlib').sha256(np.asarray(low,dtype='<f8').tobytes()).hexdigest(),
                        "sigma_sha":__import__('hashlib').sha256(np.asarray(sigma,dtype='<f8').tobytes()).hexdigest()})
                rows.extend(summarize_all_gates(bars,sig,family,scale,symbol))
    annual=pd.DataFrame(rows)
    pool=pool_years(annual,(2021,2022,2023,2024,2025))
    replay=pool_years(annual,(2026,))
    anchor_df=pd.DataFrame(anchor)
    # 5m scaled/fixed must be byte-identical signal/filter/sigma paths for each symbol.
    anchor_ok=True
    for symbol,z in anchor_df.groupby("symbol"):
        anchor_ok &= z.signal_sha.nunique()==1 and z.low_sha.nunique()==1 and z.sigma_sha.nunique()==1
    out.mkdir(parents=True,exist_ok=True)
    annual.to_csv(out/"annual_surface.csv",index=False)
    pool.to_csv(out/"pool_2021_2025.csv",index=False)
    replay.to_csv(out/"replay_2026.csv",index=False)
    pd.DataFrame(bar_receipts).to_csv(out/"bar_receipts.csv",index=False)
    anchor_df.to_csv(out/"five_minute_anchor.csv",index=False)
    result={"schema":"state_conditioned_physical_scale_v2","scales":list(SCALES),"families":list(FAMILIES),"gates":list(GATES),
        "costs_one_way_bp":list(COSTS),"five_minute_anchor_identical":bool(anchor_ok),
        "guardrails":["2021-2025 consumed exploratory history","2026 already-opened consistency replay only",
            "NoEpisode is pre-trigger reference, not Clean","half-session positions forced flat","no scale selection",
            "single-pass settlement is exact-equivalent engineering optimization only"]}
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    if not anchor_ok: raise RuntimeError("5m family anchor mismatch")
    print(json.dumps(result))
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    args=ap.parse_args();run(Path(args.repo_root).resolve(),Path(args.out))

if __name__=="__main__": main()
