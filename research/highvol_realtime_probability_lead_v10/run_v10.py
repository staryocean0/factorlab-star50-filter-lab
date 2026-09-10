from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pandas as pd

SYMBOLS=("000688.SH","000852.SH")
REF_YEARS=(2020,2021,2022,2023)
DEV_YEARS=(2021,2022,2023)
LEADS=(60,30,15,6,3)
PRIMARY_LEAD=15
FROZEN_V9_BLOB="ae2a7e095df58692ef9df0dfee5856cac727ca44"


def load_v9(root:Path):
    p=root/"research/highvol_realtime_probability_lead_v10/frozen_v9.py"
    if not p.exists(): raise RuntimeError("missing materialized frozen_v9.py")
    import subprocess
    got=subprocess.check_output(["git","hash-object",str(p)],text=True).strip()
    if got!=FROZEN_V9_BLOB: raise RuntimeError(f"frozen V9 blob drift: {got}")
    spec=importlib.util.spec_from_file_location("frozen_v9_lead_curve",p)
    if spec is None or spec.loader is None: raise RuntimeError(p)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.REF_YEARS=REF_YEARS; mod.DEV_YEARS=DEV_YEARS; mod.SYMBOLS=SYMBOLS
    return mod


def run(root:Path,out:Path)->dict:
    mod=load_v9(root)
    pieces=[]
    for symbol in SYMBOLS:
        ref=mod.load_reference(root,symbol)
        rr=mod.reference_rows(ref)
        for lead in LEADS:
            mod.PRIMARY_LEAD_SECONDS=lead
            x=mod.attach_realtime(root,ref,rr,symbol)
            x["lead_seconds"]=lead
            pieces.append(x)
    detail=pd.concat(pieces,ignore_index=True)
    rows=[]
    for lead in LEADS:
        z=detail[detail.lead_seconds.eq(lead)]
        rows.append({"lead_seconds":lead,**mod.summarize(z,"pooled","pooled")})
        for y in DEV_YEARS:
            rows.append({"lead_seconds":lead,**mod.summarize(z[z.year.eq(y)],"year",str(y))})
        for s in SYMBOLS:
            rows.append({"lead_seconds":lead,**mod.summarize(z[z.symbol.eq(s)],"symbol",s)})
    primary=next(r for r in rows if r["lead_seconds"]==PRIMARY_LEAD and r["group_type"]=="pooled")
    annual=[r for r in rows if r["lead_seconds"]==PRIMARY_LEAD and r["group_type"]=="year"]
    acceptance={
      "lead15_pooled_coverage_ge_098":primary["realtime_probability_coverage"]>=0.98,
      "lead15_each_year_coverage_ge_095":all(r["realtime_probability_coverage"]>=0.95 for r in annual),
      "lead15_pooled_probability_mae_le_001":primary["probability_mae_vs_reference"]<=0.01,
      "lead15_pooled_brier_degradation_le_0002":primary["brier_degradation_matched"]<=0.002,
      "lead15_each_year_brier_degradation_le_0005":all(r["brier_degradation_matched"]<=0.005 for r in annual),
      "frozen_v9_blob_unchanged":True,
      "validation_queried_false":True,
      "blackbox_queried_false":True,
      "pnl_computed_false":True,
      "trading_rule_created_false":True,
    }
    summary={
      "schema":"highvol_realtime_probability_lead_v10_development",
      "development_only":True,
      "development_period":["2021-01-01","2023-12-31"],
      "symbols":list(SYMBOLS),
      "leads_seconds":list(LEADS),
      "primary_lead_seconds":PRIMARY_LEAD,
      "frozen_v9_source_commit":"e01b293dcfc3100a02265315376bc63a9137c3d3",
      "frozen_v9_runner_blob":FROZEN_V9_BLOB,
      "probability_fit_performed":False,
      "threshold_search_performed":False,
      "validation_queried":False,
      "blackbox_queried":False,
      "pnl_computed":False,
      "trading_rule_created":False,
      "production_authority":False,
      "summary_rows":rows,
      "acceptance":acceptance,
      "lead15_validation_eligible":bool(all(acceptance.values())),
    }
    out.mkdir(parents=True,exist_ok=True)
    detail.to_parquet(out/"detail.parquet",index=False)
    (out/"summary.json").write_text(json.dumps(mod.clean(summary),indent=2,sort_keys=True)+"\n")
    print(json.dumps(mod.clean(summary),sort_keys=True))
    return summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path(".")); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); run(a.repo_root.resolve(),a.out.resolve())

if __name__=="__main__": main()
