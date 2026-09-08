from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
SCALE=5
FAMILY="fixed_physical"
POLICIES=("baseline_ungated","unsafe_hard_off","unsafe_entry_block")
ADMITTED=("NoEpisode","Recovering")
COSTS=(0.5,1.0,2.0)
YEARS=(2021,2022,2023,2024,2025,2026)
SEED=20260908
BOOT_DRAWS=10000


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def decision_targets(signal:np.ndarray,state:np.ndarray,valid:np.ndarray,policy:str)->np.ndarray:
    signal=np.asarray(signal,float);state=np.asarray(state,object);valid=np.asarray(valid,bool)
    good=valid & np.isfinite(signal) & (signal!=0)
    if policy=="baseline_ungated":
        return np.where(good,signal,0.0)
    if policy=="unsafe_hard_off":
        return np.where(good & np.isin(state,ADMITTED),signal,0.0)
    if policy!="unsafe_entry_block": raise ValueError(policy)
    out=np.zeros(len(signal),float);cur=0.0
    for i in range(len(signal)):
        if not good[i] or state[i]=="Unknown":
            cur=0.0
        elif cur==0:
            cur=float(signal[i]) if state[i] in ADMITTED else 0.0
        elif signal[i]==cur:
            # Unsafe blocks new risk but does not itself force same-direction exit.
            pass
        else:
            # Signal flip: reverse only in admitted state; otherwise close to flat.
            cur=float(signal[i]) if state[i] in ADMITTED else 0.0
        out[i]=cur
    return out


def contiguous_runs(mask:np.ndarray):
    mask=np.asarray(mask,bool);i=0;n=len(mask)
    while i<n:
        while i<n and not mask[i]: i+=1
        if i>=n: break
        j=i+1
        while j<n and mask[j]: j+=1
        yield i,j
        i=j


def simulate_valid_run(open_px:np.ndarray,target:np.ndarray)->dict:
    op=np.asarray(open_px,float);target=np.asarray(target,float);n=len(op)
    ep=np.zeros(n,float)
    if n>2: ep[2:]=target[:-2]
    fwd=np.zeros(n,float)
    if n>1: fwd[1:]=np.log(op[1:]/op[:-1])*1e4
    pnl=ep*fwd
    active=ep!=0
    turnover=float(np.sum(np.abs(np.diff(np.r_[0.0,ep,0.0]))))
    return {"gross_bp":float(np.sum(pnl)),"one_way_turnover":turnover,
            "exposure_bars":int(active.sum()),"booked_returns":int(active.sum()),
            "winning_returns":int((pnl[active]>0).sum())}


def session_rows(bars:pd.DataFrame,signal:np.ndarray,symbol:str)->pd.DataFrame:
    rows=[]
    opens=bars.open.to_numpy(float);valid_all=bars.valid.to_numpy(bool)
    states=bars.route_state.to_numpy(object);signal=np.asarray(signal,float)
    days=bars.trading_day.astype(str).to_numpy()
    for session,idx in bars.groupby("session",sort=False).indices.items():
        ix=np.asarray(idx,int);year=int(bars.year.iloc[ix[0]])
        if year not in YEARS: continue
        op=opens[ix];sig=signal[ix];st=states[ix];valid=valid_all[ix]&np.isfinite(op)&(op>0)
        unsafe_bars=int(np.sum(valid & (st=="Unsafe")))
        for policy in POLICIES:
            total={"gross_bp":0.0,"one_way_turnover":0.0,"exposure_bars":0,
                   "booked_returns":0,"winning_returns":0}
            for a,b in contiguous_runs(valid):
                target=decision_targets(sig[a:b],st[a:b],np.ones(b-a,bool),policy)
                q=simulate_valid_run(op[a:b],target)
                for k in total: total[k]+=q[k]
            total["exposure_minutes"]=total["exposure_bars"]*SCALE
            total["gross_bp_per_exposure_min"]=total["gross_bp"]/total["exposure_minutes"] if total["exposure_minutes"] else np.nan
            total["break_even_one_way_cost_bp"]=total["gross_bp"]/total["one_way_turnover"] if total["one_way_turnover"] else np.nan
            total["hit_rate"]=total["winning_returns"]/total["booked_returns"] if total["booked_returns"] else np.nan
            for c in COSTS:
                total[f"net_cost_{c:g}_bp"]=total["gross_bp"]-c*total["one_way_turnover"]
            rows.append({"symbol":symbol,"trading_day":str(days[ix[0]])[:10],"session":session,"year":year,
                         "unsafe_decision_bars":unsafe_bars,"affected":unsafe_bars>0,"policy":policy,**total})
    return pd.DataFrame(rows)


def aggregate(rows:pd.DataFrame,group_cols:list[str])->pd.DataFrame:
    sums=["gross_bp","one_way_turnover","exposure_bars","exposure_minutes","booked_returns","winning_returns"]
    out=rows.groupby(group_cols,dropna=False)[sums].sum().reset_index()
    sess=rows.assign(active=rows.exposure_bars>0).groupby(group_cols).active.sum().rename("sessions_with_exposure").reset_index()
    out=out.merge(sess,on=group_cols,how="left")
    out["gross_bp_per_exposure_min"]=out.gross_bp/out.exposure_minutes.replace(0,np.nan)
    out["break_even_one_way_cost_bp"]=out.gross_bp/out.one_way_turnover.replace(0,np.nan)
    out["hit_rate"]=out.winning_returns/out.booked_returns.replace(0,np.nan)
    for c in COSTS:
        out[f"net_cost_{c:g}_bp"]=out.gross_bp-c*out.one_way_turnover
        out[f"net_cost_{c:g}_bp_per_exposure_min"]=out[f"net_cost_{c:g}_bp"]/out.exposure_minutes.replace(0,np.nan)
    return out


def check_anchor(annual:pd.DataFrame,anchor_path:Path)->dict:
    anchor=json.loads(anchor_path.read_text())
    base=annual[annual.policy=="baseline_ungated"].set_index(["symbol","year"])
    fields=("gross_bp","one_way_turnover","exposure_bars","exposure_minutes","booked_returns","winning_returns")
    max_abs=0.0;checks=[]
    for symbol,items in anchor["symbols"].items():
        for r in items:
            year=int(r["year"]);q=base.loc[(symbol,year)];diffs={}
            for f in fields:
                d=float(q[f])-float(r[f]);diffs[f]=d;max_abs=max(max_abs,abs(d))
                if not np.isclose(float(q[f]),float(r[f]),atol=1e-9,rtol=0):
                    raise RuntimeError(f"Phase2 5m anchor mismatch {symbol} {year} {f}: {q[f]} != {r[f]}")
            checks.append({"symbol":symbol,"year":year,**diffs})
    return {"passed":True,"max_abs_difference":max_abs,"checks":checks,
            "source_phase2_run":anchor["source_phase2_run"],
            "source_phase2_artifact_sha256":anchor["source_phase2_artifact_sha256"]}


def bootstrap_day_delta(affected:pd.DataFrame,policy:str,metric:str)->dict:
    z=affected[affected.policy.isin(["baseline_ungated",policy])].copy()
    piv=z.pivot_table(index=["trading_day","session"],columns="policy",values=metric,aggfunc="sum")
    piv=piv.dropna(subset=["baseline_ungated",policy])
    piv["delta"]=piv[policy]-piv["baseline_ungated"]
    day=piv.reset_index().groupby("trading_day").delta.sum()
    if len(day)==0: return {"days":0,"point_mean":None,"ci95":[None,None]}
    arr=day.to_numpy(float);rng=np.random.default_rng(SEED + (0 if policy=="unsafe_hard_off" else 1000) + (0 if metric=="gross_bp" else 100))
    ids=rng.integers(0,len(arr),size=(BOOT_DRAWS,len(arr)))
    means=arr[ids].mean(axis=1);lo,med,hi=np.quantile(means,[.025,.5,.975])
    return {"days":int(len(arr)),"point_mean":float(arr.mean()),"bootstrap_median":float(med),
            "ci95":[float(lo),float(hi)],"draws":BOOT_DRAWS}


def affected_delta_summary(rows:pd.DataFrame,year_filter)->tuple[pd.DataFrame,dict]:
    x=rows[rows.year.isin(year_filter) & rows.affected].copy()
    records=[];boots={}
    for symbol in SYMBOLS:
        s=x[x.symbol==symbol]
        for policy in ("unsafe_hard_off","unsafe_entry_block"):
            z=s[s.policy.isin(["baseline_ungated",policy])]
            piv=z.pivot_table(index=["trading_day","session"],columns="policy",
                              values=["gross_bp","one_way_turnover"]+[f"net_cost_{c:g}_bp" for c in COSTS],aggfunc="sum")
            if piv.empty: continue
            p=z[z.policy==policy]
            rec={"symbol":symbol,"policy":policy,"affected_sessions":int(p.session.nunique()),
                 "policy_gross_bp":float(p.gross_bp.sum()),"policy_turnover":float(p.one_way_turnover.sum()),
                 "policy_worst_session_gross_bp":float(p.gross_bp.min()),
                 "policy_q05_session_gross_bp":float(p.gross_bp.quantile(.05))}
            for metric in ["gross_bp","one_way_turnover"]+[f"net_cost_{c:g}_bp" for c in COSTS]:
                if (metric,"baseline_ungated") in piv and (metric,policy) in piv:
                    d=piv[(metric,policy)]-piv[(metric,"baseline_ungated")]
                    rec[f"delta_{metric}_total"]=float(d.sum());rec[f"delta_{metric}_mean_session"]=float(d.mean())
            records.append(rec)
            boots[f"{symbol}|{policy}|gross"] = bootstrap_day_delta(s,policy,"gross_bp")
            # Construct 1bp net explicitly for bootstrap.
            ss=s.copy();ss["net1"]=ss.gross_bp-ss.one_way_turnover
            boots[f"{symbol}|{policy}|net1"] = bootstrap_day_delta(ss,policy,"net1")
    return pd.DataFrame(records),boots


def run(root:Path,out:Path)->dict:
    phase2=load(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_5m")
    fg=load(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","fast_grid_5m")
    state_mod=phase2.load_module(root/"docs/research/post_shock_recovery_v1/code/state_sufficiency.py","state_builder_5m")
    filters=phase2.load_module(root/"src/star50_filter/filters.py","filters_5m")
    all_rows=[]
    for symbol in SYMBOLS:
        native=phase2.load_native(root,symbol);states=phase2.route_states(state_mod,native,symbol)
        minute=fg.build_minute_grid(native,states,symbol);bars=fg.aggregate_scale(minute,SCALE).reset_index(drop=True)
        signal,_,_=phase2.base_signal(filters,bars,FAMILY,SCALE)
        all_rows.append(session_rows(bars,signal,symbol))
    sessions=pd.concat(all_rows,ignore_index=True)
    annual=aggregate(sessions,["symbol","year","policy"])
    pooled=aggregate(sessions[sessions.year<=2025],["symbol","policy"])
    replay=aggregate(sessions[sessions.year==2026],["symbol","policy"])
    anchor=check_anchor(annual,root/"docs/research/unsafe_risk_admission_5m_v1/phase2_5m_ungated_anchor.json")
    delta_pool,boot_pool=affected_delta_summary(sessions,(2021,2022,2023,2024,2025))
    delta_26,boot_26=affected_delta_summary(sessions,(2026,))
    out.mkdir(parents=True,exist_ok=True)
    sessions.to_csv(out/"session_results.csv",index=False);annual.to_csv(out/"annual_results.csv",index=False)
    pooled.to_csv(out/"pooled_2021_2025.csv",index=False);replay.to_csv(out/"replay_2026.csv",index=False)
    delta_pool.to_csv(out/"affected_delta_2021_2025.csv",index=False);delta_26.to_csv(out/"affected_delta_2026.csv",index=False)
    (out/"bootstrap_2021_2025.json").write_text(json.dumps(boot_pool,indent=2)+"\n")
    (out/"bootstrap_2026.json").write_text(json.dumps(boot_26,indent=2)+"\n")
    (out/"phase2_anchor_check.json").write_text(json.dumps(anchor,indent=2)+"\n")
    result={"schema":"unsafe_risk_admission_5m_v1","scale_min":SCALE,"family":FAMILY,
            "symbols":list(SYMBOLS),"policies":list(POLICIES),"costs_one_way_bp":list(COSTS),
            "phase2_anchor_passed":True,"bootstrap_draws":BOOT_DRAWS,"seed":SEED,
            "guardrails":["2021-2025 consumed exploratory history","2026 already-opened consistency replay only",
                          "no frequency/filter/threshold search","Clean disabled","Unknown never admitted",
                          "index-return abstraction, not carrier fill simulation"]}
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result));return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=="__main__": main()
