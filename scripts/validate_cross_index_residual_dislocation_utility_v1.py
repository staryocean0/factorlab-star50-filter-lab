#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/cross_index_residual_dislocation_utility_v1"
DECISION = "CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_NOT_SUPPORTED"
PROTOCOL_BLOB = "807623a9f810a37fda0df8ba9e63932471dc3a48"
RUNNER_BLOB = "00b414f508afe1112564b1d9110af31da2de9167"
TEST_BLOB = "354c807146ea801fc83b4cfe8860623d0781c6f2"
CROSS_PARENT_BLOB = "b4d3c72e58706b2eb9ae8425f7e7f5439ba002c5"
ACTIVITY_PARENT_BLOB = "b148d8ccf1d13651434b7b14b42a27dc4b31f5e6"
MODEL_SHA = "8f37d237172a86c23aa75baf3f69f2f5b8948cbbd12c267bdde5da6864607d94"
FIT_SHA = "23107f9a2e7a1b712db2afa3a2cdb99c6996311155d729cfecf89aa8280f52da"
MODEL_SHA_FILE_SHA = "e40b0dd9ef2c647abc2afad36f10d6f4d6390ab23fb70d2e12f79d212eb4c6e0"
COMPARISONS_SHA = "c939a345c2dd9f70c9c3c8aa2714e74b288b8fba32e4fa48d7b641cf984dfe6d"
VALIDATION_SHA = "2cc44ce7baff43dfd84884e6ce1ebf81aada12c2644e1bbe48384ac4d8f82654"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def main() -> int:
    state = load("PROGRAM_STATE.json")
    execution = load("EXECUTION_RECEIPT.json")
    decisive = load("DECISIVE_RECEIPT.json")
    source = json.loads((BASE / "evidence/EVIDENCE_SOURCE.json").read_text(encoding="utf-8"))
    fit = json.loads((BASE / "evidence/FIT_RECEIPT.json").read_text(encoding="utf-8"))

    for obj, key in ((state, "state"), (execution, "decision"), (decisive, "decision")):
        assert obj[key] == DECISION

    assert git_blob(BASE / "PROTOCOL.md") == PROTOCOL_BLOB
    assert git_blob(BASE / "run_study.py") == RUNNER_BLOB
    assert git_blob(BASE / "test_study.py") == TEST_BLOB
    assert git_blob(ROOT / "research/cross_index_degree_transfer_utility_v1/run_study.py") == CROSS_PARENT_BLOB
    assert git_blob(ROOT / "research/activity_degree_incremental_utility_v1/run_study.py") == ACTIVITY_PARENT_BLOB

    assert sha256(BASE / "evidence/FIT_RECEIPT.json") == FIT_SHA
    assert sha256(BASE / "evidence/MODEL_SHA256.txt") == MODEL_SHA_FILE_SHA
    assert (BASE / "evidence/MODEL_SHA256.txt").read_text(encoding="utf-8").strip() == MODEL_SHA
    assert sha256(BASE / "evidence/comparisons.csv") == COMPARISONS_SHA

    assert source["source_main_commit"] == "e30a0eb0e0884a569110c8819fb4b2696bb9dd29"
    assert source["study_head_commit"] == "f795845e3ec6abcd201e638c7264cb78ffe0e729"
    assert source["decisive_run_id"] == 34688304454
    assert source["fit_job_id"] == 103539075057
    assert source["validation_job_id"] == 103539290902
    assert source["fit_artifact_id"] == 10296505999
    assert source["validation_artifact_id"] == 10295914902
    assert source["frozen_models_sha256"] == MODEL_SHA
    assert source["fit_receipt_sha256"] == FIT_SHA
    assert source["validation_results_sha256"] == VALIDATION_SHA
    assert source["comparisons_csv_sha256"] == COMPARISONS_SHA
    assert source["protocol_git_blob"] == PROTOCOL_BLOB
    assert source["runner_git_blob"] == RUNNER_BLOB
    assert source["test_git_blob"] == TEST_BLOB
    assert source["cross_index_degree_parent_runner_git_blob"] == CROSS_PARENT_BLOB
    assert source["activity_parent_runner_git_blob"] == ACTIVITY_PARENT_BLOB

    fi = fit["feature_identity"]
    assert fi["base_columns"] == 99
    assert fi["residual_columns"] == 107
    assert fi["raw_spread_control_columns"] == 107
    assert fi["R_Q_schema_identical"] is True
    assert fi["relationship_block_columns"] == 8
    assert fi["relation_window"] == 48
    assert fi["current_other_iv_in_base"] is True
    assert fi["same_row_availability"] is True
    assert fi["global_sign_invariant"] is True
    assert fit["model_sha256"] == MODEL_SHA
    assert fit["validation_scored"] is False
    assert all(v["coverage"] == 1.0 for v in fit["development_coverage"].values())

    with (BASE / "evidence/comparisons.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 12
    assert all(r["supported"] == "False" for r in rows)
    keys = {(int(r["horizon"]), r["endpoint"], r["comparison"]): r for r in rows}

    for h in (15, 30, 60):
        for endpoint in ("log_future_sigma", "future_tail"):
            assert (h, endpoint, "R_vs_B") in keys
            assert (h, endpoint, "R_vs_Q") in keys

    r_vs_b = [r for r in rows if r["comparison"] == "R_vs_B"]
    r_vs_q = [r for r in rows if r["comparison"] == "R_vs_Q"]
    assert len(r_vs_b) == len(r_vs_q) == 6
    assert all(float(r["relative_gain"]) > 0 for r in r_vs_b)
    assert max(float(r["relative_gain"]) for r in r_vs_b) == 0.002356951581085741
    assert max(float(r["relative_gain"]) for r in r_vs_q) == 0.0008571009881953478
    assert float(keys[(15, "log_future_sigma", "R_vs_Q")]["relative_gain"]) < 0
    assert float(keys[(30, "log_future_sigma", "R_vs_B")]["relative_gain"]) == 0.0020754095585199094
    assert all(float(r["relative_gain"]) < 0.01 for r in rows)
    assert all(float(r["absolute_gain"]) < 0.0005 for r in rows if r["endpoint"] == "future_tail")
    assert all(float(r["development_forward_gain"]) >= 0 for r in rows)

    assert state["formal_comparison_count"] == 12
    assert state["formal_comparison_support_count"] == 0
    assert state["all_R_vs_B_pooled_gains_positive"] is True
    assert state["thirty_min_rms_R_vs_B_adjusted_interval_positive"] is True
    assert state["thirty_min_rms_R_vs_B_all_year_symbol_slices_positive"] is True
    assert state["one_percent_gate_met_any"] is False
    assert state["tail_0005_gate_met_any"] is False
    assert state["residual_specific_practical_increment_supported"] is False
    assert state["cross_index_residual_consumer_promotion"] is False
    assert state["single_index_rescue_authorized"] is False
    assert state["relationship_model_rescue_authorized"] is False
    assert state["cross_index_residual_dislocation_spec_closed"] is True
    assert state["distinct_executable_axis_remaining"] is False
    assert state["research_hold"] is True
    assert state["d4_decision_unchanged"] is True
    assert state["d5_contract_unchanged"] is True
    assert state["v19_frozen"] is True

    assert decisive["thirty_min_rms_R_vs_B"]["adjusted_5day_ci_low"] > 0
    assert decisive["thirty_min_rms_R_vs_B"]["one_percent_gate"] is False
    assert decisive["largest_tail_absolute_gain"] < 0.0005
    assert decisive["single_index_rescue_forbidden"] is True
    assert decisive["relationship_model_rescue_forbidden"] is True
    assert decisive["posthoc_feature_search_forbidden"] is True

    for obj in (state, execution, decisive, source):
        assert obj["validation_reused"] is True
        assert obj["fresh_oos"] is False
        assert obj["read_2026"] is False
        assert obj["synthetic_2026_used"] is False
        assert obj["blackbox_queried"] is False
        assert obj["pnl_computed"] is False
        assert obj["production_authority"] is False

    results = (BASE / "RESULTS.md").read_text(encoding="utf-8")
    assert DECISION in results
    assert "+0.20754%" in results
    assert "+0.04428%" in results
    assert "weak statistical hint" in results
    assert "HOLD CURRENT AUTHORITY" in results
    assert "No residual-dislocation field or gate is added to D5" in results

    sums = (BASE / "evidence/ARTIFACT_SHA256SUMS.txt").read_text(encoding="utf-8")
    assert f"{MODEL_SHA}  ./FROZEN_MODELS.json" in sums
    assert f"{VALIDATION_SHA}  ./VALIDATION_RESULTS.json" in sums
    assert f"{COMPARISONS_SHA}  ./comparisons.csv" in sums

    print("cross-index residual dislocation utility V1 authority: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
