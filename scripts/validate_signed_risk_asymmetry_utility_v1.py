#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/signed_risk_asymmetry_utility_v1"
DECISION = "SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED"
MODEL_SHA = "92a5fdd5a75a57a1ca3adb567e8a12d03309c7de4ef33a601fc67cbb8c38f4d2"
VALIDATION_SHA = "c0ffac04a70fed796bfb766876bd51f1781c788e4648b202eefd3b9ef01b203b"
PROTOCOL_BLOB = "8e5690d4fa1250fcc2e3b5cc3bfdea733dd46880"
RUNNER_BLOB = "52fe22bef0b1e34364d908fc306fd076c8a20264"
PARENT_BLOB = "0afc45e5061f45f544ecc7ee4519eae4e5204bca"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def main() -> int:
    state = load("PROGRAM_STATE.json")
    receipt = load("EXECUTION_RECEIPT.json")
    decisive = load("DECISIVE_RECEIPT.json")
    validation = load("evidence/VALIDATION_RESULTS.json")
    source = load("evidence/EVIDENCE_SOURCE.json")
    frozen = load("evidence/FROZEN_MODELS.json")

    for obj, key in ((state, "state"), (receipt, "decision"), (decisive, "decision"), (validation, "decision")):
        assert obj[key] == DECISION

    assert git_blob(BASE / "PROTOCOL.md") == PROTOCOL_BLOB
    assert git_blob(BASE / "run_study.py") == RUNNER_BLOB
    parent = ROOT / "research/degree_trajectory_utility_v1/run_study.py"
    assert git_blob(parent) == PARENT_BLOB
    assert sha256(BASE / "evidence/FROZEN_MODELS.json") == MODEL_SHA
    assert (BASE / "evidence/MODEL_SHA256.txt").read_text(encoding="utf-8").strip() == MODEL_SHA
    assert sha256(BASE / "evidence/VALIDATION_RESULTS.json") == VALIDATION_SHA

    assert source["decisive_run_id"] == 34681733485
    assert source["fit_job_id"] == 103521475450
    assert source["validation_job_id"] == 103521623283
    assert source["fit_artifact_id"] == 10294178564
    assert source["fit_artifact_bytes"] == 26054
    assert source["fit_artifact_zip_sha256"] == "f7704e9e77163a6c7f977fb8d9007543d03b579aebf80ef5f403fb830a63a369"
    assert source["validation_artifact_id"] == 10293179281
    assert source["validation_artifact_bytes"] == 67661
    assert source["validation_artifact_zip_sha256"] == "f9597bb93b91a481b6a07a225dfae22c90c2f9178216079f41e6053f3076af79"
    assert source["frozen_models_sha256"] == MODEL_SHA
    assert source["validation_results_sha256"] == VALIDATION_SHA
    assert source["protocol_git_blob"] == PROTOCOL_BLOB
    assert source["runner_git_blob"] == RUNNER_BLOB
    assert source["parent_runner_git_blob"] == PARENT_BLOB
    assert source["source_main_commit"] == "291d04861e85492337a2f86f1fade0419254972d"
    assert source["source_artifact_copied_byte_for_byte"] is True

    assert frozen["feature_identity"]["base_columns"] == 84
    assert frozen["feature_identity"]["signed_columns"] == 104
    assert frozen["feature_identity"]["magnitude_control_columns"] == 104
    assert frozen["feature_identity"]["A_M_complexity_matched"] is True
    assert frozen["feature_identity"]["current_final_return_excluded_by_shift1"] is True
    assert frozen["lookback_valid_completed_bars"] == 12
    assert frozen["validation_scored"] is False

    assert validation["model_sha256"] == MODEL_SHA
    assert validation["validation_years"] == [2024, 2025]
    assert validation["validation_reused"] is True
    assert validation["fresh_oos"] is False
    assert validation["read_2026"] is False
    assert validation["blackbox_queried"] is False
    assert validation["pnl_computed"] is False
    assert validation["candidate_nominated"] is False
    assert validation["production_authority"] is False
    assert validation["v20_started"] is False
    assert validation["d6_started"] is False

    assert len(validation["comparisons"]) == 12
    assert len(validation["joint_endpoint_support"]) == 6
    assert not any(validation["joint_endpoint_support"].values())
    assert all(row["supported"] is False for row in validation["comparisons"])
    rows = {(r["horizon"], r["endpoint"], r["comparison"]): r for r in validation["comparisons"]}

    for comparison in ("A_vs_C", "A_vs_M"):
        row = rows[(60, "log_future_sigma", comparison)]
        assert row["relative_gain"] >= 0.01
        assert row["gates"]["relative_at_least_one_percent"] is True
        assert row["ci_5day"]["low"] < 0
        assert row["gates"]["adjusted_5day_interval_positive"] is False
        assert row["slices"]["symbol:000688.SH"]["absolute_gain"] < 0
        assert row["slices"]["symbol:000852.SH"]["absolute_gain"] > 0
        assert row["gates"]["annual_and_symbol_signs"] is False
        assert row["supported"] is False

    for row in validation["comparisons"]:
        if row["endpoint"] == "future_tail":
            assert row["absolute_gain"] < 0.0005
            assert row["gates"]["tail_absolute_at_least_0005"] is False

    for h in ("15", "30", "60"):
        assert validation["coverage"][h]["development"]["coverage"] >= 0.95
        assert validation["coverage"][h]["validation"]["coverage"] >= 0.95

    assert state["base_columns"] == 84
    assert state["signed_columns"] == 104
    assert state["magnitude_control_columns"] == 104
    assert state["signed_magnitude_control_complexity_matched"] is True
    assert state["pooled_60m_rms_one_percent_gate_met_vs_C"] is True
    assert state["pooled_60m_rms_one_percent_gate_met_vs_M"] is True
    assert state["pooled_60m_rms_adjusted_interval_supported"] is False
    assert state["star50_60m_rms_gain_positive"] is False
    assert state["csi1000_60m_rms_gain_positive"] is True
    assert state["cross_symbol_robustness_supported"] is False
    assert state["signed_asymmetry_practical_increment_supported"] is False
    assert state["signed_asymmetry_consumer_promotion"] is False
    assert state["single_index_rescue_authorized"] is False
    assert state["posthoc_rescue_authorized"] is False
    assert state["signed_asymmetry_spec_closed"] is True
    assert state["d4_decision_unchanged"] is True
    assert state["d5_contract_unchanged"] is True
    assert state["v19_frozen"] is True
    assert decisive["single_index_rescue_forbidden"] is True
    assert decisive["posthoc_rescue_forbidden"] is True
    assert decisive["consumer_logic_change"] is False

    results = (BASE / "RESULTS.md").read_text(encoding="utf-8")
    assert DECISION in results
    assert "1%" in results
    assert "000688.SH" in results and "000852.SH" in results
    assert "selecting only CSI1000" in results or "selecting the favorable index" in results
    assert "no signed-asymmetry field is added to D5" in results
    assert "Validation" in results and "fresh_oos=false" in results

    print("signed-risk asymmetry utility V1 authority: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
