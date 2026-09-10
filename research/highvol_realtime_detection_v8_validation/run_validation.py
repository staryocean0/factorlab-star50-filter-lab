from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
BASE_RUNNER = HERE.parent / "highvol_realtime_detection_v8" / "run_detection.py"
BASE_PROTOCOL = HERE.parent / "highvol_realtime_detection_v8" / "protocol.md"
FROZEN_PATH = HERE / "FROZEN_DETECTOR_V8.json"

VAL_YEARS = (2024, 2025)
REF_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
SYMBOLS = ("000688.SH", "000852.SH")
LEADS = (60, 30, 15, 6, 3)
PRIMARY_LEAD = 3


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def load_frozen() -> dict:
    frozen = json.loads(FROZEN_PATH.read_text())
    if git_blob_sha(BASE_RUNNER) != frozen["source_runner_blob_sha"]:
        raise RuntimeError("frozen V8 runner blob drift")
    if git_blob_sha(BASE_PROTOCOL) != frozen["source_protocol_blob_sha"]:
        raise RuntimeError("frozen V8 protocol blob drift")
    if frozen["primary_lead_seconds"] != PRIMARY_LEAD:
        raise RuntimeError("primary lead drift")
    if tuple(frozen["leads_seconds"]) != LEADS:
        raise RuntimeError("lead set drift")
    return frozen


def load_base():
    spec = importlib.util.spec_from_file_location("highvol_realtime_detection_v8_frozen", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(BASE_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.DEV_YEARS = VAL_YEARS
    mod.REF_YEARS = REF_YEARS
    mod.SYMBOLS = SYMBOLS
    mod.LEADS = LEADS
    return mod


def check_base_constants(mod, frozen: dict) -> None:
    expected = {
        "RV_WINDOW": frozen["rv_window"],
        "BG_WINDOW": frozen["bg_window"],
        "HIGHVOL_RATIO": frozen["highvol_ratio"],
        "RECOVERY_NORMAL_RATIO": frozen["recovery_normal_ratio"],
        "SHOCK_SIGMA": frozen["shock_sigma"],
    }
    got = {k: getattr(mod, k) for k in expected}
    if got != expected:
        raise RuntimeError(f"frozen constants drift: {got} != {expected}")


def metric(rows: list[dict], lead: int, group_type: str, group_value: str) -> dict:
    return next(
        r for r in rows
        if r["lead_seconds"] == lead
        and r["group_type"] == group_type
        and r["group_value"] == group_value
    )


def run(root: Path, out: Path) -> dict:
    frozen = load_frozen()
    mod = load_base()
    check_base_constants(mod, frozen)

    detail_parts = []
    coverage_parts = []
    for symbol in SYMBOLS:
        detail, coverage = mod.build_rows_for_symbol(root, symbol)
        detail_parts.append(detail)
        coverage_parts.append(coverage)

    detail = pd.concat(detail_parts, ignore_index=True)
    coverage = pd.concat(coverage_parts, ignore_index=True)
    metrics = mod.summaries(detail, coverage)
    onset_lead = mod.onset_leads(detail, coverage)

    pooled = metric(metrics, PRIMARY_LEAD, "pooled", "pooled")
    annual = [metric(metrics, PRIMARY_LEAD, "year", str(y)) for y in VAL_YEARS]

    thresholds = frozen["development_acceptance"]
    acceptance = {
        "lead3_pooled_coverage_ge_095": pooled["coverage"] >= thresholds["pooled_coverage_min"],
        "lead3_each_year_coverage_ge_095": all(r["coverage"] >= thresholds["annual_coverage_min"] for r in annual),
        "lead3_pooled_unsafe_precision_ge_090": pooled["unsafe"]["precision"] is not None and pooled["unsafe"]["precision"] >= thresholds["pooled_unsafe_precision_min"],
        "lead3_pooled_unsafe_recall_ge_090": pooled["unsafe"]["recall"] is not None and pooled["unsafe"]["recall"] >= thresholds["pooled_unsafe_recall_min"],
        "lead3_each_year_unsafe_precision_ge_085": all(r["unsafe"]["precision"] is not None and r["unsafe"]["precision"] >= thresholds["annual_unsafe_precision_min"] for r in annual),
        "lead3_each_year_unsafe_recall_ge_085": all(r["unsafe"]["recall"] is not None and r["unsafe"]["recall"] >= thresholds["annual_unsafe_recall_min"] for r in annual),
        "frozen_runner_blob_unchanged": True,
        "frozen_protocol_blob_unchanged": True,
        "state_thresholds_unchanged": True,
        "threshold_search_performed_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
        "blackbox_queried_false": True,
    }

    summary = {
        "schema": "highvol_realtime_detection_v8_3s_validation_subset",
        "validation_subset": ["2024-01-01", "2025-12-31"],
        "validation_subset_years": list(VAL_YEARS),
        "validation_complete_through_2026_08_21": False,
        "validation_2026_queried": False,
        "validation_subset_limitation": "repository 3s physical contract ends 2025-12-31; 2026 remains unvalidated",
        "frozen_source_commit": frozen["source_commit"],
        "frozen_development_run_id": frozen["development_run_id"],
        "frozen_development_artifact_id": frozen["development_artifact_id"],
        "symbols": list(SYMBOLS),
        "reference_years": list(REF_YEARS),
        "leads_seconds": list(LEADS),
        "primary_lead_seconds": PRIMARY_LEAD,
        "selection": frozen["selection"],
        "threshold_search_performed": False,
        "state_thresholds_unchanged": True,
        "pnl_computed": False,
        "trading_rule_created": False,
        "blackbox_queried": False,
        "production_authority": False,
        "available_detection_rows": int(len(detail)),
        "eligible_checkpoint_rows": int(len(coverage)),
        "metrics": metrics,
        "unsafe_onset_lead": onset_lead,
        "acceptance": acceptance,
        "available_validation_subset_pass": bool(all(acceptance.values())),
        "complete_validation_pass": False,
    }

    out.mkdir(parents=True, exist_ok=True)
    detail.to_parquet(out / "detail.parquet", index=False)
    coverage.to_parquet(out / "coverage.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(mod.clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(mod.clean(summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
