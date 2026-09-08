from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOL="000852.SH"
SCALE=3
FAMILY="fixed_physical"
POLICIES=("hard_gate","admission_gate")
YEARS=(2021,2022,2023,2024,2025,2026)
OPEN_FEE_BP=0.23
SAME_DAY_CLOSE_FEE_BP=2.30
EXTRA_PER_LEG_BP=(0.0,0.25,0.50)


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def decision_targets(signal:np.ndarray,state:np.ndarray,valid:np.ndarray,policy:str)->np.ndarray:
    signal=np.asarray(signal,float);state=np.asarray(state,object);valid=np.asarray(valid,bool)
    out=np.zeros(len(signal),float)
    if policy=="hard_gate":
        return np.where(valid & (state=="Unsafe"),signal,0.0)
    if policy!="admission_gate": raise ValueError(policy)
    cur=0.0
    for i in range(len(signal)):
        if not valid[i] or not np.isfinite(signal[i]) or signal[i]==0:
            cur=0.0
        elif cur==0:
            cur=float(signal[i]) if state[i]=="Unsafe" else 0.0
        elif signal[i]==cur:
            # Unsafe is an admission gate, not an automatic exit gate.
            pass
        else:
            # Frozen signal flipped. Exit current side; reverse only under Unsafe.
            cur=float(signal[i]) if state[i]=="Unsafe" else 0.0
        out[i]=cur
    return out


def transition_fees(exec_pos:np.ndarray)->dict:
    ep=np.asarray(exec_pos,float)
    opens=closes=reversals=0
    prev=0.0
    for cur in np.r_[ep,0.0]:
        if cur==prev: continue
        if prev==0 and cur!=0:
            opens+=1
        elif prev!=0 and cur==0:
            closes+=1
        elif prev!=0 and cur!=0 and np.sign(prev)!=np.sign(cur):
            closes+=1;opens+=1;reversals+=1
        else:
            raise RuntimeError((prev,cur))
        prev=cur
    legs=opens+closes
    exchange=opens*OPEN_FEE_BP+closes*SAME_DAY_CLOSE_FEE_BP
    turnover=float(np.sum(np.abs(np.diff(np.r_[0.0,ep,0.0]))))
    if abs(turnover-legs)>1e-12:
        raise RuntimeError((turnover,legs))
    return {"open_legs":opens,"close_legs":closes,"reversal_execs":reversals,
            "execution_legs":legs,"one_way_turnover":turnover,"exchange_fee_bp":float(exchange)}


def simulate_valid_run(open_px:np.ndarray,signal:np.ndarray,state:np.ndarray,policy:str)->dict:
    op=np.asarray(open_px,float);sig=np.asarray(signal,float);st=np.asarray(state,object)
    n=len(op)
    valid=np.isfinite(op)&(op>0)&np.isfinite(sig)
    target=decision_targets(sig,st,valid,policy)
    ep=np.zeros(n,float)
    if n>2: ep[2:]=target[:-2]
    fwd=np.zeros(n,float)
    if n>1: fwd[1:]=np.log(op[1:]/op[:-1])*1e4
    pnl=ep*fwd
    fee=transition_fees(ep)
    active=ep!=0
    gross=float(np.sum(pnl))
    out={"gross_bp":gross,"exposure_bars":int(active.sum()),"booked_returns":int(active.sum()),
         "winning_returns":int((pnl[active]>0).sum()),**fee}
    out["exposure_minutes"]=out["exposure_bars"]*SCALE
    out["gross_bp_per_exposure_min"]=gross/out["exposure_minutes"] if out["exposure_minutes"] else np.nan
    out["symmetric_break_even_one_way_cost_bp"]=gross/out["one_way_turnover"] if out["one_way_turnover"] else np.nan
    out["net_exchange_bp"]=gross-out["exchange_fee_bp"]
    out["net_exchange_bp_per_exposure_min"]=out["net_exchange_bp"]/out["exposure_minutes"] if out["exposure_minutes"] else np.nan
    out["break_even_extra_per_leg_bp"]=out["net_exchange_bp"]/out["execution_legs"] if out["execution_legs"] else np.nan
    for c in EXTRA_PER_LEG_BP:
        out[f"net_extra_{c:g}_bp"]=out["net_exchange_bp"]-c*out["execution_legs"]
        out[f"net_extra_{c:g}_bp_per_exposure_min"]=out[f"net_extra_{c:g}_bp"]/out["exposure_minutes"] if out["exposure_minutes"] else np.nan
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


def session_policy_rows(bars:pd.DataFrame,signal:np.ndarray)->pd.DataFrame:
    rows=[]
    opens=bars.open.to_numpy(float);valid_all=bars.valid.to_numpy(bool);states=bars.route_state.to_numpy(object)
    signal=np.asarray(signal,float)
    for session,idx in bars.groupby("session",sort=False).indices.items():
        ix=np.asarray(idx,int);year=int(bars.year.iloc[ix[0]])
        if year not in YEARS: continue
        op=opens[ix];sig=signal[ix];st=states[ix]
        valid=np.isfinite(op)&(op>0)&valid_all[ix]
        for policy in POLICIES:
            total={"gross_bp":0.0,"exposure_bars":0,"booked_returns":0,"winning_returns":0,
                   "open_legs":0,"close_legs":0,"reversal_execs":0,"execution_legs":0,
                   "one_way_turnover":0.0,"exchange_fee_bp":0.0}
            for a,b in contiguous_runs(valid):
                q=simulate_valid_run(op[a:b],sig[a:b],st[a:b],policy)
                for k in total: total[k]+=q[k]
            total["exposure_minutes"]=total["exposure_bars"]*SCALE
            total["gross_bp_per_exposure_min"]=total["gross_bp"]/total["exposure_minutes"] if total["exposure_minutes"] else np.nan
            total["symmetric_break_even_one_way_cost_bp"]=total["gross_bp"]/total["one_way_turnover"] if total["one_way_turnover"] else np.nan
            total["net_exchange_bp"]=total["gross_bp"]-total["exchange_fee_bp"]
            total["net_exchange_bp_per_exposure_min"]=total["net_exchange_bp"]/total["exposure_minutes"] if total["exposure_minutes"] else np.nan
            total["break_even_extra_per_leg_bp"]=total["net_exchange_bp"]/total["execution_legs"] if total["execution_legs"] else np.nan
            for c in EXTRA_PER_LEG_BP:
                total[f"net_extra_{c:g}_bp"]=total["net_exchange_bp"]-c*total["execution_legs"]
                total[f"net_extra_{c:g}_bp_per_exposure_min"]=total[f"net_extra_{c:g}_bp"]/total["exposure_minutes"] if total["exposure_minutes"] else np.nan
            rows.append({"session":session,"year":year,"policy":policy,**total})
    return pd.DataFrame(rows)


def aggregate(rows:pd.DataFrame,group_cols:list[str])->pd.DataFrame:
    sums=["gross_bp","exposure_bars","exposure_minutes","booked_returns","winning_returns","open_legs","close_legs",
          "reversal_execs","execution_legs","one_way_turnover","exchange_fee_bp"]
    out=rows.groupby(group_cols,dropna=False)[sums].sum().reset_index()
    out["sessions_with_exposure"]=rows.assign(active=rows.exposure_bars>0).groupby(group_cols).active.sum().to_numpy()
    out["gross_bp_per_exposure_min"]=out.gross_bp/out.exposure_minutes.replace(0,np.nan)
    out["hit_rate"]=out.winning_returns/out.booked_returns.replace(0,np.nan)
    out["symmetric_break_even_one_way_cost_bp"]=out.gross_bp/out.one_way_turnover.replace(0,np.nan)
    out["net_exchange_bp"]=out.gross_bp-out.exchange_fee_bp
    out["net_exchange_bp_per_exposure_min"]=out.net_exchange_bp/out.exposure_minutes.replace(0,np.nan)
    out["break_even_extra_per_leg_bp"]=out.net_exchange_bp/out.execution_legs.replace(0,np.nan)
    for c in EXTRA_PER_LEG_BP:
        out[f"net_extra_{c:g}_bp"]=out.net_exchange_bp-c*out.execution_legs
        out[f"net_extra_{c:g}_bp_per_exposure_min"]=out[f"net_extra_{c:g}_bp"]/out.exposure_minutes.replace(0,np.nan)
    return out


def check_phase2_anchor(annual:pd.DataFrame,anchor_path:Path)->dict:
    anchor=json.loads(anchor_path.read_text())
    h=annual[annual.policy=="hard_gate"].set_index("year")
    fields=("gross_bp","one_way_turnover","exposure_bars","exposure_minutes","booked_returns","winning_returns")
    max_abs=0.0
    rows=[]
    for r in anchor["annual"]:
        year=int(r["year"]);q=h.loc[year]
        diffs={}
        for f in fields:
            d=float(q[f])-float(r[f]);diffs[f]=d;max_abs=max(max_abs,abs(d))
            if not np.isclose(float(q[f]),float(r[f]),atol=1e-9,rtol=0):
                raise RuntimeError(f"Phase2 hard-gate anchor mismatch {year} {f}: {q[f]} != {r[f]}")
        rows.append({"year":year,**diffs})
    return {"passed":True,"max_abs_difference":max_abs,"rows":rows,
            "source_phase2_run":anchor["source_phase2_run"],"source_phase2_artifact_sha256":anchor["source_phase2_artifact_sha256"]}


def run(root:Path,out:Path)->dict:
    phase2=load(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2")
    fg=load(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","fast_grid")
    state_mod=phase2.load_module(root/"docs/research/post_shock_recovery_v1/code/state_sufficiency.py","state_builder")
    filters=phase2.load_module(root/"src/star50_filter/filters.py","filters")
    native=phase2.load_native(root,SYMBOL)
    states=phase2.route_states(state_mod,native,SYMBOL)
    minute=fg.build_minute_grid(native,states,SYMBOL)
    bars=fg.aggregate_scale(minute,SCALE).reset_index(drop=True)
    signal,low,sigma=phase2.base_signal(filters,bars,FAMILY,SCALE)
    sessions=session_policy_rows(bars,signal)
    annual=aggregate(sessions,["year","policy"])
    pooled=aggregate(sessions[sessions.year<=2025],["policy"])
    replay=aggregate(sessions[sessions.year==2026],["policy"])
    anchor=check_phase2_anchor(annual,root/"docs/research/csi1000_unsafe_admission_fee_v1/phase2_hard_gate_anchor.json")
    out.mkdir(parents=True,exist_ok=True)
    sessions.to_csv(out/"session_results.csv",index=False)
    annual.to_csv(out/"annual_results.csv",index=False)
    pooled.to_csv(out/"pooled_2021_2025.csv",index=False)
    replay.to_csv(out/"replay_2026.csv",index=False)
    (out/"phase2_anchor_check.json").write_text(json.dumps(anchor,indent=2)+"\n")
    summary={"schema":"csi1000_unsafe_admission_fee_v1","symbol":SYMBOL,"scale_min":SCALE,"family":FAMILY,
             "policies":list(POLICIES),"open_fee_bp":OPEN_FEE_BP,"same_day_close_fee_bp":SAME_DAY_CLOSE_FEE_BP,
             "extra_per_execution_leg_bp":list(EXTRA_PER_LEG_BP),"phase2_anchor_passed":True,
             "guardrails":["post-selection exploratory follow-up","2021-2025 consumed history","2026 already-opened replay",
                           "current CFFEX fee table used uniformly as stress model, not historical fee reconstruction",
                           "index-open return abstraction, no futures basis/spread/slippage"]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary))
    return summary


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=="__main__": main()
