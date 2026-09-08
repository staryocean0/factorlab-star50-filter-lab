from __future__ import annotations

import numpy as np
import pandas as pd


def build_minute_grid(native: pd.DataFrame, state_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Build the same session-local 1m grid used by session_grid, once per symbol."""
    st = state_df.set_index(["session", "minute"])
    rows=[]
    need=("open","high","low","close")
    for day,zday in native.groupby("trading_day",sort=True):
        indexed=zday.set_index("ts")
        for afternoon,start in [(0,pd.Timestamp(f"{day} 09:30:00")),(1,pd.Timestamp(f"{day} 13:00:00"))]:
            session=f"{day}/{afternoon}"
            times=pd.date_range(start,periods=120,freq="1min")
            z=indexed.reindex(times)
            good=z.high_frequency_analysis_eligible.eq(True)&z.causal_flat_fill.eq(False)
            numeric={}
            for c in need:
                numeric[c]=pd.to_numeric(z[c],errors="coerce")
                good &= np.isfinite(numeric[c])&(numeric[c]>0)
            for k,t in enumerate(times,1):
                try:
                    state=st.loc[(session,k),"route_state"]
                    ratio=st.loc[(session,k),"recovery_ratio"]
                except KeyError:
                    state="Unknown";ratio=np.nan
                rows.append({"symbol":symbol,"trading_day":day,"year":int(str(day)[:4]),"session":session,
                    "minute":k,"timestamp":t,"open":float(numeric["open"].iloc[k-1]) if good.iloc[k-1] else np.nan,
                    "high":float(numeric["high"].iloc[k-1]) if good.iloc[k-1] else np.nan,
                    "low":float(numeric["low"].iloc[k-1]) if good.iloc[k-1] else np.nan,
                    "close":float(numeric["close"].iloc[k-1]) if good.iloc[k-1] else np.nan,
                    "valid":bool(good.iloc[k-1]),"route_state":state,"recovery_ratio":ratio})
    return pd.DataFrame(rows)


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
        timestamp=("timestamp","last"),
        open=("open","first"),
        high=("high","max"),
        low=("low","min"),
        close=("close","last"),
        route_state=("route_state","last"),
        recovery_ratio=("recovery_ratio","last"),
        bar_close_minute=("minute","last"),
    ).reset_index()
    out["valid"]=out.valid.astype(bool)&out.minute_count.eq(scale)
    bad=~out.valid
    out.loc[bad,["open","high","low","close"]]=np.nan
    out["scale_min"]=scale
    out["bar_in_session"]=out.block.astype(int)+1
    return out[["symbol","trading_day","year","session","scale_min","bar_in_session","bar_close_minute",
                "timestamp","open","high","low","close","valid","route_state","recovery_ratio"]].reset_index(drop=True)
