from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

END="2026-08-21"


def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def eff(x:np.ndarray)->float:
    tv=float(np.sum(np.abs(x))); net=float(np.sum(x))
    return abs(net)/tv if tv>0 else np.nan


def build_rows(minute:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for session,z0 in minute.groupby("session",sort=False):
        z=z0.sort_values("minute").reset_index(drop=True)
        st=z.route_state.to_numpy(object); c=z.close.to_numpy(float); op=z.open.to_numpy(float); valid=z.valid.to_numpy(bool)
        ratio=pd.to_numeric(z.recovery_ratio,errors="coerce").to_numpy(float)
        r=np.full(len(z),np.nan,float)
        for i in range(1,len(z)):
            if valid[i] and valid[i-1] and np.isfinite(c[i]) and np.isfinite(c[i-1]) and c[i]>0 and c[i-1]>0:
                r[i]=np.log(c[i]/c[i-1])*1e4
        for i in range(35,len(z)):
            if st[i]!="HighVol" or st[i-1]!="NormalVol": continue
            recent=r[i-4:i+1]
            bg30=r[i-34:i-4]
            prior10=r[i-14:i-4]
            prior15=r[i-19:i-4]
            if not np.isfinite(recent).all() or not np.isfinite(bg30).all() or not np.isfinite(prior10).all() or not np.isfinite(prior15).all(): continue
            net5=float(recent.sum());tv=float(np.abs(recent).sum())
            if tv<=0 or net5==0: continue
            sign=1.0 if net5>0 else -1.0
            tail1=abs(float(recent[-1]))/tv; tail2=float(np.abs(recent[-2:]).sum())/tv
            if not (tail2>=0.80 and tail1<0.60): continue
            entry=i+1;exit_=entry+10
            if exit_>=len(z) or not valid[entry:exit_+1].all(): continue
            if not (np.isfinite(op[entry]) and np.isfinite(op[exit_]) and op[entry]>0 and op[exit_]>0): continue
            gross=sign*np.log(op[exit_]/op[entry])*1e4
            bg_net=float(bg30.sum()); p10=float(prior10.sum()); p15=float(prior15.sum())
            rows.append({
                "year":int(z.year.iloc[0]),"trading_day":z.trading_day.iloc[0],"session":session,"onset_row":i,"onset_minute":int(z.minute.iloc[i]),
                "sign5":sign,"tail1_share":tail1,"tail2_share":tail2,"eff5":eff(recent),"vol_ratio":float(ratio[i]),"gross_bp":float(gross),
                "bg30_net_bp":bg_net,"bg30_eff":eff(bg30),"same_direction_30":bool(bg_net!=0 and np.sign(bg_net)==sign),
                "prior10_net_bp":p10,"prior10_eff":eff(prior10),"same_direction_10":bool(p10!=0 and np.sign(p10)==sign),
                "prior15_net_bp":p15,"prior15_eff":eff(prior15),"same_direction_15":bool(p15!=0 and np.sign(p15)==sign),
            })
    raw=pd.DataFrame(rows).sort_values(["session","onset_row"]) if rows else pd.DataFrame()
    # Reproduce original candidate non-overlap rule.
    selected=[]
    for session,g in raw.groupby("session",sort=False):
        next_allowed=-1
        for x in g.itertuples(index=False):
            if int(x.onset_row)<next_allowed: continue
            selected.append(x._asdict())
            next_allowed=int(x.onset_row)+11
    return pd.DataFrame(selected)


def summarize(rows:pd.DataFrame)->pd.DataFrame:
    out=[]
    x=rows.copy()
    x["role"]=np.where(x.year<=2023,"Development","Validation")
    x["direction"]=np.where(x.sign5>0,"long","short")
    for keys in [
        ["role","same_direction_30"],
        ["role","direction","same_direction_30"],
        ["year","same_direction_30"],
        ["year","direction","same_direction_30"],
    ]:
        for k,z in x.groupby(keys):
            if not isinstance(k,tuple): k=(k,)
            rec={name:value for name,value in zip(keys,k)}
            n=len(z); mean=float(z.gross_bp.mean())
            rec.update({"n":n,"mean_gross_bp":mean,"hit_rate":float((z.gross_bp>0).mean()),"one_way_break_even_bp":mean/2,
                        "mean_net_1bp_per_leg":mean-2})
            out.append(rec)
    return pd.DataFrame(out)


def run(root:Path,out:Path):
    regime=load_module(root/"docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py","regime_ctx")
    orig=load_module(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_ctx")
    fg=load_module(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","grid_ctx")
    native=orig.load_native(root,"000852.SH").copy();native["trading_day"]=native.trading_day.astype(str).str[:10];native=native[native.trading_day<=END]
    state=regime.build_continuous_state(native,"000852.SH")
    minute=fg.build_minute_grid(native,state.rename(columns={"vol_ratio":"recovery_ratio"}),"000852.SH").reset_index(drop=True)
    minute=minute[(minute.trading_day>="2021-01-01")&(minute.trading_day<=END)].reset_index(drop=True)
    rows=build_rows(minute);summary=summarize(rows)
    out.mkdir(parents=True,exist_ok=True)
    rows.to_csv(out/"candidate_context_rows.csv",index=False);summary.to_csv(out/"context_summary.csv",index=False)
    receipt={"schema":"csi1000_highvol_context_diag_v1","rows":len(rows),"development_rows":int((rows.year<=2023).sum()),"validation_rows":int((rows.year>=2024).sum()),"blackbox_queried":False}
    (out/"summary.json").write_text(json.dumps(receipt,indent=2)+"\n");print(json.dumps(receipt))


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True);a=ap.parse_args();run(Path(a.repo_root).resolve(),Path(a.out))
if __name__=="__main__": main()
