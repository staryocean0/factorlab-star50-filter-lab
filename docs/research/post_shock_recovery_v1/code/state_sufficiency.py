from __future__ import annotations

import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

CHECKPOINTS=(5,10,15,20)
SEED=20260907
SYMBOLS=("000688.SH","000852.SH")
MODELS={
    "ratio_only":["log_ratio"],
    "plus_elapsed":["log_ratio","elapsed10"],
    "plus_recovery_age":["log_ratio","elapsed10","recover_age10"],
}


def roll_mean(x,n):
    s=pd.Series(np.asarray(x,float))
    return s.rolling(n,min_periods=n).mean().to_numpy()


def state_band(x):
    if not np.isfinite(x): return "Unknown"
    if x>=1.5: return "Unsafe"
    if x>=1.0: return "Recovering-high"
    return "Recovering-low"


def build_panel(native: pd.DataFrame, symbol: str) -> pd.DataFrame:
    need={"symbol","timestamp","trading_day","close","causal_flat_fill","high_frequency_analysis_eligible"}
    miss=need-set(native.columns)
    if miss: raise ValueError(f"missing {sorted(miss)}")
    x=native.copy()
    if set(x.symbol)!={symbol}: raise ValueError("symbol mismatch")
    x["ts"]=pd.to_datetime(x.timestamp.astype(str).str[:19])
    close=pd.to_numeric(x.close,errors="coerce")
    good=x.high_frequency_analysis_eligible.eq(True)&x.causal_flat_fill.eq(False)&(close>0)
    x["px"]=close.where(good)
    parts=[]
    for day,z0 in x.groupby("trading_day",sort=True):
        for afternoon,start in [(0,pd.Timestamp(f"{day} 09:30:00")),(1,pd.Timestamp(f"{day} 13:00:00"))]:
            times=pd.date_range(start,periods=120,freq="1min")
            z=z0.set_index("ts").reindex(times)
            px=z.px.to_numpy(float)
            r=np.full(120,np.nan)
            ok=np.isfinite(px[1:])&np.isfinite(px[:-1])
            r[1:][ok]=np.log(px[1:][ok]/px[:-1][ok])*1e4
            rv30=roll_mean(r*r,30)
            sigma=np.sqrt(np.r_[np.nan,rv30[:-1]])
            event=np.full(120,np.nan)
            fr=np.isfinite(r)
            event[fr&(np.abs(r)<=30)]=0
            known=fr&np.isfinite(sigma)
            event[known]=((np.abs(r[known])>30)&(np.abs(r[known])>4*np.maximum(sigma[known],1))).astype(float)
            first=np.full(120,np.nan)
            for j in range(30,120):
                prev=event[j-30:j]
                if np.isfinite(prev).all() and np.isfinite(event[j]):
                    first[j]=float(event[j]==1 and not prev.any())
            parts.append(pd.DataFrame({
                "symbol":symbol,"session":f"{day}/{afternoon}","day":day,"minute":np.arange(1,121),
                "return_bp":r,"sigma_pre":sigma,"event":event,"first":first,
            }))
    return pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()


def build_checkpoints(panel: pd.DataFrame, year:int) -> pd.DataFrame:
    rows=[]
    for (symbol,session),z0 in panel.groupby(["symbol","session"],sort=False):
        z=z0.sort_values("minute").reset_index(drop=True)
        r=z.return_bp.to_numpy(float); first=z["first"].to_numpy(float); mins=z.minute.to_numpy(int)
        for j in np.flatnonzero(first==1):
            if mins[j]<33: continue
            sig=float(z.loc[j,"sigma_pre"])
            if not(np.isfinite(sig) and sig>0): continue
            ratios={}
            for lag in range(5,21):
                a=r[j+lag-4:j+lag+1]
                if len(a)==5 and np.isfinite(a).all():
                    ratios[lag]=float(np.sqrt(np.mean(a*a))/sig)
            key=f"{symbol}|{session}|{mins[j]}"
            for cp in CHECKPOINTS:
                a=r[j+cp-4:j+cp+1]; b=r[j+cp+1:j+cp+6]
                if len(a)!=5 or len(b)!=5 or not np.isfinite(a).all() or not np.isfinite(b).all(): continue
                cur=float(np.sqrt(np.mean(a*a))/sig); nxt=float(np.sqrt(np.mean(b*b))/sig)
                last_unsafe=0
                for lag in range(5,cp+1):
                    if lag in ratios and ratios[lag]>=1.5: last_unsafe=lag
                recover_age=0 if cur>=1.5 else cp-last_unsafe
                rows.append({"key":key,"symbol":symbol,"year":year,"session":session,"day":z.loc[j,"day"],
                    "checkpoint":cp,"current_ratio":cur,"next_ratio":nxt,"next_unsafe":int(nxt>=1.5),
                    "current_state":state_band(cur),"log_ratio":float(np.log(max(cur,1e-8))),"elapsed10":cp/10.0,
                    "recover_age":recover_age,"recover_age10":recover_age/10.0})
    return pd.DataFrame(rows)


def metric(y,p):
    y=np.asarray(y,int); p=np.asarray(p,float)
    out={"n":len(y),"base_rate":float(y.mean()) if len(y) else None}
    if not len(y): return out
    out["log_loss"]=float(log_loss(y,p,labels=[0,1])); out["brier"]=float(brier_score_loss(y,p))
    out["auc"]=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None
    return out


def fit_models(train):
    y=train.next_unsafe.to_numpy(int); packs={}
    for name,cols in MODELS.items():
        m=make_pipeline(StandardScaler(),LogisticRegression(C=1.0,max_iter=2000,class_weight=None,solver="lbfgs",random_state=SEED))
        m.fit(train[cols],y); packs[name]=m
    return packs


def predict_models(packs,df):
    return {name:packs[name].predict_proba(df[cols])[:,1] for name,cols in MODELS.items()}


def cluster_bootstrap_loss_delta(df, preds, challenger, base="ratio_only", repeats=5000):
    eps=1e-15
    q=df[["key","next_unsafe"]].copy()
    y=q.next_unsafe.to_numpy(int)
    def losses(p):
        p=np.clip(np.asarray(p,float),eps,1-eps)
        return -(y*np.log(p)+(1-y)*np.log(1-p))
    q["base"]=losses(preds[base]); q["challenger"]=losses(preds[challenger])
    daily=q.groupby("key")[["base","challenger"]].mean()
    d=(daily.challenger-daily.base).to_numpy(float)
    rng=np.random.default_rng(SEED); vals=[]
    for _ in range(repeats):
        vals.append(float(d[rng.integers(0,len(d),size=len(d))].mean()))
    qs=np.quantile(vals,[.025,.5,.975])
    return {"events":len(d),"median_delta_log_loss":float(qs[1]),"ci95":[float(qs[0]),float(qs[2])],
            "point_delta_log_loss":float(d.mean())}


def summarize(train, eval25, replay26=None):
    packs=fit_models(train)
    result={"fit":{"rows":len(train),"events":int(train.key.nunique()),"positives":int(train.next_unsafe.sum())},"evaluation":{}}
    for label,df in [("2025",eval25),("2026_replay",replay26)]:
        if df is None or len(df)==0: continue
        ps=predict_models(packs,df); sec={"rows":len(df),"events":int(df.key.nunique()),"models":{}}
        for name,p in ps.items(): sec["models"][name]=metric(df.next_unsafe,p)
        if label=="2025":
            sec["bootstrap"]={c:cluster_bootstrap_loss_delta(df,ps,c) for c in ("plus_elapsed","plus_recovery_age")}
        strata=[]
        for st,z in df.groupby("current_state"):
            for half,g in z.groupby(z.checkpoint<=10):
                strata.append({"state":st,"period":"+5/+10" if half else "+15/+20","n":len(g),"next_unsafe":float(g.next_unsafe.mean())})
        sec["state_time_strata"]=strata
        result["evaluation"][label]=sec
    return result,packs


def load_year(root:Path,symbol:str,year:int):
    if year<=2025:
        p=root/f"data/cross_index_risk_gate_v1/1m/{symbol}/{year}.parquet"
    else:
        p=root/f"data/cross_index_risk_gate_2026_v1/1m/{symbol}/2026.parquet"
    return pd.read_parquet(p)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    args=ap.parse_args();root=Path(args.repo_root).resolve();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    frames=[]
    for year in (2024,2025,2026):
        for symbol in SYMBOLS:
            native=load_year(root,symbol,year); panel=build_panel(native,symbol); cp=build_checkpoints(panel,year); frames.append(cp)
    allcp=pd.concat(frames,ignore_index=True)
    train=allcp[allcp.year==2024].copy(); ev25=allcp[allcp.year==2025].copy(); rep26=allcp[allcp.year==2026].copy()
    result,_=summarize(train,ev25,rep26)
    result["guardrails"]=["2024 fit, 2025 fixed evaluation","2026 replay is consumed descriptive consistency only","no state threshold/window changes"]
    allcp.to_csv(out/"checkpoints.csv",index=False)
    (out/"summary.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__": main()
