from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("base_cont",HERE/"run_continuous_vol_regime.py")
base=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(base)


def run(root:Path,out:Path):
    orig=base.load_module(root/"docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py","phase2_orig_fast")
    fg=base.load_module(root/"docs/research/state_conditioned_frequency_v2/code/fast_grid.py","phase2_grid_fast")
    filters=orig.load_module(root/"src/star50_filter/filters.py","filters_cont_fast")
    # Exact engineering optimization only: the Phase-2 function was already
    # tested against the repeated reference settlement. Gate names are generic.
    orig.GATES=base.GATES
    orig.COSTS=base.COSTS
    rows=[];receipts=[];state_receipts=[]
    for symbol in base.SYMBOLS:
        native=orig.load_native(root,symbol)
        state=base.build_continuous_state(native,symbol)
        state_receipts.append({"symbol":symbol,"rows":len(state),"high_minutes":int((state.route_state=="HighVol").sum()),"normal_minutes":int((state.route_state=="NormalVol").sum()),"unknown_minutes":int((state.route_state=="Unknown").sum())})
        minute=fg.build_minute_grid(native,state.rename(columns={"vol_ratio":"recovery_ratio"}),symbol)
        for scale in base.SCALES:
            bars=fg.aggregate_scale(minute,scale).reset_index(drop=True)
            receipts.append({"symbol":symbol,"scale_min":scale,"rows":len(bars),"valid":int(bars.valid.sum()),"first_day":bars.trading_day.min(),"last_day":bars.trading_day.max()})
            for family in base.FAMILIES:
                sig,_,_=orig.base_signal(filters,bars,family,scale)
                rows.extend(orig.summarize_all_gates(bars,sig,family,scale,symbol))
    annual=pd.DataFrame(rows)
    dev_pool=base.pool_years(annual,base.DEV_YEARS)
    val_pool=base.pool_years(annual,base.VAL_YEARS)
    nom=base.nominate(annual,dev_pool)
    evaluation=base.evaluate_nomination(annual,dev_pool,val_pool,nom)
    out.mkdir(parents=True,exist_ok=True)
    annual.to_csv(out/"annual_surface.csv",index=False)
    dev_pool.to_csv(out/"development_pool_2021_2023.csv",index=False)
    val_pool.to_csv(out/"validation_pool_2024_2026.csv",index=False)
    nom.to_csv(out/"development_nomination.csv",index=False)
    evaluation.to_csv(out/"validation_evaluation.csv",index=False)
    pd.DataFrame(receipts).to_csv(out/"bar_receipts.csv",index=False)
    pd.DataFrame(state_receipts).to_csv(out/"state_receipts.csv",index=False)
    summary={"schema":"continuous_vol_regime_v1","runner":"single_pass_exact_equivalent","threshold":1.5,"background_floor_bp":1.0,"fast_window_min":5,"background_window_min":30,"overlap":False,"development_years":list(base.DEV_YEARS),"validation_years":[2024,2025,"2026_through_2026-08-21"],"blackbox_queried":False,"nomination":nom.to_dict(orient="records"),"evaluation":evaluation.to_dict(orient="records")}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print(json.dumps(summary,default=str))
    return summary


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--out",required=True)
    args=ap.parse_args();run(Path(args.repo_root).resolve(),Path(args.out))

if __name__=="__main__": main()
