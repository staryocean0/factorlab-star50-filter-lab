from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
REF_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
VAL_YEARS = (2024, 2025)
EXPECTED_V19_BLOB = "ee2fce299d5ee21abf1ab2c2c5183bac101ae822"
EXPECTED_V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
EXPECTED_V18_BLOB = "62c207badff1c3e37cbb1a8e17ef89feeea611d8"
EXPECTED_V17_BLOB = "397d80037806ba11cadf7f77717d36d55fbafc91"
EXPECTED_V16_SURFACE_BLOB = "1f88966cf5dd3fb102f0d75746d5d00434555647"
SOURCE_DEVELOPMENT_COMMIT = "6fad49e5dc674d9a48b5c1719e060eceabc166d2"
SOURCE_DEVELOPMENT_RUN = 34611126345
SOURCE_DEVELOPMENT_ARTIFACT = 10267923594

HERE = Path(__file__).resolve().parent
FROZEN_V19 = HERE / "frozen_v19.py"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_v19():
    got = git_blob_sha(FROZEN_V19)
    if got != EXPECTED_V19_BLOB:
        raise RuntimeError(f"frozen V19 blob drift: {got}")
    spec = importlib.util.spec_from_file_location("v19_frozen_for_validation", FROZEN_V19)
    if spec is None or spec.loader is None:
        raise RuntimeError(FROZEN_V19)
    v19 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v19)
    v19.SYMBOLS = SYMBOLS
    v19.REF_YEARS = REF_YEARS
    v19.DEV_YEARS = VAL_YEARS
    return v19


def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (np.floating, float)):
        x = float(v)
        return x if np.isfinite(x) else None
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    return v


def run(root: Path, out: Path) -> dict:
    v19 = load_v19()
    v9, adaptive, age_only, blob_receipt = v19.load_frozen_authority()

    expected_upstream = {
        "frozen_v9.py": EXPECTED_V9_BLOB,
        "frozen_v18.py": EXPECTED_V18_BLOB,
        "frozen_v17.py": EXPECTED_V17_BLOB,
        "frozen_v16_surface.json": EXPECTED_V16_SURFACE_BLOB,
    }
    if blob_receipt != expected_upstream:
        raise RuntimeError(f"upstream frozen authority drift: {blob_receipt}")

    pieces = []
    boundary = {}
    for symbol in SYMBOLS:
        x, b = v19.build_symbol_rows(root, v9, symbol)
        pieces.append(x)
        boundary[symbol] = b
    detail = pd.concat(pieces, ignore_index=True)
    if detail.candidate_id.duplicated().any():
        raise RuntimeError("candidate_id collision")
    if set(detail.year.unique()) != set(VAL_YEARS):
        raise RuntimeError(f"Validation year drift: {sorted(detail.year.unique())}")

    detail = v19.attach_recovery_probabilities(detail, v9, adaptive, age_only)
    detail = v19.add_episode_ids(detail, "reference_risk", "reference_e15_state", "reference_episode_id", "REF")
    detail = v19.add_episode_ids(detail, "machine_risk", "machine_state", "machine_episode_id", "MACH")

    pooled = v19.classification_summary(detail)
    yearly = {str(y): v19.classification_summary(detail[detail.year.eq(y)]) for y in VAL_YEARS}
    by_symbol = {s: v19.classification_summary(detail[detail.symbol.eq(s)]) for s in SYMBOLS}
    transitions = v19.transition_summary(detail)
    ref_ep, mach_ep, episodes = v19.episode_tables(detail)
    prob = v19.probability_integrity(detail)

    ep_pool = episodes["pooled"]
    acceptance = {
        "pooled_evaluable_checkpoints_ge_30000": int(len(detail)) >= 30000,
        "pooled_reference_episodes_ge_300": ep_pool["reference_episodes"] >= 300,
        "each_validation_year_reference_episodes_ge_50": all(episodes["yearly"][str(y)]["reference_episodes"] >= 50 for y in VAL_YEARS),
        "pooled_checkpoint_coverage_ge_098": pooled["checkpoint_coverage"] is not None and pooled["checkpoint_coverage"] >= 0.98,
        "each_validation_year_checkpoint_coverage_ge_095": all(yearly[str(y)]["checkpoint_coverage"] is not None and yearly[str(y)]["checkpoint_coverage"] >= 0.95 for y in VAL_YEARS),
        "pooled_risk_precision_ge_098": pooled["risk_precision"] is not None and pooled["risk_precision"] >= 0.98,
        "pooled_risk_recall_ge_098": pooled["risk_recall"] is not None and pooled["risk_recall"] >= 0.98,
        "pooled_false_positive_rate_le_0005": pooled["false_positive_rate"] is not None and pooled["false_positive_rate"] <= 0.005,
        "each_validation_year_risk_precision_ge_095": all(yearly[str(y)]["risk_precision"] is not None and yearly[str(y)]["risk_precision"] >= 0.95 for y in VAL_YEARS),
        "each_validation_year_risk_recall_ge_095": all(yearly[str(y)]["risk_recall"] is not None and yearly[str(y)]["risk_recall"] >= 0.95 for y in VAL_YEARS),
        "each_validation_year_false_positive_rate_le_001": all(yearly[str(y)]["false_positive_rate"] is not None and yearly[str(y)]["false_positive_rate"] <= 0.01 for y in VAL_YEARS),
        "pooled_exact_three_state_agreement_ge_090": pooled["exact_three_state_agreement"] is not None and pooled["exact_three_state_agreement"] >= 0.90,
        "reference_episode_capture_rate_ge_098": ep_pool["capture_rate"] is not None and ep_pool["capture_rate"] >= 0.98,
        "false_machine_episode_rate_le_010": ep_pool["false_episode_rate"] is not None and ep_pool["false_episode_rate"] <= 0.10,
        "reference_episode_fragmentation_rate_le_005": ep_pool["fragmentation_rate"] is not None and ep_pool["fragmentation_rate"] <= 0.05,
        "uncensored_same_checkpoint_onset_rate_ge_080": ep_pool["same_checkpoint_onset_rate"] is not None and ep_pool["same_checkpoint_onset_rate"] >= 0.80,
        "each_validation_year_uncensored_same_checkpoint_onset_rate_ge_070": all(episodes["yearly"][str(y)]["same_checkpoint_onset_rate"] is not None and episodes["yearly"][str(y)]["same_checkpoint_onset_rate"] >= 0.70 for y in VAL_YEARS),
        "switch_on_same_checkpoint_unsafe_recall_ge_080": transitions["switch_on"]["recall"] is not None and transitions["switch_on"]["recall"] >= 0.80,
        "re_escalation_same_checkpoint_unsafe_recall_ge_080": transitions["re_escalation"]["recall"] is not None and transitions["re_escalation"]["recall"] >= 0.80,
        "unsafe_to_recovering_same_checkpoint_recall_ge_080": transitions["unsafe_to_recovering"]["recall"] is not None and transitions["unsafe_to_recovering"]["recall"] >= 0.80,
        "close_confirmed_premature_normal_rate_le_002": transitions["close_confirmed_exit"]["premature_normal_rate"] is not None and transitions["close_confirmed_exit"]["premature_normal_rate"] <= 0.02,
        "recovery_probabilities_rowwise_monotone": prob["monotone_all_rows"],
        "sixty_minute_exact_frozen_age_anchor": prob["sixty_minute_anchor_exact"],
        "frozen_v19_runner_unchanged": git_blob_sha(FROZEN_V19) == EXPECTED_V19_BLOB,
        "frozen_v9_blob_unchanged": blob_receipt["frozen_v9.py"] == EXPECTED_V9_BLOB,
        "frozen_v18_blob_unchanged": blob_receipt["frozen_v18.py"] == EXPECTED_V18_BLOB,
        "frozen_v17_blob_unchanged": blob_receipt["frozen_v17.py"] == EXPECTED_V17_BLOB,
        "frozen_v16_surface_blob_unchanged": blob_receipt["frozen_v16_surface.json"] == EXPECTED_V16_SURFACE_BLOB,
        "threshold_search_performed_false": True,
        "lead_time_search_performed_false": True,
        "persistence_length_search_performed_false": True,
        "probability_fit_performed_false": True,
        "projection_change_performed_false": True,
        "posthoc_subgroup_selection_false": True,
        "queried_3s_years_exactly_2024_2025": list(VAL_YEARS) == [2024, 2025],
        "queried_2026_3s_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    supported = bool(all(acceptance.values()))

    summary = {
        "schema": "highvol_risk_episode_state_machine_v19_reusable_validation_v1",
        "reusable_validation": True,
        "validation_period": ["2024-01-01", "2025-12-31"],
        "validation_years": list(VAL_YEARS),
        "symbols": list(SYMBOLS),
        "checkpoint_seconds_before_5m_close": 15,
        "machine_rule": "partial risk state immediately; provisional NORMAL while previous finalized state is risk is latched until bar close",
        "reference_rule": "current final risk state, else previous finalized risk state until close, else NORMAL",
        "frozen_development_authority": {
            "source_execution_commit": SOURCE_DEVELOPMENT_COMMIT,
            "source_run_id": SOURCE_DEVELOPMENT_RUN,
            "source_artifact_id": SOURCE_DEVELOPMENT_ARTIFACT,
            "frozen_v19_runner_blob": EXPECTED_V19_BLOB,
        },
        "frozen_blob_receipt": blob_receipt,
        "boundary_exclusions": boundary,
        "candidate_rows": int(len(detail)),
        "year_row_counts": {str(y): int(detail.year.eq(y).sum()) for y in VAL_YEARS},
        "pooled": pooled,
        "yearly": yearly,
        "by_symbol": by_symbol,
        "transitions": transitions,
        "episodes": episodes,
        "recovery_probability_integrity": prob,
        "threshold_search_performed": False,
        "lead_time_search_performed": False,
        "persistence_length_search_performed": False,
        "probability_fit_performed": False,
        "projection_change_performed": False,
        "posthoc_subgroup_selection": False,
        "validation_queried": True,
        "queried_3s_years": list(VAL_YEARS),
        "queried_2026_3s": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
        "acceptance": acceptance,
        "full_validation_supported": supported,
        "decision": "V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_REUSABLE_VALIDATION_SUPPORTED_2024_2025" if supported else "V19_REUSABLE_VALIDATION_FAILED_NO_REFIT",
    }

    out.mkdir(parents=True, exist_ok=True)
    detail.to_parquet(out / "checkpoint_detail.parquet", index=False)
    ref_ep.to_parquet(out / "reference_episodes.parquet", index=False)
    mach_ep.to_parquet(out / "machine_episodes.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
