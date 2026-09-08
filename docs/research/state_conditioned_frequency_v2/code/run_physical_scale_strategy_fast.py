from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent


def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

orig=load(HERE/"run_physical_scale_strategy.py","physical_scale_reference")
fg=load(HERE/"fast_grid.py","physical_scale_fast_grid")


def run(root:Path,out:Path):
    state_mod=orig.load_module(root/"docs/research/post_shock_recovery_v1/code/state_sufficiency.py","state_builder_fast")
    filters=orig.load_module(root/"src/star50_filter/filters.py","filters_fast")
    rows=[];anchor=[];bar_receipts=[]
    for symbol in orig.SYMBOLS:
        native=orig.load_native(root,symbol)
        states=orig.route_states(state_mod,native,symbol)
        minute=fg.build_minute_grid(native,states,symbol)
        for scale in orig.SCALES:
            bars=fg.aggregate_scale(minute,scale).reset_index(drop=True)
            bar_receipts.append({"symbol":symbol,"scale_min":scale,"rows":len(bars),"valid":int(bars.valid.sum()),
                "first_day":bars.trading_day.min(),"last_day":bars.trading_day.max()})
            for family in orig.FAMILIES:
                sig,low,sigma=orig.base_signal(filters,bars,family,scale)
                if scale==5:
                    anchor.append({"symbol":symbol,"family":family,
                        "signal_sha":hashlib.sha256(np.asarray(sig,dtype='<f8').tobytes()).hexdigest(),
                        "low_sha":hashlib.sha256(np.asarray(low,dtype='<f8').tobytes()).hexdigest(),
                        "sigma_sha":hashlib.sha256(np.asarray(sigma,dtype='<f8').tobytes()).hexdigest()})
                rows.extend(orig.summarize_all_gates(bars,sig,family,scale,symbol))
    annual=pd.DataFrame(rows)
    pool=orig.pool_years(annual,(2021,2022,2023,2024,2025))
    replay=orig.pool_years(annual,(2026,))
    anchor_df=pd.DataFrame(anchor)
    anchor_ok=True
    for symbol,z in anchor_df.groupby("symbol"):
        anchor_ok &= z.signal_sha.nunique()==1 and z.low_sha.nunique()==1 and z.sigma_sha.nunique()==1
    out.mkdir(parents=True,exist_ok=True)
    annual.to_csv(out/"annual_surface.csv",index=False)
    pool.to_csv(out/"pool_2021_2025.csv",index=False)
    replay.to_csv(out/"replay_2026.csv",index=False)
    pd.DataFrame(bar_receipts).to_csv(out/"bar_receipts.csv",index=False)
    anchor_df.to_csv(out/"five_minute_anchor.csv",index=False)
    result={"schema":"state_conditioned_physical_scale_v2","scales":list(orig.SCALES),"families":list(orig.FAMILIES),
        "gates":list(orig.GATES),"costs_one_way_bp":list(orig.COSTS),"five_minute_anchor_identical":bool(anchor_ok),
        "guardrails":["2021-2025 consumed exploratory history","2026 already-opened consistency replay only",
            "NoEpisode is pre-trigger reference, not Clean","half-session positions forced flat","no scale selection",
            "single-pass settlement and single-grid aggregation are exact-equivalent engineering optimizations only"]}
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    if not anchor_ok: raise RuntimeError("5m family anchor mismatch")
    print(json.dumps(result))
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    args=ap.parse_args();run(Path(args.repo_root).resolve(),Path(args.out))

if __name__=="__main__": main()
