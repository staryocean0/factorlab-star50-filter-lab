from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

HERE=Path(__file__).resolve().parent
V10=HERE.parent/"highvol_realtime_probability_lead_v10"/"run_v10.py"
VAL_YEARS=(2024,2025)
REF_YEARS=(2020,2021,2022,2023,2024,2025)
SYMBOLS=("000688.SH","000852.SH")
LEADS=(60,30,15,6,3)
PRIMARY_LEAD=15
FROZEN_V10_BLOB="783b5bb474758956b7b86a0e8c72a1264ab2e1e5"


def load_v10():
    import subprocess
    got=subprocess.check_output(["git","hash-object",str(V10)],text=True).strip()
    if got!=FROZEN_V10_BLOB: raise RuntimeError(f"V10 runner drift: {got}")
    spec=importlib.util.spec_from_file_location("v10_frozen_validation",V10)
    if spec is None or spec.loader is None: raise RuntimeError(V10)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.REF_YEARS=REF_YEARS; mod.DEV_YEARS=VAL_YEARS; mod.SYMBOLS=SYMBOLS; mod.LEADS=LEADS; mod.PRIMARY_LEAD=PRIMARY_LEAD
    return mod


def run(root:Path,out:Path)->dict:
    v10=load_v10(); mod=v10.load_v9(root)
    pieces=[]
    for symbol in SYMBOLS:
        ref=mod.load_reference(root,symbol); rr=mod.reference_rows(ref)
        for lead in LEADS:
            mod.PRIMARY_LEAD_SECONDS=lead
            x=mod.attach_realtime(root,ref,rr,symbol); x["lead_seconds"]=lead; pieces.append(x)
    detail=pd.concat(pieces,ignore_index=True)
    rows=[]
    for lead in LEADS:
        z=detail[detail.lead_seconds.eq(lead)]
        rows.append({"lead_seconds":lead,**mod.summarize(z,"pooled","pooled")})
        for y in VAL_YEARS: rows.append({"lead_seconds":lead,**mod.summarize(z[z.year.eq(y)],"year",str(y))})
        for s in SYMBOLS: rows.append({"lead_seconds":lead,**mod.summarize(z[z.symbol.eq(s)],"symbol",s)})
    primary=next(r for r in rows if r["lead_seconds"]==15 and r["group_type"]=="pooled")
    annual=[r for r in rows if r["lead_seconds"]==15 and r["group_type"]=="year"]
    acceptance={
      "lead15_pooled_coverage_ge_098":primary["realtime_probability_coverage"]>=0.98,
      "lead15_each_year_coverage_ge_095":all(r["realtime_probability_coverage"]>=0.95 for r in annual),
      "lead15_pooled_probability_mae_le_001":primary["probability_mae_vs_reference"]<=0.01,
      "lead15_pooled_brier_degradation_le_0002":primary["brier_degradation_matched"]<=0.002,
      "lead15_each_year_brier_degradation_le_0005":all(r["brier_degradation_matched"]<=0.005 for r in annual),
      "frozen_v10_runner_unchanged":True,
      "frozen_v9_runner_unchanged":True,
      "probability_fit_performed_false":True,
      "threshold_search_performed_false":True,
      "blackbox_queried_false":True,
      "pnl_computed_false":True,
      "trading_rule_created_false":True,
    }
    summary={
      "schema":"highvol_realtime_probability_lead_v10_validation_subset",
      "validation_subset_years":list(VAL_YEARS),
      "validation_complete_through_2026_08_21":False,
      "validation_2026_queried":False,
      "frozen_development_commit":"c20927b4982655a218521e1187efab2de6ada050",
      "frozen_development_run_id":34445913929,
      "frozen_development_artifact_id":10139657807,
      "leads_seconds":list(LEADS),"primary_lead_seconds":15,
      "probability_fit_performed":False,"threshold_search_performed":False,"blackbox_queried":False,
      "pnl_computed":False,"trading_rule_created":False,"production_authority":False,
      "summary_rows":rows,"acceptance":acceptance,
      "available_validation_subset_pass":bool(all(acceptance.values())),"complete_validation_pass":False,
    }
    out.mkdir(parents=True,exist_ok=True); detail.to_parquet(out/"detail.parquet",index=False)
    (out/"summary.json").write_text(json.dumps(mod.clean(summary),indent=2,sort_keys=True)+"\n")
    print(json.dumps(mod.clean(summary),sort_keys=True)); return summary

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path(".")); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); run(a.repo_root.resolve(),a.out.resolve())
