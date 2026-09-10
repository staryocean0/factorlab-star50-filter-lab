from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
BASE_RUNNER = HERE.parent / "highvol_realtime_risk_object_v9" / "run_v9.py"
BASE_PROTOCOL = HERE.parent / "highvol_realtime_risk_object_v9" / "PROTOCOL.md"
FROZEN = HERE / "FROZEN_RISK_OBJECT_V9.json"
VAL_YEARS = (2024, 2025)
REF_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
SYMBOLS = ("000688.SH", "000852.SH")


def git_blob_sha(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()


def load_base():
    frozen = json.loads(FROZEN.read_text())
    if git_blob_sha(BASE_RUNNER) != frozen["source_runner_blob_sha"]:
        raise RuntimeError("V9 runner blob drift")
    if git_blob_sha(BASE_PROTOCOL) != frozen["source_protocol_blob_sha"]:
        raise RuntimeError("V9 protocol blob drift")
    spec = importlib.util.spec_from_file_location("v9_frozen", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(BASE_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.DEV_YEARS = VAL_YEARS
    mod.REF_YEARS = REF_YEARS
    mod.SYMBOLS = SYMBOLS
    return mod, frozen


def run(root: Path, out: Path) -> dict:
    mod, frozen = load_base()
    if mod.PRIMARY_LEAD_SECONDS != frozen["primary_lead_seconds"]:
        raise RuntimeError("primary lead drift")
    expected_prob = {(k.split("/",1)[0], k.split("/",1)[1]): v for k,v in frozen["probability_table"].items()}
    if mod.PROB != expected_prob:
        raise RuntimeError("V6 probability table drift")
    constants = {
        "RV_WINDOW": frozen["rv_window"],
        "BG_WINDOW": frozen["bg_window"],
        "HIGHVOL_RATIO": frozen["highvol_ratio"],
        "RECOVERY_NORMAL_RATIO": frozen["recovery_normal_ratio"],
        "SHOCK_SIGMA": frozen["shock_sigma"],
    }
    if any(getattr(mod,k) != v for k,v in constants.items()):
        raise RuntimeError("V8/V6 state constants drift")

    pieces=[]
    for symbol in SYMBOLS:
        ref=mod.load_reference(root, symbol)
        rr=mod.reference_rows(ref)
        pieces.append(mod.attach_realtime(root, ref, rr, symbol))
    detail=pd.concat(pieces, ignore_index=True)
    rows=[mod.summarize(detail,"pooled","pooled")]
    rows += [mod.summarize(detail[detail.year.eq(y)],"year",str(y)) for y in VAL_YEARS]
    rows += [mod.summarize(detail[detail.symbol.eq(s)],"symbol",s) for s in SYMBOLS]
    pooled=rows[0]
    annual=rows[1:3]
    a=frozen["acceptance"]
    acceptance={
        "pooled_coverage_ge_098": pooled["realtime_probability_coverage"] >= a["pooled_coverage_min"],
        "each_year_coverage_ge_095": all(r["realtime_probability_coverage"] >= a["annual_coverage_min"] for r in annual),
        "pooled_probability_mae_le_001": pooled["probability_mae_vs_reference"] <= a["pooled_probability_mae_max"],
        "pooled_brier_degradation_le_0002": pooled["brier_degradation_matched"] <= a["pooled_brier_degradation_max"],
        "each_year_brier_degradation_le_0005": all(r["brier_degradation_matched"] <= a["annual_brier_degradation_max"] for r in annual),
        "primary_checkpoint_is_E_minus_3s": mod.PRIMARY_LEAD_SECONDS == 3,
        "v6_probability_table_unchanged": True,
        "v8_state_thresholds_unchanged": True,
        "probability_fit_performed_false": True,
        "threshold_search_performed_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
        "blackbox_queried_false": True,
    }
    summary={
        "schema":"highvol_realtime_risk_object_v9_validation_subset",
        "validation_subset":["2024-01-01","2025-12-31"],
        "validation_subset_years":list(VAL_YEARS),
        "validation_complete_through_2026_08_21":False,
        "validation_2026_queried":False,
        "validation_subset_limitation":"3s physical contract ends 2025-12-31",
        "frozen_source_commit":frozen["source_commit"],
        "frozen_development_run_id":frozen["development_run_id"],
        "frozen_development_artifact_id":frozen["development_artifact_id"],
        "symbols":list(SYMBOLS),
        "primary_lead_seconds":3,
        "probability_fit_performed":False,
        "threshold_search_performed":False,
        "pnl_computed":False,
        "trading_rule_created":False,
        "blackbox_queried":False,
        "production_authority":False,
        "summary_rows":rows,
        "acceptance":acceptance,
        "available_validation_subset_pass":bool(all(acceptance.values())),
        "complete_validation_pass":False,
    }
    out.mkdir(parents=True,exist_ok=True)
    detail.to_parquet(out/"detail.parquet",index=False)
    (out/"summary.json").write_text(json.dumps(mod.clean(summary),indent=2,sort_keys=True)+"\n")
    print(json.dumps(mod.clean(summary),sort_keys=True))
    return summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path(".")); ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args(); run(args.repo_root.resolve(),args.out.resolve())

if __name__=="__main__": main()
