from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
PERIODS={"2021_2025":(2021,2022,2023,2024,2025),"2026":(2026,)}
POLICIES=("unsafe_hard_off","unsafe_entry_block")
SCENARIOS=((1.0,1.0),(.8,.8),(.8,.9),(.9,.8),(.9,.9))
DRAWS=1000
SEED=20260908
COST_ONE_WAY_BP=1.0


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def contiguous_runs(mask:np.ndarray,session:np.ndarray):
    mask=np.asarray(mask,bool);session=np.asarray(session,object);n=len(mask);i=0
    while i<n:
        while i<n and not mask[i]: i+=1
        if i>=n: break
        j=i+1
        while j<n and mask[j] and session[j]==session[i]: j+=1
        yield i,j
        i=j


def build_eval_arrays(bars:pd.DataFrame,signal:np.ndarray)->dict:
    x=bars.reset_index(drop=True).copy();sig=np.asarray(signal,float)
    if len(x)!=len(sig): raise ValueError("signal length")
    op=x.open.to_numpy(float);valid=x.valid.to_numpy(bool)&np.isfinite(op)&(op>0)
    session=x.session.astype(str).to_numpy(object);state=x.route_state.to_numpy(object)
    unknown=valid&(state=="Unknown")
    true_unsafe=valid&(state=="Unsafe")
    base_target=np.where(valid & np.isfinite(sig) & (sig!=0),sig,0.0)
    n=len(x);src=np.full(n,-1,int);fwd=np.zeros(n,float);seg_starts=[];seg_ends=[];continuity=np.zeros(max(n-1,0),bool)
    for a,b in contiguous_runs(valid,session):
        seg_starts.append(a);seg_ends.append(b)
        if b-a>2: src[a+2:b]=np.arange(a,b-2)
        if b-a>1:
            fwd[a+1:b]=np.log(op[a+1:b]/op[a:b-1])*1e4
            continuity[a:b-1]=True
    return {"bars":x,"signal":sig,"valid":valid,"session":session,"state":state,"unknown":unknown,
            "true_unsafe":true_unsafe,"base_target":base_target,"src":src,"fwd":fwd,
            "seg_starts":np.asarray(seg_starts,int),"seg_ends":np.asarray(seg_ends,int),"continuity":continuity}


def mask_runs(mask:np.ndarray,arr:dict)->list[dict]:
    x=arr["bars"];runs=[]
    for a,b in contiguous_runs(mask,arr["session"]):
        row=x.iloc[a]
        runs.append({"a":a,"b":b,"idx":np.arange(a,b),"year":int(row.year),
                     "half":str(row.session).rsplit("/",1)[-1],"start_bar":int(row.bar_in_session),"length":b-a})
    return runs


def false_candidate_map(arr:dict,true_runs:list[dict])->dict:
    x=arr["bars"];valid=arr["valid"];state=arr["state"]
    groups={s:np.asarray(idx,int) for s,idx in x.groupby("session",sort=False).indices.items()}
    signatures=sorted({(r["year"],r["half"],r["start_bar"],r["length"]) for r in true_runs})
    out={}
    for sig in signatures:
        year,half,start,length=sig;cands=[]
        for session,idx in groups.items():
            if int(x.year.iloc[idx[0]])!=year or str(session).rsplit("/",1)[-1]!=half: continue
            loc=x.bar_in_session.to_numpy(int)[idx]
            chosen=idx[(loc>=start)&(loc<start+length)]
            if len(chosen)!=length: continue
            if not np.array_equal(x.bar_in_session.to_numpy(int)[chosen],np.arange(start,start+length)): continue
            if not valid[chosen].all(): continue
            st=state[chosen]
            if np.isin(st,["Unsafe","Unknown"]).any(): continue
            cands.append(chosen.copy())
        out[sig]=cands
    return out


def entry_block_target(arr:dict,pred_unsafe:np.ndarray)->np.ndarray:
    target=arr["base_target"].copy();target[arr["unknown"]]=0.0
    effective=np.asarray(pred_unsafe,bool)&arr["valid"]&~arr["unknown"]
    for a,b in contiguous_runs(effective,arr["session"]):
        # If previous decision cannot carry an admitted target into the predicted
        # Unsafe run, the run cannot initiate risk.
        pre=0.0
        if a>0 and arr["session"][a-1]==arr["session"][a] and arr["valid"][a-1] and not arr["unknown"][a-1]:
            pre=float(target[a-1])
        if pre==0 or not np.isfinite(pre):
            target[a:b]=0.0;continue
        s=arr["base_target"][a:b]
        diff=np.flatnonzero(s!=pre)
        if len(diff):
            k=a+int(diff[0]);target[a:k]=pre;target[k:b]=0.0
        else:
            target[a:b]=pre
    return target


def target_for_policy(arr:dict,pred_unsafe:np.ndarray,policy:str)->np.ndarray:
    if policy=="unsafe_hard_off":
        t=arr["base_target"].copy();t[np.asarray(pred_unsafe,bool)|arr["unknown"]]=0.0;return t
    if policy=="unsafe_entry_block": return entry_block_target(arr,pred_unsafe)
    raise ValueError(policy)


def evaluate_target(arr:dict,target:np.ndarray)->dict:
    src=arr["src"];ep=np.zeros(len(target),float);m=src>=0;ep[m]=target[src[m]]
    pnl=ep*arr["fwd"];active=ep!=0
    turn=float(np.abs(ep[arr["seg_starts"]]).sum()+np.abs(ep[arr["seg_ends"]-1]).sum())
    if len(ep)>1: turn+=float(np.abs(np.diff(ep))[arr["continuity"]].sum())
    return {"gross_bp":float(pnl.sum()),"one_way_turnover":turn,"exposure_bars":int(active.sum()),
            "exposure_minutes":int(active.sum()*5),"booked_returns":int(active.sum()),
            "winning_returns":int((pnl[active]>0).sum()),"net1_bp":float(pnl.sum()-COST_ONE_WAY_BP*turn)}


def phase4_equivalent_state(arr:dict,pred_unsafe:np.ndarray)->np.ndarray:
    st=np.full(len(pred_unsafe),"Recovering",object);st[np.asarray(pred_unsafe,bool)]="Unsafe";st[arr["unknown"]]="Unknown";return st


def make_warning_mask(arr:dict,true_runs:list[dict],candidates:dict,recall:float,precision:float,rng)->tuple[np.ndarray,dict]:
    if recall==1.0 and precision==1.0:
        mask=arr["true_unsafe"].copy()
        return mask,{"true_runs":len(true_runs),"retained_true_runs":len(true_runs),"false_runs":0,
                     "realized_run_recall":1.0 if true_runs else np.nan,"realized_run_precision":1.0 if true_runs else np.nan,
                     "predicted_unsafe_bars":int(mask.sum()),"dropped_false_attempts":0}
    mask=np.zeros(len(arr["valid"]),bool);tp=fp=dropped=0
    fp_prob=(1.0-precision)/precision
    for r in true_runs:
        if rng.random()>=recall: continue
        mask[r["idx"]]=True;tp+=1
        if rng.random()<fp_prob:
            sig=(r["year"],r["half"],r["start_bar"],r["length"]);pool=candidates.get(sig,[])
            if pool:
                chosen=pool[int(rng.integers(0,len(pool)))];mask[chosen]=True;fp+=1
            else:
                dropped+=1
    return mask,{"true_runs":len(true_runs),"retained_true_runs":tp,"false_runs":fp,
                 "realized_run_recall":tp/len(true_runs) if true_runs else np.nan,
                 "realized_run_precision":tp/(tp+fp) if tp+fp else np.nan,
                 "predicted_unsafe_bars":int(mask.sum()),"dropped_false_attempts":dropped}


def check_anchor(symbol:str,period:str,metrics:dict,anchor:dict):
    expected=anchor["symbols"][symbol][period]
    fields=("gross_bp","one_way_turnover","exposure_bars","exposure_minutes","booked_returns","winning_returns")
    max_abs=0.0
    for policy,q in metrics.items():
        for f in fields:
            d=float(q[f])-float(expected[policy][f]);max_abs=max(max_abs,abs(d))
            if not np.isclose(float(q[f]),float(expected[policy][f]),atol=1e-9,rtol=0):
                raise RuntimeError(f"Phase4 anchor mismatch {symbol} {period} {policy} {f}: {q[f]} != {expected[policy][f]}")
    return max_abs


def summarize_draws(draws:pd.DataFrame,perfect:dict)->pd.DataFrame:
    rows=[]
    keys=["symbol","period","policy","recall_target","precision_target"]
    for key,z in draws.groupby(keys,sort=False):
        symbol,period,policy,rec,prec=key
        def stats(col):
            a=z[col].to_numpy(float);q=np.nanquantile(a,[.025,.5,.975]);return float(q[0]),float(q[1]),float(q[2])
        g=stats("delta_gross_bp");n=stats("delta_net1_bp");t=stats("delta_turnover")
        rr=stats("realized_run_recall");rp=stats("realized_run_precision");pb=stats("predicted_unsafe_bars")
        perf=perfect.get((symbol,period,policy),np.nan)
        retained=np.nan
        if np.isfinite(perf) and perf>0:
            retained=float(np.nanmedian(z.delta_gross_bp.to_numpy(float)/perf))
        rows.append({"symbol":symbol,"period":period,"policy":policy,"recall_target":rec,"precision_target":prec,
                     "draws":len(z),"delta_gross_q025":g[0],"delta_gross_median":g[1],"delta_gross_q975":g[2],
                     "positive_gross_fraction":float((z.delta_gross_bp>0).mean()),
                     "delta_net1_q025":n[0],"delta_net1_median":n[1],"delta_net1_q975":n[2],
                     "positive_net1_fraction":float((z.delta_net1_bp>0).mean()),
                     "delta_turnover_median":t[1],"run_recall_median":rr[1],"run_precision_median":rp[1],
                     "predicted_unsafe_bars_median":pb[1],"median_fraction_perfect_gross_retained":retained})
    return pd.DataFrame(rows)


def run(root:Path,out:Path)->dict:
    phase2=load(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_fidelity")
    fg=load(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","fast_grid_fidelity")
    state_mod=phase2.load_module(root/"docs/research/post_shock_recovery_v1/code/state_sufficiency.py","state_builder_fidelity")
    filters=phase2.load_module(root/"src/star50_filter/filters.py","filters_fidelity")
    anchor=json.loads((root/"docs/research/unsafe_warning_fidelity_v1/phase4_policy_anchor.json").read_text())
    draw_rows=[];anchor_rows=[];run_receipts=[];perfect_delta={}
    for si,symbol in enumerate(SYMBOLS):
        native=phase2.load_native(root,symbol);states=phase2.route_states(state_mod,native,symbol)
        minute=fg.build_minute_grid(native,states,symbol);bars_all=fg.aggregate_scale(minute,5).reset_index(drop=True)
        signal_all,_,_=phase2.base_signal(filters,bars_all,"fixed_physical",5)
        for pi,(period,years) in enumerate(PERIODS.items()):
            keep=bars_all.year.isin(years).to_numpy(bool);bars=bars_all.loc[keep].reset_index(drop=True);signal=signal_all[keep]
            arr=build_eval_arrays(bars,signal);true_runs=mask_runs(arr["true_unsafe"],arr);candidates=false_candidate_map(arr,true_runs)
            base=evaluate_target(arr,arr["base_target"])
            perfect_metrics={"baseline_ungated":base}
            for policy in POLICIES:
                target=target_for_policy(arr,arr["true_unsafe"],policy);perfect_metrics[policy]=evaluate_target(arr,target)
            max_abs=check_anchor(symbol,period,perfect_metrics,anchor)
            anchor_rows.append({"symbol":symbol,"period":period,"max_abs_difference":max_abs,"passed":True})
            run_receipts.append({"symbol":symbol,"period":period,"true_unsafe_runs":len(true_runs),
                                 "true_unsafe_bars":int(arr["true_unsafe"].sum()),
                                 "false_candidate_signatures":int(sum(bool(v) for v in candidates.values())),
                                 "run_signatures":len(candidates)})
            for policy in POLICIES:
                pdlt=perfect_metrics[policy]["gross_bp"]-base["gross_bp"]
                perfect_delta[(symbol,period,policy)]=pdlt
            for sci,(recall,precision) in enumerate(SCENARIOS):
                n_draw=1 if (recall,precision)==(1.0,1.0) else DRAWS
                rng=np.random.default_rng(SEED+si*100000+pi*10000+sci*1000)
                for d in range(n_draw):
                    pred,wr=make_warning_mask(arr,true_runs,candidates,recall,precision,rng)
                    # Perfect-state target equivalence is additionally guarded by the Phase4 anchor above.
                    for policy in POLICIES:
                        q=evaluate_target(arr,target_for_policy(arr,pred,policy))
                        draw_rows.append({"symbol":symbol,"period":period,"policy":policy,"recall_target":recall,
                            "precision_target":precision,"draw":d,"gross_bp":q["gross_bp"],"one_way_turnover":q["one_way_turnover"],
                            "delta_gross_bp":q["gross_bp"]-base["gross_bp"],"delta_turnover":q["one_way_turnover"]-base["one_way_turnover"],
                            "net1_bp":q["net1_bp"],"delta_net1_bp":q["net1_bp"]-base["net1_bp"],**wr})
    draws=pd.DataFrame(draw_rows);summary=summarize_draws(draws,perfect_delta)
    out.mkdir(parents=True,exist_ok=True)
    draws.to_csv(out/"draws.csv.gz",index=False,compression="gzip");summary.to_csv(out/"scenario_summary.csv",index=False)
    pd.DataFrame(anchor_rows).to_csv(out/"phase4_anchor_check.csv",index=False)
    pd.DataFrame(run_receipts).to_csv(out/"run_receipts.csv",index=False)
    result={"schema":"unsafe_warning_fidelity_v1","scenarios":[list(x) for x in SCENARIOS],"draws_per_imperfect_scenario":DRAWS,
            "seed":SEED,"cost_one_way_bp":COST_ONE_WAY_BP,"phase4_anchor_passed":True,
            "guardrails":["hypothetical contemporaneous state-fidelity stress, not a predictor","run-level recall/precision",
                          "matched false runs preserve year/half/start clock/length","2021-2025 consumed history",
                          "2026 already-opened replay","post-2026-08-21 data untouched"]}
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result));return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=="__main__": main()
