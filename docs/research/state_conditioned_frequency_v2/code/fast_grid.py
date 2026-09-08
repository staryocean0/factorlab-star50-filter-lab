from __future__ import annotations

import numpy as np
import pandas as pd


def build_minute_grid(native: pd.DataFrame, state_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Vectorized exact equivalent of the session-local 1m grid used by session_grid."""
    days=pd.Index(sorted(native.trading_day.astype(str).str[:10].unique()),name="trading_day")
    parts=[]
    for half,base_minute in ((0,9*60+30),(1,13*60)):
        q=pd.MultiIndex.from_product([days,np.arange(1,121)],names=["trading_day","minute"]).to_frame(index=False)
        q["half"]=half
        q["session"]=q.trading_day.astype(str)+f"/{half}"
        q["timestamp"]=pd.to_datetime(q.trading_day)+pd.to_timedelta(base_minute+q.minute-1,unit="m")
        parts.append(q)
    grid=pd.concat(parts,ignore_index=True).sort_values(["trading_day","half","minute"],kind="stable").reset_index(drop=True)
    src=native.copy()
    src["trading_day"]=src.trading_day.astype(str).str[:10]
    keep=["trading_day","ts","open","high","low","close","high_frequency_analysis_eligible","causal_flat_fill"]
    src=src[keep].rename(columns={"ts":"timestamp"})
    grid=grid.merge(src,on=["trading_day","timestamp"],how="left",sort=False,validate="one_to_one")
    for c in ("open","high","low","close"):
        grid[c]=pd.to_numeric(grid[c],errors="coerce")
    good=grid.high_frequency_analysis_eligible.eq(True)&grid.causal_flat_fill.eq(False)
    for c in ("open","high","low","close"):
        good &= np.isfinite(grid[c])&(grid[c]>0)
    grid["valid"]=good.astype(bool)
    grid.loc[~good,["open","high","low","close"]]=np.nan
    st=state_df[["session","minute","route_state","recovery_ratio"]].copy()
    if st.duplicated(["session","minute"]).any():
        raise ValueError("duplicate route state key")
    grid=grid.merge(st,on=["session","minute"],how="left",sort=False,validate="one_to_one")
    grid["route_state"]=grid.route_state.fillna("Unknown")
    grid["symbol"]=symbol
    grid["year"]=grid.trading_day.str[:4].astype(int)
    return grid[["symbol","trading_day","year","session","minute","timestamp","open","high","low","close",
                 "valid","route_state","recovery_ratio"]].reset_index(drop=True)


def aggregate_scale(minute: pd.DataFrame, scale: int) -> pd.DataFrame:
    """Exact block aggregation of the prebuilt minute grid for divisors of 120."""
    if 120 % scale:
        raise ValueError("scale must divide 120")
    x=minute.copy()
    x["block"]=(x.minute.astype(int)-1)//scale
    keys=["symbol","trading_day","year","session","block"]
    g=x.groupby(keys,sort=False,dropna=False)
    out=g.agg(
        minute_count=("minute","size"),
        valid=("valid","all"),
        open=("open","first"),
        high=("high","max"),
        low=("low","min"),
        close=("close","last"),
    ).reset_index()
    # groupby.last skips NaN. Routing semantics require the exact final source
    # minute, including a NaN recovery_ratio during the initial Unsafe window.
    tail=g.tail(1)[keys+["timestamp","route_state","recovery_ratio","minute"]].copy()
    tail=tail.rename(columns={"minute":"bar_close_minute"})
    out=out.merge(tail,on=keys,how="left",sort=False,validate="one_to_one")
    out["valid"]=out.valid.astype(bool)&out.minute_count.eq(scale)
    bad=~out.valid
    out.loc[bad,["open","high","low","close"]]=np.nan
    out["scale_min"]=scale
    out["bar_in_session"]=out.block.astype(int)+1
    return out[["symbol","trading_day","year","session","scale_min","bar_in_session","bar_close_minute",
                "timestamp","open","high","low","close","valid","route_state","recovery_ratio"]].reset_index(drop=True)
