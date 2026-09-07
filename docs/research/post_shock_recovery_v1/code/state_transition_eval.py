"""Frozen evaluator for future independent post-shock state snapshots."""
from __future__ import annotations

import numpy as np
import pandas as pd

CHECKPOINTS=(5,10,15,20)
SEED=20260907


def state_band(x: float) -> str:
    if not np.isfinite(x):
        return "Unknown"
    if x >= 1.5:
        return "Unsafe"
    if x >= 1.0:
        return "Recovering-high"
    return "Recovering-low"


def build_checkpoints(panel: pd.DataFrame) -> pd.DataFrame:
    required={"symbol","session","minute","return_bp","first","sigma_pre"}
    missing=required-set(panel.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    rows=[]
    for (symbol,session), z0 in panel.groupby(["symbol","session"], sort=False):
        z=z0.sort_values("minute").reset_index(drop=True)
        mins=z.minute.to_numpy(int)
        if len(np.unique(mins)) != len(mins):
            raise ValueError("duplicate session minute")
        r=z.return_bp.to_numpy(float)
        first=z["first"].to_numpy(float)
        for j in np.flatnonzero(first==1):
            if mins[j] < 33:
                continue
            sig=float(z.loc[j,"sigma_pre"])
            if not (np.isfinite(sig) and sig>0):
                continue
            key=f"{symbol}|{session}|{mins[j]}"
            for cp in CHECKPOINTS:
                a=r[j+cp-4:j+cp+1]
                b=r[j+cp+1:j+cp+6]
                if len(a)!=5 or len(b)!=5 or not np.isfinite(a).all() or not np.isfinite(b).all():
                    continue
                cur=float(np.sqrt(np.mean(a*a))/sig)
                nxt=float(np.sqrt(np.mean(b*b))/sig)
                rows.append({"key":key,"symbol":symbol,"session":session,"event_minute":int(mins[j]),
                             "checkpoint":cp,"current_ratio":cur,"next_ratio":nxt,
                             "current_state":state_band(cur),"next_state":state_band(nxt),
                             "next_unsafe":bool(nxt>=1.5)})
    return pd.DataFrame(rows)


def transition_matrix(checkpoints: pd.DataFrame):
    order=["Recovering-low","Recovering-high","Unsafe"]
    counts=pd.crosstab(checkpoints.current_state, checkpoints.next_state).reindex(index=order,columns=order,fill_value=0)
    probs=counts.div(counts.sum(axis=1).replace(0,np.nan),axis=0)
    return counts,probs


def continuous_metrics(checkpoints: pd.DataFrame) -> dict:
    x=checkpoints.current_ratio.to_numpy(float)
    y=checkpoints.next_ratio.to_numpy(float)
    if len(x)<2:
        return {"n":len(x),"spearman":None,"log_rmse":None}
    rx=pd.Series(x).rank(method="average").to_numpy()
    ry=pd.Series(y).rank(method="average").to_numpy()
    spearman=float(np.corrcoef(rx,ry)[0,1])
    log_rmse=float(np.sqrt(np.mean((np.log(x)-np.log(y))**2)))
    return {"n":len(x),"spearman":spearman,"log_rmse":log_rmse}


def cluster_bootstrap_unsafe_minus_low(checkpoints: pd.DataFrame, repeats=10_000, seed=SEED) -> dict:
    states=["Unsafe","Recovering-low"]
    keys=list(checkpoints.key.unique())
    if not keys:
        return {"repeats":0,"median":None,"ci95":[None,None]}
    arr=np.zeros((len(keys),2,2),float)
    ki={k:i for i,k in enumerate(keys)}
    si={s:i for i,s in enumerate(states)}
    for row in checkpoints.itertuples(index=False):
        if row.current_state not in si:
            continue
        i=ki[row.key]; j=si[row.current_state]
        arr[i,j,0]+=float(row.next_unsafe); arr[i,j,1]+=1
    rng=np.random.default_rng(seed); vals=[]
    n=len(keys)
    for _ in range(int(repeats)):
        idx=rng.integers(0,n,size=n)
        s=arr[idx].sum(axis=0)
        if s[0,1] and s[1,1]:
            vals.append(s[0,0]/s[0,1]-s[1,0]/s[1,1])
    if not vals:
        return {"repeats":0,"median":None,"ci95":[None,None]}
    q=np.quantile(vals,[.025,.5,.975])
    return {"repeats":len(vals),"median":float(q[1]),"ci95":[float(q[0]),float(q[2])]}


def summarize(panel: pd.DataFrame, repeats=10_000) -> dict:
    cp=build_checkpoints(panel)
    counts,probs=transition_matrix(cp)
    return {
        "checkpoint_rows":len(cp),
        "event_count":int(cp.key.nunique()) if len(cp) else 0,
        "counts":counts.to_dict(),
        "probabilities":probs.to_dict(),
        "continuous":continuous_metrics(cp),
        "unsafe_minus_low_bootstrap":cluster_bootstrap_unsafe_minus_low(cp,repeats=repeats),
    }
