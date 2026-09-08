#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

DECL_PATH = Path("docs/governance/data_usage_declaration.json")
LEDGER_PATH = Path("docs/governance/blackbox_query_ledger.json")
POLICY_PATH = Path("docs/governance/DATA_USAGE_POLICY_V2.md")
EXPECTED_SCHEMA = "factorlab_star50_filter_lab_data_usage_v2"
LEDGER_SCHEMA = "factorlab_blackbox_query_ledger_v1"
FORBIDDEN_BLACKBOX_KEYS = {"dates","timestamps","daily","events","sessions","paths","top_contributors","worst_examples","best_examples","error_cases"}
REQUIRED_QUERY_KEYS = {"candidate_id","code_sha","config_hash","data_manifest_sha256","registered_metrics","query_timestamp","result_digest"}

def _load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def _iso(value: str) -> date:
    return date.fromisoformat(value)

def validate(root: Path) -> list[str]:
    errors=[]
    decl_path=root/DECL_PATH;ledger_path=root/LEDGER_PATH;policy_path=root/POLICY_PATH
    for path in (decl_path,ledger_path,policy_path):
        if not path.exists():errors.append(f"missing required governance file: {path.relative_to(root)}")
    if errors:return errors
    decl=_load(decl_path);ledger=_load(ledger_path)
    if decl.get("schema")!=EXPECTED_SCHEMA:errors.append("unexpected data-usage declaration schema")
    if ledger.get("schema")!=LEDGER_SCHEMA:errors.append("unexpected black-box ledger schema")
    if decl.get("policy")!=str(POLICY_PATH):errors.append("declaration does not point at V2 policy")
    if decl.get("production_authority") is not False:errors.append("production authority must remain false")
    roles=decl.get("roles",{})
    for name in ("development","validation","blackbox_v1"):
        if name not in roles:errors.append(f"missing role: {name}")
    if errors:return errors
    dev=roles["development"];val=roles["validation"];bb=roles["blackbox_v1"]
    try:
        dev_start=_iso(dev["date_start"]);dev_end=_iso(dev["date_end"]);val_start=_iso(val["date_start"]);val_end=_iso(val["date_end"])
    except (KeyError,TypeError,ValueError) as exc:errors.append(f"invalid development/validation dates: {exc}")
    else:
        if not (dev_start<=dev_end<val_start<=val_end):errors.append("development and validation date ranges overlap or are unordered")
        if val_end.isoformat()!="2026-08-21":errors.append("validation cutoff must remain frozen at 2026-08-21 unless owner changes policy")
    if dev.get("fit_allowed") is not True or dev.get("repeat_use") is not True:errors.append("development must remain open for fitting and repeated use")
    if val.get("fit_allowed_for_candidate_under_test") is not False:errors.append("validation rows must not fit the candidate under test")
    if val.get("diagnostic_inspection_allowed") is not True:errors.append("validation must permit detailed diagnostics")
    if val.get("may_inform_next_iteration") is not True or val.get("repeat_use") is not True:errors.append("validation must remain reusable for iterative research")
    if val.get("fresh_oos") is not False:errors.append("validation must not be labelled fresh OOS")
    if bb.get("definition")!="first_60_complete_trading_days_strictly_after_2026-08-21":errors.append("blackbox_v1 definition changed")
    if bb.get("required_complete_trading_days")!=60:errors.append("blackbox_v1 must contain exactly the first 60 complete trading days")
    if bb.get("detail_access")!="forbidden":errors.append("blackbox detail access must be forbidden")
    if bb.get("fit_allowed") is not False:errors.append("blackbox fitting must be forbidden")
    if bb.get("repeat_use") is not True:errors.append("blackbox must remain reusable through the blinded interface")
    if bb.get("query_interface")!="registered_aggregate_metrics_only":errors.append("blackbox query interface is not locked to registered aggregates")
    if bb.get("unblind_transition")!="reclassify_to_validation_not_destroyed":errors.append("blackbox unblinding must reclassify, not destroy, the data")
    if ledger.get("blackbox_id")!="blackbox_v1":errors.append("ledger is not bound to blackbox_v1")
    if ledger.get("status")!=bb.get("status"):errors.append("ledger status and declaration blackbox status differ")
    status=bb.get("status")
    if status=="pending_data":
        if bb.get("exact_date_start") is not None or bb.get("exact_date_end") is not None:errors.append("pending blackbox must not have frozen exact dates")
        if ledger.get("frozen_manifest_sha256") is not None:errors.append("pending blackbox ledger must not claim a frozen manifest")
    elif status=="frozen":
        if not bb.get("exact_date_start") or not bb.get("exact_date_end"):errors.append("frozen blackbox requires exact dates")
        if not ledger.get("frozen_manifest_sha256"):errors.append("frozen blackbox requires manifest SHA256 in ledger")
        if ledger.get("exact_date_start")!=bb.get("exact_date_start") or ledger.get("exact_date_end")!=bb.get("exact_date_end"):errors.append("ledger and declaration blackbox dates differ")
    else:errors.append(f"unsupported blackbox status: {status!r}")
    queries=ledger.get("queries")
    if not isinstance(queries,list):errors.append("blackbox ledger queries must be a list")
    else:
        for i,query in enumerate(queries):
            if not isinstance(query,dict):errors.append(f"query[{i}] must be an object");continue
            missing=REQUIRED_QUERY_KEYS-set(query)
            if missing:errors.append(f"query[{i}] missing keys: {sorted(missing)}")
            exposed=FORBIDDEN_BLACKBOX_KEYS&set(query)
            if exposed:errors.append(f"query[{i}] contains forbidden detail keys: {sorted(exposed)}")
            metrics=query.get("registered_metrics")
            if metrics is not None and (not isinstance(metrics,list) or not metrics):errors.append(f"query[{i}] registered_metrics must be a non-empty list")
    return errors

def main()->int:
    parser=argparse.ArgumentParser(description="Validate repository three-pool data-use governance.");parser.add_argument("--repo-root",default=".");args=parser.parse_args();root=Path(args.repo_root).resolve();errors=validate(root)
    if errors:
        for error in errors:print(f"ERROR: {error}")
        return 1
    print("data usage policy V2: OK");return 0

if __name__=="__main__":raise SystemExit(main())
