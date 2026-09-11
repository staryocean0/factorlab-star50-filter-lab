from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
VALID_YEARS = (2024, 2025)
REF_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
SOURCE_STATES = ("NORMAL", "RECOVERING")
LEADS = (60, 30, 15, 6, 3)
PRIMARY_LEAD = 15
FROZEN_V18_BLOB = "62c207badff1c3e37cbb1a8e17ef89feeea611d8"
FROZEN_V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
SOURCE_COMMIT = "542b11857baeaebd43d93dc5ac866c6c3316e477"
SOURCE_RUN = 34606023820
SOURCE_ARTIFACT = 10266486662

HERE = Path(__file__).resolve().parent
FROZEN_V18 = HERE / "frozen_v18.py"


def load_frozen_v18():
    got = subprocess.check_output(["git", "hash-object", str(FROZEN_V18)], text=True).strip()
    if got != FROZEN_V18_BLOB:
        raise RuntimeError(f"frozen V18 blob drift: {got}")
    spec = importlib.util.spec_from_file_location("v18_validation_frozen", FROZEN_V18)
    if spec is None or spec.loader is None:
        raise RuntimeError(FROZEN_V18)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SYMBOLS = SYMBOLS
    mod.REF_YEARS = REF_YEARS
    mod.DEV_YEARS = VALID_YEARS
    mod.SOURCE_STATES = SOURCE_STATES
    mod.LEADS = LEADS
    mod.PRIMARY_LEAD = PRIMARY_LEAD
    if mod.FROZEN_V9_BLOB != FROZEN_V9_BLOB:
        raise RuntimeError("frozen V9 identity drift")
    return mod


def run(root: Path, out: Path) -> dict:
    v18 = load_frozen_v18()
    v9 = v18.load_v9()
    refs = {s: v9.load_reference(root, s) for s in SYMBOLS}

    candidate_parts = []
    boundary = {}
    for s in SYMBOLS:
        c, b = v18.candidate_rows(v9, refs[s])
        candidate_parts.append(c)
        boundary[s] = b
    candidates = pd.concat(candidate_parts, ignore_index=True)
    if candidates.candidate_id.duplicated().any():
        raise RuntimeError("candidate_id collision")
    if sorted(candidates.year.unique().tolist()) != list(VALID_YEARS):
        raise RuntimeError("Validation candidate year boundary drift")

    detail_parts = []
    for lead in LEADS:
        for s in SYMBOLS:
            detail_parts.append(v18.attach_checkpoint(v9, root, refs[s], candidates, s, lead))
    detail = pd.concat(detail_parts, ignore_index=True)
    if sorted(detail.year.unique().tolist()) != list(VALID_YEARS):
        raise RuntimeError("Validation detail year boundary drift")

    pooled_by_lead = {}
    for lead in LEADS:
        z = detail[detail.lead_seconds.eq(lead)]
        pooled_by_lead[str(lead)] = v18.summarize(z, "pooled", "pooled")

    primary = detail[detail.lead_seconds.eq(PRIMARY_LEAD)].copy()
    yearly = {str(y): v18.summarize(primary[primary.year.eq(y)], "year", y) for y in VALID_YEARS}
    by_symbol = {s: v18.summarize(primary[primary.symbol.eq(s)], "symbol", s) for s in SYMBOLS}
    by_source_state = {s: v18.summarize(primary[primary.source_state.eq(s)], "source_state", s) for s in SOURCE_STATES}
    pathway_counts = candidates[candidates.final_switch_on].switch_pathway.value_counts().to_dict()
    curve = v18.evidence_curve(detail, candidates)

    p = pooled_by_lead[str(PRIMARY_LEAD)]
    acceptance = {
        "pooled_candidate_rows_ge_30000": p["candidate_rows"] >= 30000,
        "pooled_true_switch_on_events_ge_300": p["true_switch_on_events"] >= 300,
        "each_validation_year_true_switch_on_events_ge_50": all(yearly[str(y)]["true_switch_on_events"] >= 50 for y in VALID_YEARS),
        "pooled_checkpoint_coverage_ge_098": p["checkpoint_coverage"] >= 0.98,
        "each_validation_year_checkpoint_coverage_ge_095": all(yearly[str(y)]["checkpoint_coverage"] >= 0.95 for y in VALID_YEARS),
        "pooled_precision_ge_090": p["precision"] is not None and p["precision"] >= 0.90,
        "pooled_recall_ge_080": p["recall"] is not None and p["recall"] >= 0.80,
        "pooled_false_positive_rate_le_001": p["false_positive_rate"] is not None and p["false_positive_rate"] <= 0.01,
        "each_validation_year_precision_ge_085": all(yearly[str(y)]["precision"] is not None and yearly[str(y)]["precision"] >= 0.85 for y in VALID_YEARS),
        "each_validation_year_recall_ge_070": all(yearly[str(y)]["recall"] is not None and yearly[str(y)]["recall"] >= 0.70 for y in VALID_YEARS),
        "each_validation_year_false_positive_rate_le_002": all(yearly[str(y)]["false_positive_rate"] is not None and yearly[str(y)]["false_positive_rate"] <= 0.02 for y in VALID_YEARS),
        "both_symbols_have_true_events_and_true_positives": all(by_symbol[s]["true_switch_on_events"] > 0 and by_symbol[s]["tp"] > 0 for s in SYMBOLS),
        "frozen_v18_runner_unchanged": True,
        "frozen_v9_runner_and_thresholds_unchanged": True,
        "threshold_search_performed_false": True,
        "feature_search_performed_false": True,
        "probability_fit_performed_false": True,
        "lead_time_selection_performed_false": True,
        "posthoc_subgroup_selection_false": True,
        "no_2026_3s_queried": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }

    summary = {
        "schema": "highvol_unsafe_switch_on_v18_reusable_validation_v1",
        "reusable_validation": True,
        "validation_period": ["2024-01-01", "2025-12-31"],
        "validation_years": list(VALID_YEARS),
        "queried_3s_years": list(VALID_YEARS),
        "queried_2026_3s": False,
        "symbols": list(SYMBOLS),
        "source_states": list(SOURCE_STATES),
        "fixed_leads_seconds": list(LEADS),
        "primary_lead_seconds": PRIMARY_LEAD,
        "frozen_development_authority": {
            "source_execution_commit": SOURCE_COMMIT,
            "source_run_id": SOURCE_RUN,
            "source_artifact_id": SOURCE_ARTIFACT,
            "frozen_v18_runner_blob": FROZEN_V18_BLOB,
            "frozen_v9_runner_blob": FROZEN_V9_BLOB,
        },
        "candidate_rows": int(len(candidates)),
        "year_row_counts": {str(y): int((candidates.year == y).sum()) for y in VALID_YEARS},
        "boundary_exclusions": boundary,
        "true_switch_on_events": int(candidates.final_switch_on.sum()),
        "switch_pathway_counts": pathway_counts,
        "pooled_by_lead": pooled_by_lead,
        "primary_yearly": yearly,
        "primary_by_symbol": by_symbol,
        "primary_by_source_state": by_source_state,
        "evidence_curve": curve,
        "threshold_search_performed": False,
        "feature_search_performed": False,
        "probability_fit_performed": False,
        "lead_time_selection_performed": False,
        "posthoc_subgroup_selection": False,
        "validation_queried": True,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
        "acceptance": acceptance,
        "full_validation_supported": bool(all(acceptance.values())),
    }

    out.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(out / "candidate_rows.parquet", index=False)
    detail.to_parquet(out / "checkpoint_detail.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(v18.clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(v18.clean(summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
